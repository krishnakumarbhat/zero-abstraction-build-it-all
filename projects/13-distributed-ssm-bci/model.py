import math
from dataclasses import dataclass

import torch
import torch.nn as nn


@dataclass
class ModelConfig:
    channels: int = 32
    hidden: int = 128
    layers: int = 4
    classes: int = 4
    dropout: float = 0.1


class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        norm = x.pow(2).mean(dim=-1, keepdim=True)
        x = x * torch.rsqrt(norm + self.eps)
        return x * self.weight


class MinimalMambaBlock(nn.Module):
    def __init__(self, dim: int, expand: int = 2, dropout: float = 0.1):
        super().__init__()
        inner = dim * expand
        self.in_proj = nn.Linear(dim, inner)
        self.gate_proj = nn.Linear(dim, inner)
        self.out_proj = nn.Linear(inner, dim)

        self.a_log = nn.Parameter(torch.zeros(inner))
        self.b_proj = nn.Linear(inner, inner)
        self.c_proj = nn.Linear(inner, inner)
        self.d_proj = nn.Linear(inner, inner)

        self.norm = RMSNorm(dim)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, T, D]
        residual = x
        x = self.norm(x)

        u = self.in_proj(x)
        g = torch.sigmoid(self.gate_proj(x))
        u = u * g

        b = self.b_proj(u)
        c = self.c_proj(u)
        d = self.d_proj(u)

        bsz, seq_len, inner = u.shape
        h = torch.zeros((bsz, inner), device=x.device, dtype=x.dtype)

        dt = 1.0
        a = torch.exp(-dt * torch.nn.functional.softplus(self.a_log)).view(1, inner)

        ys = []
        for t in range(seq_len):
            h = a * h + b[:, t, :]
            y_t = c[:, t, :] * h + d[:, t, :]
            ys.append(y_t)
        y = torch.stack(ys, dim=1)

        y = self.out_proj(y)
        y = self.dropout(y)
        return residual + y


class SSMClassifier(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        self.input = nn.Linear(cfg.channels, cfg.hidden)
        self.blocks = nn.ModuleList(
            [MinimalMambaBlock(cfg.hidden, expand=2, dropout=cfg.dropout) for _ in range(cfg.layers)]
        )
        self.norm = RMSNorm(cfg.hidden)
        self.head = nn.Linear(cfg.hidden, cfg.classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, T, C]
        h = self.input(x)
        for block in self.blocks:
            h = block(h)
        h = self.norm(h)
        pooled = h.mean(dim=1)
        return self.head(pooled)


class GRUClassifier(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        num_layers = max(1, cfg.layers // 2)
        rnn_dropout = cfg.dropout if num_layers > 1 else 0.0
        self.rnn = nn.GRU(
            input_size=cfg.channels,
            hidden_size=cfg.hidden,
            num_layers=num_layers,
            batch_first=True,
            dropout=rnn_dropout,
        )
        self.head = nn.Linear(cfg.hidden, cfg.classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.rnn(x)
        pooled = out.mean(dim=1)
        return self.head(pooled)


class LSTMClassifier(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        num_layers = max(1, cfg.layers // 2)
        rnn_dropout = cfg.dropout if num_layers > 1 else 0.0
        self.rnn = nn.LSTM(
            input_size=cfg.channels,
            hidden_size=cfg.hidden,
            num_layers=num_layers,
            batch_first=True,
            dropout=rnn_dropout,
        )
        self.head = nn.Linear(cfg.hidden, cfg.classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.rnn(x)
        pooled = out.mean(dim=1)
        return self.head(pooled)


def count_params(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())
