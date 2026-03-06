import torch

from local_attention import local_attention_torch, local_attention_triton


def run_case(b: int, h: int, n: int, d: int, w: int, dtype: torch.dtype):
    torch.manual_seed(0)
    q = torch.randn((b, h, n, d), device="cuda", dtype=dtype)
    k = torch.randn((b, h, n, d), device="cuda", dtype=dtype)
    v = torch.randn((b, h, n, d), device="cuda", dtype=dtype)

    out_triton = local_attention_triton(q, k, v, window=w)
    out_torch = local_attention_torch(q, k, v, window=w)

    atol = 2e-2 if dtype in (torch.float16, torch.bfloat16) else 1e-3
    rtol = 2e-2 if dtype in (torch.float16, torch.bfloat16) else 1e-3

    ok = torch.allclose(out_triton, out_torch, atol=atol, rtol=rtol)
    max_abs = (out_triton - out_torch).abs().max().item()
    print(
        f"case b={b} h={h} n={n} d={d} w={w} dtype={dtype}: "
        f"allclose={ok} max_abs={max_abs:.6f}"
    )
    if not ok:
        raise SystemExit(1)


def main():
    if not torch.cuda.is_available():
        raise SystemExit("CUDA is required")

    cases = [
        (1, 4, 256, 64, 64, torch.float16),
        (2, 4, 512, 64, 128, torch.float16),
        (1, 2, 384, 32, 96, torch.float32),
    ]

    for case in cases:
        run_case(*case)

    print("All correctness checks passed.")


if __name__ == "__main__":
    main()
