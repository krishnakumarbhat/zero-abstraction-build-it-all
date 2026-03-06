import argparse
import subprocess
from datetime import datetime


def parse_list(values: str):
    return [float(v.strip()) for v in values.split(",") if v.strip()]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--lambdas", type=str, default="0.0,0.01,0.05")
    p.add_argument("--entropy-coefs", type=str, default="0.0,0.001")
    p.add_argument("--epochs", type=int, default=2)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--samples", type=int, default=8000)
    p.add_argument("--seq-len", type=int, default=64)
    p.add_argument("--input-dim", type=int, default=64)
    p.add_argument("--classes", type=int, default=8)
    p.add_argument("--experts", type=int, default=8)
    p.add_argument("--top-k", type=int, default=2)
    p.add_argument("--quick", action="store_true")
    p.add_argument("--report", type=str, default="ABLATION_REPORT.md")
    return p.parse_args()


def run_train(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    return proc.stdout


def extract_last_metrics(output: str):
    lines = [line.strip() for line in output.splitlines() if line.strip().startswith("epoch=")]
    if not lines:
        return {}
    last = lines[-1]
    out = {}
    for token in last.replace("=", " ").split():
        pass
    for part in last.split():
        if "=" in part:
            k, v = part.split("=", 1)
            try:
                out[k] = float(v)
            except ValueError:
                continue
    return out


def main():
    args = parse_args()

    lambdas = [0.0, 0.01] if args.quick else parse_list(args.lambdas)
    entropies = [0.0, 0.001] if args.quick else parse_list(args.entropy_coefs)
    epochs = 1 if args.quick else args.epochs
    samples = 2048 if args.quick else args.samples

    results = []
    for lb in lambdas:
        for le in entropies:
            cmd = [
                "python3",
                "train_moe.py",
                "--epochs",
                str(epochs),
                "--batch-size",
                str(args.batch_size),
                "--samples",
                str(samples),
                "--seq-len",
                str(args.seq_len),
                "--input-dim",
                str(args.input_dim),
                "--classes",
                str(args.classes),
                "--experts",
                str(args.experts),
                "--top-k",
                str(args.top_k),
                "--lambda-balance",
                str(lb),
                "--lambda-entropy",
                str(le),
                "--save",
                f"ablation_lb{lb}_le{le}.pt",
            ]
            output = run_train(cmd)
            metrics = extract_last_metrics(output)
            metrics["lambda_balance"] = lb
            metrics["lambda_entropy"] = le
            results.append(metrics)
            print(
                f"lambda_balance={lb} lambda_entropy={le} "
                f"val_acc={metrics.get('val_acc', float('nan')):.4f} "
                f"balance={metrics.get('balance', float('nan')):.4f}"
            )

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# MoE Router Ablation Report",
        "",
        f"Generated: {ts}",
        f"Quick mode: {args.quick}",
        "",
        "| lambda_balance | lambda_entropy | val_acc | balance | router_entropy | util_entropy |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        lines.append(
            "| {lambda_balance:.4f} | {lambda_entropy:.4f} | {val_acc:.4f} | {balance:.4f} | {router_entropy:.4f} | {util_entropy:.4f} |".format(
                lambda_balance=r.get("lambda_balance", 0.0),
                lambda_entropy=r.get("lambda_entropy", 0.0),
                val_acc=r.get("val_acc", float("nan")),
                balance=r.get("balance", float("nan")),
                router_entropy=r.get("router_entropy", float("nan")),
                util_entropy=r.get("util_entropy", float("nan")),
            )
        )

    with open(args.report, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"report written: {args.report}")


if __name__ == "__main__":
    main()
