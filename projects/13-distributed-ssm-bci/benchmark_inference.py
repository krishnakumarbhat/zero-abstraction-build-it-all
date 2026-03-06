import argparse
import time

import torch

from model import GRUClassifier, LSTMClassifier, ModelConfig, SSMClassifier, count_params


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--seq-len", type=int, default=512)
    p.add_argument("--channels", type=int, default=64)
    p.add_argument("--classes", type=int, default=8)
    p.add_argument("--hidden", type=int, default=128)
    p.add_argument("--layers", type=int, default=4)
    p.add_argument("--dropout", type=float, default=0.1)
    p.add_argument("--warmup", type=int, default=20)
    p.add_argument("--steps", type=int, default=100)
    p.add_argument("--dtype", type=str, default="fp16", choices=["fp16", "fp32", "bf16"])
    return p.parse_args()


def as_dtype(dtype: str):
    if dtype == "fp16":
        return torch.float16
    if dtype == "bf16":
        return torch.bfloat16
    return torch.float32


def measure(model, x, warmup: int, steps: int):
    model.eval()
    with torch.no_grad():
        for _ in range(warmup):
            _ = model(x)
        if x.is_cuda:
            torch.cuda.synchronize()

        start = torch.cuda.Event(enable_timing=True) if x.is_cuda else None
        end = torch.cuda.Event(enable_timing=True) if x.is_cuda else None

        if x.is_cuda:
            start.record()
            for _ in range(steps):
                _ = model(x)
            end.record()
            torch.cuda.synchronize()
            total_ms = start.elapsed_time(end)
        else:
            t0 = time.perf_counter()
            for _ in range(steps):
                _ = model(x)
            total_ms = (time.perf_counter() - t0) * 1000.0

    return total_ms / steps


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = as_dtype(args.dtype)

    cfg = ModelConfig(
        channels=args.channels,
        hidden=args.hidden,
        layers=args.layers,
        classes=args.classes,
        dropout=args.dropout,
    )

    x = torch.randn((args.batch_size, args.seq_len, args.channels), device=device, dtype=dtype)

    model_defs = [
        ("SSM", SSMClassifier(cfg)),
        ("GRU", GRUClassifier(cfg)),
        ("LSTM", LSTMClassifier(cfg)),
    ]

    print(f"device={device} dtype={dtype} input=[{args.batch_size},{args.seq_len},{args.channels}]")
    print("model,param_count,latency_ms_per_step,samples_per_sec")

    for name, model in model_defs:
        model = model.to(device)
        if device.type == "cuda" and dtype in (torch.float16, torch.bfloat16):
            model = model.to(dtype)

        ms = measure(model, x, args.warmup, args.steps)
        sps = args.batch_size / (ms / 1000.0)
        print(f"{name},{count_params(model):,},{ms:.4f},{sps:.2f}")


if __name__ == "__main__":
    main()
