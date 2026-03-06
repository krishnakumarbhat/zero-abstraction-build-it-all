# Project C: Distributed Training of a Minimal LLM/SSM from Scratch

Theme: Scaling Brain-Computer Interface (BCI) Models

This project trains a minimal Mamba-style State Space Model (SSM) for EEG sequence classification and supports distributed training with PyTorch Fully Sharded Data Parallel (FSDP).

## Core math

Continuous-time state equation:

$$
h'(t) = A h(t) + B x(t)
$$

Discretized update (zero-order style simplification):

$$
h_t = \alpha \odot h_{t-1} + \beta(x_t), \quad y_t = C(x_t) \odot h_t + D(x_t)
$$

Where $\alpha = \exp(-\Delta t \cdot \text{softplus}(a))$ is stable by construction.

## Files

- `model.py` - Minimal Mamba-like SSM block + EEG classifier + GRU/LSTM baselines
- `data.py` - Synthetic EEG dataset + DataLoader helpers
- `train_fsdp.py` - Distributed training entrypoint using FSDP (`torchrun`)
- `benchmark_inference.py` - Inference latency benchmark (SSM vs GRU vs LSTM)

## Run: single GPU smoke test

```bash
cd projects/13-distributed-ssm-bci
python3 train_fsdp.py --epochs 1 --batch-size 16 --seq-len 256 --channels 32 --classes 4 --samples 512
python3 benchmark_inference.py --seq-len 256 --channels 32 --classes 4 --batch-size 16 --steps 100
```

## Run: multi-GPU distributed training

```bash
torchrun --standalone --nproc_per_node=2 train_fsdp.py --epochs 5 --batch-size 32 --seq-len 512 --channels 64 --classes 8 --samples 20000
```

Use `--nproc_per_node=<num_gpus>` matching your machine.

## Publishable angle checklist

- Accuracy comparison: SSM vs GRU/LSTM on EEG labels
- Throughput/latency comparison on target GPU(s)
- Memory footprint under FSDP
- Inference-time edge efficiency discussion (important for on-device decoding)
