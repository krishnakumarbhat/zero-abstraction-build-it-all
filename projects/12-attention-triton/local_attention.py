import math
from typing import Tuple

import torch
import triton
import triton.language as tl


@triton.jit
def _local_attn_fwd_kernel(
    q_ptr,
    k_ptr,
    v_ptr,
    o_ptr,
    stride_qb,
    stride_qh,
    stride_qn,
    stride_qd,
    stride_kb,
    stride_kh,
    stride_kn,
    stride_kd,
    stride_vb,
    stride_vh,
    stride_vn,
    stride_vd,
    stride_ob,
    stride_oh,
    stride_on,
    stride_od,
    B,
    H,
    N,
    D,
    WINDOW,
    sm_scale,
    BLOCK_W: tl.constexpr,
    BLOCK_DMODEL: tl.constexpr,
):
    pid_m = tl.program_id(0)
    pid_bh = tl.program_id(1)

    batch_id = pid_bh // H
    head_id = pid_bh % H

    offs_m = pid_m
    offs_d = tl.arange(0, BLOCK_DMODEL)

    q_base = q_ptr + batch_id * stride_qb + head_id * stride_qh + offs_m * stride_qn + offs_d * stride_qd
    q = tl.load(q_base, mask=(offs_m < N) & (offs_d < D), other=0.0).to(tl.float32)

    win_start = tl.maximum(0, offs_m - WINDOW + 1)
    offs_w = tl.arange(0, BLOCK_W)
    offs_n = win_start + offs_w
    win_len = offs_m - win_start + 1
    row_valid = offs_m < N
    win_mask = row_valid & (offs_w < win_len) & (offs_n < N)

    k_base = (
        k_ptr
        + batch_id * stride_kb
        + head_id * stride_kh
        + offs_n[:, None] * stride_kn
        + offs_d[None, :] * stride_kd
    )
    v_base = (
        v_ptr
        + batch_id * stride_vb
        + head_id * stride_vh
        + offs_n[:, None] * stride_vn
        + offs_d[None, :] * stride_vd
    )
    kv_mask = win_mask[:, None] & (offs_d[None, :] < D)
    k = tl.load(k_base, mask=kv_mask, other=0.0).to(tl.float32)
    v = tl.load(v_base, mask=kv_mask, other=0.0).to(tl.float32)

    scores = tl.sum(k * q[None, :], axis=1) * sm_scale
    scores = tl.where(win_mask, scores, -float("inf"))
    m = tl.max(scores, axis=0)
    p = tl.where(win_mask, tl.exp(scores - m), 0.0)
    denom = tl.sum(p, axis=0) + 1e-6
    p = p / denom

    out = tl.sum(p[:, None] * v, axis=0)

    o_base = o_ptr + batch_id * stride_ob + head_id * stride_oh + offs_m * stride_on + offs_d * stride_od
    tl.store(o_base, out, mask=(offs_m < N) & (offs_d < D))


def _check_inputs(q: torch.Tensor, k: torch.Tensor, v: torch.Tensor):
    if not q.is_cuda or not k.is_cuda or not v.is_cuda:
        raise ValueError("q, k, v must be CUDA tensors")
    if q.dtype not in (torch.float16, torch.bfloat16, torch.float32):
        raise ValueError("q dtype must be float16/bfloat16/float32")
    if q.shape != k.shape or q.shape != v.shape:
        raise ValueError("q, k, v must have the same shape [B, H, N, D]")
    if q.ndim != 4:
        raise ValueError("q, k, v must be rank-4 tensors [B, H, N, D]")


def local_attention_triton(
    q: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    window: int,
    sm_scale: float | None = None,
) -> torch.Tensor:
    _check_inputs(q, k, v)
    if window <= 0:
        raise ValueError("window must be > 0")

    B, H, N, D = q.shape
    if D > 128:
        raise ValueError("current kernel supports D <= 128")
    if window > 256:
        raise ValueError("current kernel supports window <= 256")

    if sm_scale is None:
        sm_scale = 1.0 / math.sqrt(D)

    o = torch.empty_like(q)

    grid = (N, B * H)
    _local_attn_fwd_kernel[grid](
        q,
        k,
        v,
        o,
        q.stride(0),
        q.stride(1),
        q.stride(2),
        q.stride(3),
        k.stride(0),
        k.stride(1),
        k.stride(2),
        k.stride(3),
        v.stride(0),
        v.stride(1),
        v.stride(2),
        v.stride(3),
        o.stride(0),
        o.stride(1),
        o.stride(2),
        o.stride(3),
        B,
        H,
        N,
        D,
        window,
        sm_scale,
        BLOCK_W=256,
        BLOCK_DMODEL=128,
        num_warps=4,
        num_stages=2,
    )
    return o


def local_attention_torch(
    q: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    window: int,
    sm_scale: float | None = None,
) -> torch.Tensor:
    _check_inputs(q, k, v)
    B, H, N, D = q.shape
    if sm_scale is None:
        sm_scale = 1.0 / math.sqrt(D)

    scores = torch.matmul(q, k.transpose(-1, -2)) * sm_scale

    idx_q = torch.arange(N, device=q.device).view(N, 1)
    idx_k = torch.arange(N, device=q.device).view(1, N)
    causal = idx_k <= idx_q
    local = idx_k >= (idx_q - window + 1)
    mask = causal & local

    scores = scores.masked_fill(~mask.view(1, 1, N, N), float("-inf"))
    probs = torch.softmax(scores, dim=-1)
    return torch.matmul(probs, v)


def bytes_moved_estimate(q: torch.Tensor) -> int:
    return (q.numel() * 4) * q.element_size()


def benchmark_pair(
    q: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    window: int,
    warmup: int,
    iters: int,
) -> Tuple[float, float, float, float]:
    for _ in range(warmup):
        _ = local_attention_triton(q, k, v, window)
    torch.cuda.synchronize()
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    start.record()
    for _ in range(iters):
        _ = local_attention_triton(q, k, v, window)
    end.record()
    torch.cuda.synchronize()
    triton_ms = start.elapsed_time(end) / iters

    for _ in range(warmup):
        _ = local_attention_torch(q, k, v, window)
    torch.cuda.synchronize()
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    start.record()
    for _ in range(iters):
        _ = local_attention_torch(q, k, v, window)
    end.record()
    torch.cuda.synchronize()
    torch_ms = start.elapsed_time(end) / iters

    bytes_rw = bytes_moved_estimate(q)
    triton_gbs = bytes_rw / (triton_ms * 1e-3) / 1e9
    torch_gbs = bytes_rw / (torch_ms * 1e-3) / 1e9
    return triton_ms, torch_ms, triton_gbs, torch_gbs
