from __future__ import annotations

import numpy as np


def kernel_norm_squared(u_kernel: float, v_kernel: float, w_kernel: float) -> float:
    return u_kernel * u_kernel + v_kernel * v_kernel + w_kernel * w_kernel


def acceptance_probability(
    *,
    nmesh: int,
    l3: int,
    dt: float,
    pl: np.ndarray,
    ratefac: float,
    viscpen: float,
    u_kernel: float,
    v_kernel: float,
    w_kernel: float,
) -> float:
    """Python port of the main formula in `BProb.f`."""
    l = 3 * l3
    p = kernel_norm_squared(u_kernel, v_kernel, w_kernel) - viscpen / float(l) ** 2
    if p <= 0.0:
        return 0.0
    disfac = 1.0 - 3.0 / float(l)
    if disfac <= 0.0:
        return 0.0
    # `pl` stores the Fortran cumulative distribution PL(I) in zero-based form,
    # so Python index `k-1` corresponds to Fortran index `k`.
    prob_l = float(pl[l3 - 1] - pl[l3 - 2])
    if prob_l <= 0.0:
        return 0.0
    return (ratefac / (disfac * float(l) ** 3)) * np.sqrt(p) * dt * (nmesh - l) / prob_l
