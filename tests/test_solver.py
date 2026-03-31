import numpy as np

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
