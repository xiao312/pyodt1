from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from pyodt1.config import EddySample, EddySizeDistribution, OdtConfig
from pyodt1.eddy_sampling import build_length_distribution, sample_eddy
from pyodt1.rng import OdtRNG
from pyodt1.state import OdtState
from pyodt1.triplet import add_k, triplet_map


@dataclass(slots=True)
class StepResult:
    sample: EddySample
    accepted: bool
    dt: float
    td: float
    state: OdtState
    ii: int
    pa: float
    np_nonzero: int


class OdtSolver:
    def __init__(self, config: OdtConfig, state: OdtState, rng: OdtRNG):
        if config.nmesh != state.nmesh:
            raise ValueError("config.nmesh must match state size")
        self.config = config
        self.state = state
        self.rng = rng
        self.dist: EddySizeDistribution = build_length_distribution(config.nmesh, config.ipars, config.nipars)
        self.ii = 0
        self.pa = 0.0
        self.np_nonzero = 0

    @staticmethod
    def _compute_c_coefficients(l: int, u_k: float, v_k: float, w_k: float) -> tuple[float, float, float]:
        disfac = 1.0 - 3.0 / float(l)
        cfac = 6.75 / (disfac * float(l))
        root = np.sqrt((u_k * u_k + v_k * v_k + w_k * w_k) / 3.0)
        cu = cfac * (-u_k + np.copysign(root, u_k))
        cv = cfac * (-v_k + np.copysign(root, v_k))
        cw = cfac * (-w_k + np.copysign(root, w_k))
        return float(cu), float(cv), float(cw)

    def apply_eddy(self, sample: EddySample) -> None:
        start = sample.m - 1
        cu, cv, cw = self._compute_c_coefficients(sample.l, sample.u_kernel, sample.v_kernel, sample.w_kernel)
        self.state.u = triplet_map(self.state.u, start, sample.l)
        self.state.v = triplet_map(self.state.v, start, sample.l)
        self.state.w = triplet_map(self.state.w, start, sample.l)
        self.state.u = add_k(self.state.u, start, sample.l, cu)
        self.state.v = add_k(self.state.v, start, sample.l, cv)
        self.state.w = add_k(self.state.w, start, sample.l, cw)

    def sample_only(self, dt: float, td: float) -> tuple[EddySample, float, float]:
        self.ii += 1
        sample = sample_eddy(
            nmesh=self.state.nmesh,
            u=self.state.u,
            v=self.state.v,
            w=self.state.w,
            dt=dt,
            dist=self.dist,
            ratefac=self.config.ratefac,
            viscpen=self.config.viscpen,
            rng=self.rng,
        )

        pp = sample.acceptance_probability
        pmax = float(self.config.rpars[0]) if self.config.nrpars >= 1 else 0.0
        tdfac = float(self.config.rpars[3]) if self.config.nrpars >= 4 else 0.0
        if pp > 0.0 and pmax > 0.0 and pp > pmax:
            dt = dt * pmax / pp
            td = tdfac * dt
            pp = pmax
            sample = EddySample(
                m=sample.m,
                l=sample.l,
                l3=sample.l3,
                acceptance_probability=pp,
                u_kernel=sample.u_kernel,
                v_kernel=sample.v_kernel,
                w_kernel=sample.w_kernel,
            )

        if sample.acceptance_probability > 0.0:
            self.pa += sample.acceptance_probability
            self.np_nonzero += 1
        return sample, dt, td

    def one_step(self, dt: float, td: float) -> StepResult:
        sample, dt, td = self.sample_only(dt, td)
        accepted = False
        if sample.acceptance_probability > 0.0 and self.rng.uniform() < sample.acceptance_probability:
            self.apply_eddy(sample)
            accepted = True

        return StepResult(
            sample=sample,
            accepted=accepted,
            dt=dt,
            td=td,
            state=self.state.copy(),
            ii=self.ii,
            pa=self.pa,
            np_nonzero=self.np_nonzero,
        )
