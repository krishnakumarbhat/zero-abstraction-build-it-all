import torch
from torch.utils.data import DataLoader, Dataset, random_split


class RoutingDataset(Dataset):
    def __init__(self, samples: int, seq_len: int, input_dim: int, classes: int, seed: int = 42):
        g = torch.Generator().manual_seed(seed)
        self.x = torch.randn(samples, seq_len, input_dim, generator=g)

        # Controlled target mapping that benefits from conditional routing.
        # Different feature groups dominate different classes.
        group_size = max(1, input_dim // classes)
        scores = []
        for class_idx in range(classes):
            start = (class_idx * group_size) % input_dim
            end = min(input_dim, start + group_size)
            score = self.x[:, :, start:end].mean(dim=(1, 2))
            scores.append(score)
        logits = torch.stack(scores, dim=-1) + 0.1 * torch.randn(samples, classes, generator=g)
        self.y = logits.argmax(dim=-1)

    def __len__(self):
        return self.x.shape[0]

    def __getitem__(self, idx: int):
        return self.x[idx], self.y[idx]


def build_loaders(
    samples: int,
    seq_len: int,
    input_dim: int,
    classes: int,
    batch_size: int,
):
    dataset = RoutingDataset(samples, seq_len, input_dim, classes)
    n_train = int(0.8 * len(dataset))
    n_val = len(dataset) - n_train
    train_ds, val_ds = random_split(dataset, [n_train, n_val])

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=2, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=2, pin_memory=True)
    return train_loader, val_loader
