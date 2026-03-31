from __future__ import annotations

import numpy as np


def triplet_map(values: np.ndarray, start: int, length: int) -> np.ndarray:
    """Apply a discrete triplet map to a 1D array segment.

    Parameters
    ----------
    values:
        Input 1D field.
    start:
        Zero-based starting index of the mapped segment.
    length:
        Segment length. Must be divisible by 3.
    """
    if values.ndim != 1:
        raise ValueError("values must be a 1D array")
    if length <= 0 or length % 3 != 0:
        raise ValueError("length must be positive and divisible by 3")
    if start < 0 or start + length > values.size:
        raise ValueError("mapped segment out of bounds")

    out = values.copy()
    segment = values[start : start + length]
    lo = length // 3

    x = np.empty(length, dtype=values.dtype)
    for j in range(1, lo + 1):
        k = start + 3 * (j - 1)
        x[j - 1] = values[k]
    for j in range(1, lo + 1):
        k = start + length + 1 - (3 * j)
        x[(j - 1) + lo] = values[k]
    for j in range(1, lo + 1):
        k = start + (3 * j) - 1
        x[(j - 1) + 2 * lo] = values[k]

    out[start : start + length] = x
    return out


def add_k(values: np.ndarray, start: int, length: int, coefficient: float) -> np.ndarray:
    """Port of `BAddK.f` using zero-based Python indexing."""
    if values.ndim != 1:
        raise ValueError("values must be a 1D array")
    if length <= 0 or length % 3 != 0:
        raise ValueError("length must be positive and divisible by 3")
    if start < 0 or start + length > values.size:
        raise ValueError("segment out of bounds")

    out = values.copy()
    lo = length // 3
    for j in range(1, lo + 1):
        y1 = -2.0 * (j - 1)
        y2 = 4.0 * (j + lo - 1) - 2.0 * (length - 1)
        y3 = 2.0 * (length - 1) - 2.0 * (j + lo + lo - 1)
        j1 = start + j - 1
        j2 = start + j + lo - 1
        j3 = start + j + lo + lo - 1
        out[j1] += coefficient * y1
        out[j2] += coefficient * y2
        out[j3] += coefficient * y3
    return out
