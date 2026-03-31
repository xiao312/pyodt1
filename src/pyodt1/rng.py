from __future__ import annotations

from dataclasses import dataclass


_SEED_TABLE = [984573405, 238400857, 757234405, 430904431, 175728293]


@dataclass(slots=True)
class OdtRNG:
    """Port of the legacy `Brng` generator used by `odt1`.

    If `seed_index` is given, seeds are initialized using the same pattern as `BSeeds.f`
    and warmed up for 100 draws. Otherwise explicit seeds may be supplied.
    """

    seed_index: int | None = None
    i1: int | None = None
    i2: int | None = None

    def __post_init__(self) -> None:
        if self.seed_index is not None:
            idx = int(self.seed_index)
            if idx < 1 or idx > 5:
                raise ValueError("seed_index must be in 1..5")
            self.i1 = _SEED_TABLE[idx - 1]
            self.i2 = _SEED_TABLE[idx % 5]
            for _ in range(100):
                self.uniform()
        else:
            if self.i1 is None or self.i2 is None:
                self.i1 = 984573405
                self.i2 = 238400857

    def uniform(self) -> float:
        ik = self.i1 // 53668
        self.i1 = 40014 * (self.i1 - ik * 53668) - ik * 12211
        if self.i1 < 0:
            self.i1 += 2147483563

        ik = self.i2 // 52774
        self.i2 = 40692 * (self.i2 - ik * 52774) - ik * 3791
        if self.i2 < 0:
            self.i2 += 2147483399

        ix = self.i1 - self.i2
        if ix < 1:
            ix += 2147483562
        return float(ix) * 4.65661305956e-10

    def get_state(self) -> tuple[int, int]:
        return int(self.i1), int(self.i2)

    def put_state(self, i1: int, i2: int) -> None:
        self.i1 = int(i1)
        self.i2 = int(i2)
