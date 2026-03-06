import argparse
from datetime import datetime

import torch

from local_attention import benchmark_pair


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=2)
    p.add_argument("--heads", type=int, default=8)
    p.add_argument("--d-head", type=int, default=64)
    p.add_argument("--window", type=int, default=128)
    p.add_argument("--seq-lens", type=str, default="512,1024,2048")
    p.add_argument("--iters", type=int, default=50)
    p.add_argument("--warmup", type=int, default=10)
    p.add_argument("--dtype", type=str, default="fp16", choices=["fp16", "fp32", "bf16"])
    p.add_argument("--quick", action="store_true")
    p.add_argument("--report", type=str, default="BENCHMARK_REPORT.md")
    return p.parse_args()


def to_dtype(s: str):
    if s == "fp16":
        return torch.float16
    if s == "fp32":
        return torch.float32
    return torch.bfloat16


def main():
    args = parse_args()
    if not torch.cuda.is_available():
        raise SystemExit("CUDA is required for this benchmark")

    if args.quick:
        seq_lens = [512, 1024]
        iters = 20
        warmup = 5
    else:
        seq_lens = [int(x.strip()) for x in args.seq_lens.split(",") if x.strip()]
        iters = args.iters
        warmup = args.warmup

    dtype = to_dtype(args.dtype)
    device_name = torch.cuda.get_device_name(0)

    rows = []
    print(f"GPU: {device_name}")
    print("running benchmarks...")

    for n in seq_lens:
        q = torch.randn((args.batch, args.heads, n, args.d_head), device="cuda", dtype=dtype)
        k = torch.randn((args.batch, args.heads, n, args.d_head), device="cuda", dtype=dtype)
        v = torch.randn((args.batch, args.heads, n, args.d_head), device="cuda", dtype=dtype)

        triton_ms, torch_ms, triton_gbs, torch_gbs = benchmark_pair(
            q, k, v, window=args.window, warmup=warmup, iters=iters
        )
        speedup = torch_ms / triton_ms

        row = {
            "N": n,
            "triton_ms": triton_ms,
            "torch_ms": torch_ms,
            "triton_gbs": triton_gbs,
            "torch_gbs": torch_gbs,
            "speedup": speedup,
        }
        rows.append(row)
        print(
            f"N={n:<5} | triton={triton_ms:.3f} ms ({triton_gbs:.2f} GB/s) "
            f"| torch={torch_ms:.3f} ms ({torch_gbs:.2f} GB/s) "
            f"| speedup={speedup:.2f}x"
        )

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Project A Benchmark Report",
        "",
        f"Generated: {ts}",
        f"GPU: {device_name}",
        f"Config: B={args.batch}, H={args.heads}, D={args.d_head}, window={args.window}, dtype={args.dtype}",
        "",
        "## Results",
        "",
        "| Seq Len (N) | Triton ms | PyTorch ms | Triton GB/s | PyTorch GB/s | Speedup |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['N']} | {r['triton_ms']:.4f} | {r['torch_ms']:.4f} | {r['triton_gbs']:.2f} | {r['torch_gbs']:.2f} | {r['speedup']:.2f}x |"
        )

    avg_speedup = sum(r["speedup"] for r in rows) / len(rows)
    lines += [
        "",
        "## Summary",
        "",
        f"Average speedup (Triton vs PyTorch local attention): **{avg_speedup:.2f}x**",
        "",
        "This report is intended as a starting benchmark section for a publishable kernel-efficiency study.",
    ]

    with open(args.report, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"report written: {args.report}")


if __name__ == "__main__":
    main()
