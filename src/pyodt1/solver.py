from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from pyodt1.advance import compute_initial_dt, compute_td, equation_step, generate_initial_state, sample_exponential_wait
from pyodt1.config import EddySample, EddySizeDistribution, OdtConfig, load_legacy_case
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


@dataclass(slots=True)
class RunResult:
    state: OdtState
    trial_count: int
    accepted_count: int
    rejected_count: int
    dt: float
    td: float
    scheduled_time: float
    physical_time: float


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

    @classmethod
    def from_legacy_case(cls, directory: str, seed_index: int = 1) -> "OdtSolver":
        config = load_legacy_case(directory)
        rng = OdtRNG(seed_index=seed_index)
        state = generate_initial_state(config.nmesh, config.dom, rng)
        return cls(config=config, state=state, rng=rng)

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

    def raise_dt(self, dt: float, td: float) -> tuple[float, float]:
        iwait = int(self.config.ipars[1]) if self.config.nipars >= 2 else 0
        if iwait <= 0 or self.ii % iwait != 0:
            return dt, td

        pa = self.pa / float(self.np_nonzero) if self.np_nonzero > 0 else self.pa
        pmin = float(self.config.rpars[1]) if self.config.nrpars >= 2 else 0.0
        dtfac = float(self.config.rpars[2]) if self.config.nrpars >= 3 else 1.0
        tdfac = float(self.config.rpars[3]) if self.config.nrpars >= 4 else 0.0
        if pa < pmin:
            if pa < pmin / dtfac:
                dt = dt * dtfac
            elif pa > 0.0:
                dt = dt * pmin / pa
        td = tdfac * dt
        self.pa = 0.0
        self.np_nonzero = 0
        return float(dt), float(td)

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

    def run_realization(
        self,
        tend: float | None = None,
        *,
        dt: float | None = None,
        td: float | None = None,
        max_trials: int | None = None,
    ) -> RunResult:
        if tend is None:
            tend = float(self.config.tend)
        if dt is None:
            dt = compute_initial_dt(self.config)
        if td is None:
            td = compute_td(dt, self.config)

        scheduled_time = self.state.time + sample_exponential_wait(dt, self.rng)
        physical_time = float(self.state.time)
        accepted_count = 0
        rejected_count = 0

        while scheduled_time <= tend and (max_trials is None or self.ii < max_trials):
            if (scheduled_time - physical_time) >= td:
                self.state = equation_step(self.state, scheduled_time - physical_time, self.config.dom, self.config.visc, self.config.pgrad, self.config.rpars)
                physical_time = scheduled_time

            sample, dt, td = self.sample_only(dt, td)
            accepted = False
            if sample.acceptance_probability > 0.0 and self.rng.uniform() < sample.acceptance_probability:
                self.apply_eddy(sample)
                accepted = True
                accepted_count += 1
                if scheduled_time > physical_time:
                    self.state = equation_step(self.state, scheduled_time - physical_time, self.config.dom, self.config.visc, self.config.pgrad, self.config.rpars)
                    physical_time = scheduled_time
            else:
                rejected_count += 1

            scheduled_time = scheduled_time + sample_exponential_wait(dt, self.rng)
            dt, td = self.raise_dt(dt, td)

        if tend > physical_time:
            self.state = equation_step(self.state, tend - physical_time, self.config.dom, self.config.visc, self.config.pgrad, self.config.rpars)
            physical_time = tend

        self.state.time = physical_time
        return RunResult(
            state=self.state.copy(),
            trial_count=self.ii,
            accepted_count=accepted_count,
            rejected_count=rejected_count,
            dt=float(dt),
            td=float(td),
            scheduled_time=float(scheduled_time),
            physical_time=float(physical_time),
        )
