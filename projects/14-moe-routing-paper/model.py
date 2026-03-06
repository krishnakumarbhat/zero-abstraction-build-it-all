from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class MoEConfig:
    input_dim: int = 64
    model_dim: int = 128
    hidden_dim: int = 256
    classes: int = 8
    experts: int = 8
    top_k: int = 2
    dropout: float = 0.1


class ExpertMLP(nn.Module):
    def __init__(self, model_dim: int, hidden_dim: int, dropout: float):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(model_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, model_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class NoisyTopKRouter(nn.Module):
    def __init__(self, model_dim: int, experts: int, top_k: int):
        super().__init__()
        self.experts = experts
        self.top_k = top_k
        self.gate = nn.Linear(model_dim, experts)
        self.noise = nn.Linear(model_dim, experts)

    def forward(self, x: torch.Tensor, noisy: bool = True):
        # x: [tokens, d]
        logits = self.gate(x)
        if noisy and self.training:
            noise_std = F.softplus(self.noise(x)) + 1e-2
            logits = logits + torch.randn_like(logits) * noise_std

        topk_val, topk_idx = torch.topk(logits, k=self.top_k, dim=-1)
        topk_prob = F.softmax(topk_val, dim=-1)

        gates = torch.zeros_like(logits)
        gates.scatter_(1, topk_idx, topk_prob)
        return gates, logits


class MoELayer(nn.Module):
    def __init__(self, cfg: MoEConfig):
        super().__init__()
        self.cfg = cfg
        self.router = NoisyTopKRouter(cfg.model_dim, cfg.experts, cfg.top_k)
        self.experts = nn.ModuleList(
            [ExpertMLP(cfg.model_dim, cfg.hidden_dim, cfg.dropout) for _ in range(cfg.experts)]
        )
        self.norm = nn.LayerNorm(cfg.model_dim)

    def forward(self, x: torch.Tensor):
        # x: [B, T, D]
        b, t, d = x.shape
        tokens = x.reshape(b * t, d)
        gates, logits = self.router(tokens, noisy=True)

        out = torch.zeros_like(tokens)
        expert_load = []
        for expert_idx, expert in enumerate(self.experts):
            w = gates[:, expert_idx]
            mask = w > 0
            expert_load.append(mask.float().mean())
            if mask.any():
                selected = tokens[mask]
                y = expert(selected)
                out[mask] += y * w[mask].unsqueeze(-1)

        out = out.reshape(b, t, d)
        out = self.norm(out + x)

        # Auxiliary losses/metrics for balancing and sparsity behavior.
        route_probs = F.softmax(logits, dim=-1)
        importance = route_probs.mean(dim=0)
        load = torch.stack(expert_load)
        balance_loss = self.cfg.experts * torch.sum(importance * load)

        eps = 1e-8
        entropy = -(route_probs * torch.log(route_probs + eps)).sum(dim=-1).mean()
        utilization_entropy = -(load * torch.log(load + eps)).sum()

        aux = {
            "balance_loss": balance_loss,
            "router_entropy": entropy,
            "utilization_entropy": utilization_entropy,
            "expert_load": load.detach(),
            "importance": importance.detach(),
        }
        return out, aux


class MoEClassifier(nn.Module):
    def __init__(self, cfg: MoEConfig):
        super().__init__()
        self.cfg = cfg
        self.input = nn.Linear(cfg.input_dim, cfg.model_dim)
        self.moe = MoELayer(cfg)
        self.head = nn.Linear(cfg.model_dim, cfg.classes)

    def forward(self, x: torch.Tensor):
        h = self.input(x)
        h, aux = self.moe(h)
        pooled = h.mean(dim=1)
        logits = self.head(pooled)
        return logits, aux


def count_params(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())
