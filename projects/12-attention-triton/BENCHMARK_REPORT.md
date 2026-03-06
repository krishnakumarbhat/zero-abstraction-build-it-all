# Project A Benchmark Report

Generated: 2026-03-01 04:01:24
GPU: NVIDIA GeForce RTX 3050 Laptop GPU
Config: B=2, H=8, D=64, window=128, dtype=fp16

## Results

| Seq Len (N) | Triton ms | PyTorch ms | Triton GB/s | PyTorch GB/s | Speedup |
|---:|---:|---:|---:|---:|---:|
| 512 | 2.5585 | 0.6031 | 1.64 | 6.95 | 0.24x |
| 1024 | 5.1028 | 2.3214 | 1.64 | 3.61 | 0.45x |

## Summary

Average speedup (Triton vs PyTorch local attention): **0.35x**

This report is intended as a starting benchmark section for a publishable kernel-efficiency study.
