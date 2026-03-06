# Project A: Custom CUDA/Triton Kernel for Attention

Theme: Hardware-Accelerated Continuous Signal Processing

This project implements a fused Triton kernel for **causal sliding-window attention** on 1D continuous sensor sequences (radar/EEG-like streams), inspired by FlashAttention's online softmax strategy.

## What this demonstrates

- Localized attention window to avoid full $O(N^2)$ memory footprint.
- Fused kernel that computes softmax + value accumulation in-kernel.
- Practical GPU benchmarking vs standard PyTorch implementations.

## Complexity target

- Full attention memory: $O(N^2)$
- Sliding-window attention memory: $O(N \cdot W)$ with fixed window $W$, effectively linear in $N$ when $W$ is constant.

## Files

- `local_attention.py` - Triton kernel + Python wrappers and PyTorch baselines
- `test_correctness.py` - numerical correctness checks against PyTorch local attention
- `benchmark.py` - throughput/latency benchmark and markdown report generation

## Requirements

- NVIDIA GPU (tested path: RTX on Pop!_OS)
- CUDA-enabled PyTorch
- Triton

## Quick start

```bash
cd projects/12-attention-triton
python3 test_correctness.py
python3 benchmark.py --quick
```

## Full benchmark run

```bash
python3 benchmark.py --batch 4 --heads 8 --d-head 64 --window 256 --seq-lens 1024,2048,4096 --iters 100 --warmup 20 --report BENCHMARK_REPORT.md
```

## Publishable angle

The benchmark report includes:

- Mean latency per method
- Effective memory bandwidth (GB/s)
- Speedup of fused Triton local attention vs PyTorch baselines

This provides a strong starting point for a paper section on hardware efficiency for continuous 1D sensor streams.
