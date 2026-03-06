#!/usr/bin/env python3
import math
import random
import sys


def matmul(a, b):
    n, m, p = len(a), len(a[0]), len(b[0])
    out = [[0.0 for _ in range(p)] for _ in range(n)]
    for i in range(n):
        for k in range(m):
            for j in range(p):
                out[i][j] += a[i][k] * b[k][j]
    return out


def add_bias(x, b):
    return [[x[i][j] + b[j] for j in range(len(b))] for i in range(len(x))]


def relu(x):
    return [[v if v > 0 else 0.0 for v in row] for row in x]


def drelu(x):
    return [[1.0 if v > 0 else 0.0 for v in row] for row in x]


def transpose(x):
    return [list(c) for c in zip(*x)]


def sub(a, b):
    return [[a[i][j] - b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def mul_elem(a, b):
    return [[a[i][j] * b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def scale(a, s):
    return [[v * s for v in row] for row in a]


def mean_rows(x):
    n = len(x)
    return [sum(row[j] for row in x) / n for j in range(len(x[0]))]


def mse(yhat, y):
    n = len(y)
    s = 0.0
    for i in range(n):
        s += sum((yhat[i][j] - y[i][j]) ** 2 for j in range(len(y[0])))
    return s / n


class TinyNN:
    def __init__(self, in_dim=2, hidden=8, out_dim=1):
        rnd = lambda: random.uniform(-0.5, 0.5)
        self.w1 = [[rnd() for _ in range(hidden)] for _ in range(in_dim)]
        self.b1 = [0.0 for _ in range(hidden)]
        self.w2 = [[rnd() for _ in range(out_dim)] for _ in range(hidden)]
        self.b2 = [0.0 for _ in range(out_dim)]

    def forward(self, x):
        z1 = add_bias(matmul(x, self.w1), self.b1)
        a1 = relu(z1)
        z2 = add_bias(matmul(a1, self.w2), self.b2)
        return z1, a1, z2

    def train_step(self, x, y, lr=0.05):
        z1, a1, yhat = self.forward(x)
        n = len(x)

        dy = scale(sub(yhat, y), 2.0 / n)
        dw2 = matmul(transpose(a1), dy)
        db2 = mean_rows(dy)

        da1 = matmul(dy, transpose(self.w2))
        dz1 = mul_elem(da1, drelu(z1))
        dw1 = matmul(transpose(x), dz1)
        db1 = mean_rows(dz1)

        for i in range(len(self.w2)):
            for j in range(len(self.w2[0])):
                self.w2[i][j] -= lr * dw2[i][j]
        for j in range(len(self.b2)):
            self.b2[j] -= lr * db2[j]

        for i in range(len(self.w1)):
            for j in range(len(self.w1[0])):
                self.w1[i][j] -= lr * dw1[i][j]
        for j in range(len(self.b1)):
            self.b1[j] -= lr * db1[j]

        return mse(yhat, y)


def self_test():
    random.seed(7)
    x = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]
    y = [[0.0], [1.0], [1.0], [0.0]]
    nn = TinyNN(2, 12, 1)
    loss0 = nn.train_step(x, y, 0.01)
    for _ in range(4000):
        loss = nn.train_step(x, y, 0.01)
    assert loss < loss0
    print("ok", round(loss, 4))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        self_test()
        sys.exit(0)
    self_test()
