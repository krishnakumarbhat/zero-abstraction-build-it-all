# Project D: Implementing a SOTA Paper (from scratch)

Theme: Neuromorphic Computing & Efficient Routing

## Selected direction (best as of now)

This implementation chooses **hardware-aware Mixture of Experts (MoE) with noisy top-k gating**.

Why this choice now:

- Strong current relevance in SOTA large-model training/inference efficiency.
- Cleanly measurable routing behavior (expert balance, sparsity, utilization).
- Directly supports publishable ablations on routing penalties.

## What is implemented

- From-scratch PyTorch MoE layer with noisy top-k router (`k=1 or k=2`)
- Expert dispatch/combine and router load-balancing auxiliary loss
- End-to-end classifier for sequence tasks
- Ablation study script varying sparsity/load-balancing penalties

## Publishable replication study angle

`ablation.py` sweeps router coefficients and reports:

- Validation accuracy
- Expert utilization entropy
- Router load balancing loss
- Tokens-per-expert imbalance

## Files

- `model.py` - MoE router + experts + classifier
- `data.py` - synthetic sequence dataset for controlled routing experiments
- `train_moe.py` - training/evaluation script
- `ablation.py` - penalty sweep and markdown report generation

## Quick run

```bash
cd projects/14-moe-routing-paper
python3 train_moe.py --epochs 2 --batch-size 64 --samples 4096 --seq-len 64 --input-dim 64 --classes 8 --experts 8 --top-k 2
python3 ablation.py --quick
```

## Full ablation example

```bash
python3 ablation.py \
  --lambdas 0.0,0.01,0.05,0.1 \
  --entropy-coefs 0.0,0.001,0.01 \
  --epochs 3 --samples 20000 --report ABLATION_REPORT.md
```
