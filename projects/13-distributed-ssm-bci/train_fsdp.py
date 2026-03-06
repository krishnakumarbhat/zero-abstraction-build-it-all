import argparse
import os
import time

import torch
import torch.distributed as dist
import torch.nn as nn
import torch.optim as optim
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.fsdp import ShardingStrategy

from data import build_train_loader
from model import ModelConfig, SSMClassifier, count_params


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--weight-decay", type=float, default=1e-2)
    p.add_argument("--samples", type=int, default=20000)
    p.add_argument("--seq-len", type=int, default=512)
    p.add_argument("--channels", type=int, default=64)
    p.add_argument("--classes", type=int, default=8)
    p.add_argument("--hidden", type=int, default=128)
    p.add_argument("--layers", type=int, default=4)
    p.add_argument("--dropout", type=float, default=0.1)
    p.add_argument("--save", type=str, default="ssm_fsdp.pt")
    return p.parse_args()


def setup_dist():
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    rank = int(os.environ.get("RANK", "0"))
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    distributed = world_size > 1
    if distributed:
        dist.init_process_group(backend="nccl")
        torch.cuda.set_device(local_rank)
    return distributed, rank, world_size, local_rank


def cleanup_dist(distributed: bool):
    if distributed and dist.is_initialized():
        dist.destroy_process_group()


def reduce_mean(value: float, device: torch.device, distributed: bool) -> float:
    if not distributed:
        return value
    t = torch.tensor([value], device=device)
    dist.all_reduce(t, op=dist.ReduceOp.SUM)
    t /= dist.get_world_size()
    return t.item()


def main():
    args = parse_args()
    distributed, rank, world_size, local_rank = setup_dist()

    device = torch.device(f"cuda:{local_rank}" if torch.cuda.is_available() else "cpu")
    torch.backends.cudnn.benchmark = True

    cfg = ModelConfig(
        channels=args.channels,
        hidden=args.hidden,
        layers=args.layers,
        classes=args.classes,
        dropout=args.dropout,
    )
    base_model = SSMClassifier(cfg).to(device)

    if distributed and torch.cuda.is_available():
        model = FSDP(
            base_model,
            device_id=torch.cuda.current_device(),
            sharding_strategy=ShardingStrategy.FULL_SHARD,
            sync_module_states=True,
        )
    else:
        model = base_model

    if rank == 0:
        print(f"params={count_params(base_model):,} world_size={world_size} device={device}")

    loader, sampler = build_train_loader(
        samples=args.samples,
        seq_len=args.seq_len,
        channels=args.channels,
        classes=args.classes,
        batch_size=args.batch_size,
        distributed=distributed,
        rank=rank,
        world_size=world_size,
    )

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)

    for epoch in range(1, args.epochs + 1):
        if sampler is not None:
            sampler.set_epoch(epoch)

        model.train()
        start = time.time()
        total_loss = 0.0
        total_correct = 0
        total_items = 0

        for x, y in loader:
            x = x.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)

            optimizer.zero_grad(set_to_none=True)
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()

            with torch.no_grad():
                preds = logits.argmax(dim=-1)
                total_correct += (preds == y).sum().item()
                total_items += y.numel()
                total_loss += loss.item() * y.numel()

        avg_loss = total_loss / max(total_items, 1)
        avg_acc = total_correct / max(total_items, 1)
        avg_loss = reduce_mean(avg_loss, device, distributed)
        avg_acc = reduce_mean(avg_acc, device, distributed)

        if rank == 0:
            elapsed = time.time() - start
            print(
                f"epoch={epoch} loss={avg_loss:.4f} acc={avg_acc:.4f} "
                f"samples={total_items * world_size} time={elapsed:.2f}s"
            )

    if rank == 0:
        state = base_model.state_dict() if distributed else model.state_dict()
        torch.save(
            {
                "config": cfg.__dict__,
                "state_dict": state,
            },
            args.save,
        )
        print(f"saved checkpoint: {args.save}")

    cleanup_dist(distributed)


if __name__ == "__main__":
    main()
