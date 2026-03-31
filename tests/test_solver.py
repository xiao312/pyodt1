import numpy as np
import pytest

from pyodt1.advance import compute_initial_dt, compute_td
from pyodt1.config import OdtConfig
from pyodt1.eddy_sampling import bs_kd
from pyodt1.rng import OdtRNG
from pyodt1.solver import OdtSolver
from pyodt1.state import OdtState
from pyodt1.triplet import add_k, triplet_map


def _dummy_config(nmesh: int = 30) -> OdtConfig:
    ioptions = np.zeros(100, dtype=int)
    ipars = np.zeros(100, dtype=int)
    ipars[0] = nmesh
    ipars[2] = 2
    ipars[3] = 4
    ipars[4] = 8
    ipars[5] = 1
    rpars = np.zeros(100, dtype=float)
    rpars[0] = 0.4
    rpars[3] = 1.0
    return OdtConfig(
        niter=1,
        nstat=1,
        ntseg=1,
        tend=1.0,
        dom=1.0,
        visc=0.0,
        pgrad=0.0,
        ratefac=1.0,
        viscpen=0.0,
        nmesh=nmesh,
        ioptions=ioptions,
        ipars=ipars,
        rpars=rpars,
        nopt=0,
        nipars=5,
        nrpars=4,
    )


def test_bs_kd_zero_for_constant_signal():
    arr = np.ones(12)
    assert bs_kd(arr, 1, 6) == 0.0


def test_add_k_changes_only_target_range():
    arr = np.zeros(12)
    out = add_k(arr, 3, 6, 1.0)
    assert np.all(out[:3] == 0.0)
    assert np.all(out[9:] == 0.0)
    assert np.any(out[3:9] != 0.0)


def test_solver_one_step_returns_valid_result():
    cfg = _dummy_config()
    state = OdtState(np.linspace(0.0, 1.0, 30), np.zeros(30), np.zeros(30))
    solver = OdtSolver(cfg, state, OdtRNG(seed_index=1))
    result = solver.one_step(dt=0.01, td=0.01)
    assert result.sample.l == 3 * result.sample.l3
    assert result.dt > 0.0
    assert result.td >= 0.0
    assert result.state.nmesh == 30


def test_triplet_then_addk_pipeline_runs():
    arr = np.arange(12, dtype=float)
    mapped = triplet_map(arr, 3, 6)
    shifted = add_k(mapped, 3, 6, 0.1)
    assert shifted.shape == arr.shape


def test_solver_run_realization_advances_to_target_time():
    cfg = _dummy_config(18)
    cfg.visc = 1.0e-5
    cfg.tend = 5.0e-4
    cfg.rpars[1] = 0.2
    cfg.rpars[2] = 1.5
    cfg.rpars[3] = 0.5
    cfg.rpars[4] = 0.5
    cfg.rpars[5] = -1.0
    cfg.nrpars = 6
    cfg.ipars[1] = 2
    cfg.nipars = 6
    state = OdtState(np.linspace(0.0, 1.0, 18), np.zeros(18), np.zeros(18))
    solver = OdtSolver(cfg, state, OdtRNG(seed_index=1))
    result = solver.run_realization(tend=cfg.tend, dt=compute_initial_dt(cfg), td=compute_td(compute_initial_dt(cfg), cfg), max_trials=5)
    assert result.physical_time == pytest.approx(cfg.tend)
    assert result.state.time == pytest.approx(cfg.tend)
    assert result.trial_count <= 5
    assert result.accepted_count + result.rejected_count == result.trial_count


def test_lower_dt_matches_expected_capping_and_accumulation():
    cfg = _dummy_config(18)
    cfg.rpars[0] = 0.4
    cfg.rpars[3] = 0.5
    cfg.nrpars = 4
    state = OdtState(np.zeros(18), np.zeros(18), np.zeros(18))
    solver = OdtSolver(cfg, state, OdtRNG(seed_index=1))
    solver.pa = 0.1
    solver.np_nonzero = 1
    sample = solver.lower_dt(0.1, 0.05, type("S", (), {"m": 1, "l": 6, "l3": 2, "acceptance_probability": 0.8, "u_kernel": 0.0, "v_kernel": 0.0, "w_kernel": 0.0})())
    lowered, dt, td = sample
    assert lowered.acceptance_probability == 0.4
    assert dt == pytest.approx(0.05)
    assert td == pytest.approx(0.025)
    assert solver.pa == 0.5
    assert solver.np_nonzero == 2


def test_run_scheduled_realization_tracks_subinterval_series():
    cfg = _dummy_config(18)
    cfg.visc = 1.0e-5
    cfg.tend = 6.0e-4
    cfg.nstat = 2
    cfg.ntseg = 3
    cfg.rpars[1] = 0.2
    cfg.rpars[2] = 1.5
    cfg.rpars[3] = 0.5
    cfg.rpars[4] = 0.5
    cfg.rpars[5] = -1.0
    cfg.nrpars = 6
    cfg.ipars[1] = 2
    cfg.nipars = 6
    solver = OdtSolver(cfg, OdtState(np.linspace(0.0, 1.0, 18), np.zeros(18), np.zeros(18)), OdtRNG(seed_index=1))
    result = solver.run_scheduled_realization(max_trials=5)
    assert result.itime == cfg.nstat * cfg.ntseg
    assert len(result.centerline_u_sum) == result.itime
    assert len(result.centerline_u2_sum) == result.itime
    assert result.physical_time == pytest.approx(cfg.tend)
