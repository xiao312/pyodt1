from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class OdtState:
    u: np.ndarray
    v: np.ndarray
    w: np.ndarray
    time: float = 0.0

    def __post_init__(self) -> None:
        self.u = np.asarray(self.u, dtype=float)
        self.v = np.asarray(self.v, dtype=float)
        self.w = np.asarray(self.w, dtype=float)
        if self.u.ndim != 1 or self.v.ndim != 1 or self.w.ndim != 1:
            raise ValueError("u, v, w must be 1D arrays")
        if not (self.u.size == self.v.size == self.w.size):
            raise ValueError("u, v, w must have the same length")

    @property
    def nmesh(self) -> int:
        return int(self.u.size)

    def copy(self) -> "OdtState":
        return OdtState(self.u.copy(), self.v.copy(), self.w.copy(), self.time)
