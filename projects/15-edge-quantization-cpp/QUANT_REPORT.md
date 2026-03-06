# Project B Quantization Report

Config: samples=4000, features=128, classes=8, iters=80

KL calibrated activation clip: 0.102039

| Scheme | Accuracy | Latency (ms) | Speedup vs FP32 |
|---|---:|---:|---:|
| FP32 | 0.026 | 1.20827 | 1.0000 |
| PTQ int8 | 0.088 | 6.09997 | 0.198079 |
| AWQ int8 | 0.088 | 6.0814 | 0.198684 |

Pareto note: choose points with best latency for acceptable accuracy degradation.
