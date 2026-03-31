from __future__ import annotations

import math
from collections.abc import Callable

import numpy as np

from pyodt1.config import OdtConfig
from pyodt1.rng import OdtRNG
from pyodt1.state import OdtState


DEFAULT_PERTURBATION_AMPLITUDE = 1.0e-8


def advance_diffusion(r: np.ndarray, tstep: float, dom: float, visc: float, force: float) -> np.ndarray:
    """Advance one property field for a single explicit BAdv step.

    This is a direct port of ``BAdv.f``.
    """
    arr = np.asarray(r, dtype=float).copy()
    n = int(arr.size)
    if n < 1:
        raise ValueError("r must contain at least one cell")

    dz = float(dom) / float(n)
    flux = np.empty(n, dtype=float)
    flux[0] = -float(visc) * arr[0] / dz
    for j in range(1, n):
        flux[j] = float(visc) * (arr[j - 1] - arr[j]) / dz

    for j in range(0, n - 1):
        arr[j] = arr[j] + float(tstep) * (((flux[j] - flux[j + 1]) / dz) + float(force))
    return arr


def equation_step(
    state: OdtState,
    delt: float,
    dom: float,
    visc: float,
    pgrad: float,
    rpars: np.ndarray,
    stats_callback: Callable[[OdtState, float], None] | None = None,
) -> OdtState:
    """Advance the deterministic transport equations over ``delt``.

    This ports the numerically active part of ``BEqnStep.f``.
    Statistics accumulation present in the Fortran code is intentionally
    omitted here.
    """
    if delt <= 0.0:
        return state.copy()

    tfrac = float(rpars[4])
    tcfl = 0.5 * (float(dom) / float(state.nmesh)) ** 2 / float(visc)
    irat = int(float(delt) / (tfrac * tcfl))
    et = float(delt) / (float(irat) + 1.0)

    out = state.copy()
    zero = 0.0
    for _ in range(irat + 1):
        if stats_callback is not None:
            stats_callback(out.copy(), et)
        out.u = advance_diffusion(out.u, et, dom, visc, pgrad)
        out.v = advance_diffusion(out.v, et, dom, visc, zero)
        out.w = advance_diffusion(out.w, et, dom, visc, zero)
    out.time = state.time + float(delt)
    return out


def sample_exponential_wait(dt: float, rng: OdtRNG) -> float:
    """Sample an exponential waiting time with mean ``dt``.

    Direct port of ``BExp.f``.
    """
    rannum = rng.uniform()
    return float(-float(dt) * math.log(1.0 - rannum))


def compute_initial_dt(config: OdtConfig) -> float:
    """Compute the initial trial mean waiting time from ``BInitIter.f``."""
    pav = float(config.rpars[1])
    dt = pav * float(config.dom) ** 2 / (float(config.visc) * float(config.nmesh) ** 3)
    if config.nrpars >= 6:
        test = float(config.rpars[5])
        if test > 0.0:
            dt = test
        else:
            dt = abs(test) * dt
    return float(dt)


def compute_td(dt: float, config: OdtConfig) -> float:
    """Compute the deterministic-advance threshold from ``BInitIter.f``."""
    return float(config.rpars[3]) * float(dt)


def generate_initial_state(nmesh: int, dom: float, rng: OdtRNG, amplitude: float = DEFAULT_PERTURBATION_AMPLITUDE) -> OdtState:
    """Generate the default initial velocity fields following ``BInitRun.f``.

    The first ``nmesh - 1`` points receive tiny independent random
    perturbations in each velocity component. The final point is pinned to 0.
    """
    u = np.zeros(int(nmesh), dtype=float)
    v = np.zeros(int(nmesh), dtype=float)
    w = np.zeros(int(nmesh), dtype=float)
    amp = float(amplitude)
    for j in range(0, int(nmesh) - 1):
        u[j] = amp * (rng.uniform() - 0.5)
        v[j] = amp * (rng.uniform() - 0.5)
        w[j] = amp * (rng.uniform() - 0.5)
    u[-1] = 0.0
    v[-1] = 0.0
    w[-1] = 0.0
    return OdtState(u=u, v=v, w=w, time=0.0)
