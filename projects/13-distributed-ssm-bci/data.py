import math
import random

import torch
from torch.utils.data import DataLoader, Dataset, DistributedSampler


class SyntheticEEGDataset(Dataset):
    def __init__(self, samples: int, seq_len: int, channels: int, classes: int, seed: int = 42):
        self.samples = samples
        self.seq_len = seq_len
        self.channels = channels
        self.classes = classes
        self.rng = random.Random(seed)

    def __len__(self):
        return self.samples

    def __getitem__(self, idx: int):
        label = idx % self.classes

        t = torch.linspace(0, 1, self.seq_len)
        signal = []
        for channel in range(self.channels):
            base_f = 4.0 + label * 2.0 + (channel % 5) * 0.2
            phase = (channel % 7) * 0.3
            amp = 1.0 + label * 0.1
            wave = amp * torch.sin(2 * math.pi * base_f * t + phase)
            noise = 0.15 * torch.randn_like(wave)
            signal.append(wave + noise)
        x = torch.stack(signal, dim=-1).float()  # [T, C]
        y = torch.tensor(label, dtype=torch.long)
        return x, y


def build_train_loader(
    samples: int,
    seq_len: int,
    channels: int,
    classes: int,
    batch_size: int,
    distributed: bool,
    rank: int,
    world_size: int,
):
    dataset = SyntheticEEGDataset(samples=samples, seq_len=seq_len, channels=channels, classes=classes)
    sampler = None
    if distributed:
        sampler = DistributedSampler(dataset, num_replicas=world_size, rank=rank, shuffle=True)
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        sampler=sampler,
        shuffle=(sampler is None),
        num_workers=2,
        pin_memory=True,
        drop_last=True,
    )
    return loader, sampler
