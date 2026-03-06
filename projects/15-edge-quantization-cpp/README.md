# Project B: Edge AI Quantization Engine

Theme: On-Device Inference for Genomic/Biological Models

This project builds a C++ quantization pipeline for a sequential biological classifier (synthetic RNA-like features), with a ggml-friendly edge deployment layout.

## Implemented methods

- Post-Training Quantization (PTQ) to int8
- KL-divergence calibration for activation clipping threshold
- Activation-aware Weight Quantization (AWQ-style) per-output-channel scaling
- Accuracy vs latency benchmarking with Pareto-style report output

Core quantization mapping:

$$
W_q = \text{round}(W_f / \Delta)
$$

## Files

- `src/main.cpp` - quantization engine + benchmark harness
- `CMakeLists.txt` - CMake build setup
- `run.sh` - convenience build/run script

## Build & Run

```bash
cd projects/15-edge-quantization-cpp
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
./build/quant_engine --samples 8000 --features 256 --classes 8 --iters 200
```

## Output

- Console table: accuracy and latency for `fp32`, `ptq_int8`, `awq_int8`
- `QUANT_REPORT.md`: Pareto-style summary for publication material

## ggml note

The code is structured to mirror tensor quantization/export steps used for ggml deployment pipelines. You can adapt the packed int8 buffers directly into a ggml graph loader for ARM edge targets.
