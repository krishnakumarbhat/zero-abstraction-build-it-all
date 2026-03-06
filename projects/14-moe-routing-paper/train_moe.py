import argparse
from dataclasses import asdict

import torch
import torch.nn as nn
import torch.optim as optim

from data import build_loaders
from model import MoEClassifier, MoEConfig, count_params


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--epochs", type=int, default=5)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--samples", type=int, default=20000)
    p.add_argument("--seq-len", type=int, default=64)
    p.add_argument("--input-dim", type=int, default=64)
    p.add_argument("--classes", type=int, default=8)
    p.add_argument("--model-dim", type=int, default=128)
    p.add_argument("--hidden-dim", type=int, default=256)
    p.add_argument("--experts", type=int, default=8)
    p.add_argument("--top-k", type=int, default=2)
    p.add_argument("--dropout", type=float, default=0.1)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--weight-decay", type=float, default=1e-2)
    p.add_argument("--lambda-balance", type=float, default=0.01)
    p.add_argument("--lambda-entropy", type=float, default=0.001)
    p.add_argument("--save", type=str, default="moe_ckpt.pt")
    return p.parse_args()


@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    correct = 0
    total = 0
    bal = 0.0
    ent = 0.0
    util_ent = 0.0
    n_batches = 0

    for x, y in loader:
        x = x.to(device, non_blocking=True)
        y = y.to(device, non_blocking=True)

        logits, aux = model(x)
        pred = logits.argmax(dim=-1)
        correct += (pred == y).sum().item()
        total += y.numel()
        bal += aux["balance_loss"].item()
        ent += aux["router_entropy"].item()
        util_ent += aux["utilization_entropy"].item()
        n_batches += 1

    return {
        "acc": correct / max(total, 1),
        "balance_loss": bal / max(n_batches, 1),
        "router_entropy": ent / max(n_batches, 1),
        "utilization_entropy": util_ent / max(n_batches, 1),
    }


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    cfg = MoEConfig(
        input_dim=args.input_dim,
        model_dim=args.model_dim,
        hidden_dim=args.hidden_dim,
        classes=args.classes,
        experts=args.experts,
        top_k=args.top_k,
        dropout=args.dropout,
    )
    model = MoEClassifier(cfg).to(device)

    train_loader, val_loader = build_loaders(
        samples=args.samples,
        seq_len=args.seq_len,
        input_dim=args.input_dim,
        classes=args.classes,
        batch_size=args.batch_size,
    )

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)

    print(f"device={device} params={count_params(model):,} cfg={asdict(cfg)}")

    for epoch in range(1, args.epochs + 1):
        model.train()
        running_loss = 0.0
        n_items = 0

        for x, y in train_loader:
            x = x.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)

            optimizer.zero_grad(set_to_none=True)
            logits, aux = model(x)

            cls = criterion(logits, y)
            loss = cls + args.lambda_balance * aux["balance_loss"] - args.lambda_entropy * aux["router_entropy"]
            loss.backward()
            optimizer.step()

            batch_items = y.numel()
            running_loss += loss.item() * batch_items
            n_items += batch_items

        val = evaluate(model, val_loader, device)
        avg_loss = running_loss / max(n_items, 1)
        print(
            f"epoch={epoch} train_loss={avg_loss:.4f} val_acc={val['acc']:.4f} "
            f"balance={val['balance_loss']:.4f} router_entropy={val['router_entropy']:.4f} "
            f"util_entropy={val['utilization_entropy']:.4f}"
        )

    torch.save(
        {
            "state_dict": model.state_dict(),
            "config": asdict(cfg),
            "args": vars(args),
        },
        args.save,
    )
    print(f"saved checkpoint: {args.save}")


if __name__ == "__main__":
    main()
