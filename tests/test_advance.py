import numpy as np

from pyodt1.advance import advance_diffusion, compute_initial_dt, compute_td, equation_step, generate_initial_state, sample_exponential_wait
from pyodt1.config import OdtConfig
from pyodt1.rng import OdtRNG
from pyodt1.state import OdtState


def _config(nmesh: int = 8, visc: float = 0.5, pgrad: float = 1.0) -> OdtConfig:
    ioptions = np.zeros(100, dtype=int)
    ipars = np.zeros(100, dtype=int)
    ipars[0] = nmesh
    ipars[1] = 2
    ipars[2] = 2
    ipars[3] = 3
    ipars[4] = nmesh
    ipars[5] = 1
    rpars = np.zeros(100, dtype=float)
    rpars[0] = 0.5
    rpars[1] = 0.2
    rpars[2] = 1.5
    rpars[3] = 0.5
    rpars[4] = 0.5
    rpars[5] = -1.0
    return OdtConfig(
        niter=1,
        nstat=1,
        ntseg=1,
        tend=0.01,
        dom=1.0,
        visc=visc,
        pgrad=pgrad,
        ratefac=1.0,
        viscpen=0.0,
        nmesh=nmesh,
        ioptions=ioptions,
        ipars=ipars,
        rpars=rpars,
        nopt=0,
        nipars=6,
        nrpars=6,
    )


def test_advance_diffusion_preserves_last_cell():
    arr = np.array([1.0, 2.0, 3.0, 4.0])
    out = advance_diffusion(arr, tstep=0.01, dom=1.0, visc=0.1, force=0.0)
    assert out[-1] == arr[-1]


def test_equation_step_advances_time_and_changes_u_with_pressure_gradient():
    cfg = _config()
    state = OdtState(np.zeros(cfg.nmesh), np.zeros(cfg.nmesh), np.zeros(cfg.nmesh), time=0.0)
    out = equation_step(state, delt=1.0e-4, dom=cfg.dom, visc=cfg.visc, pgrad=cfg.pgrad, rpars=cfg.rpars)
    assert out.time == state.time + 1.0e-4
    assert np.any(out.u[:-1] != 0.0)
    assert np.allclose(out.v, 0.0)
    assert np.allclose(out.w, 0.0)


def test_compute_initial_dt_and_td_follow_inititer_formula():
    cfg = _config(nmesh=10, visc=2.0, pgrad=0.0)
    dt = compute_initial_dt(cfg)
    expected = 0.2 * cfg.dom**2 / (cfg.visc * cfg.nmesh**3)
    assert dt == expected
    assert compute_td(dt, cfg) == cfg.rpars[3] * dt


def test_generate_initial_state_is_wall_pinned_at_upper_boundary():
    rng = OdtRNG(seed_index=1)
    state = generate_initial_state(12, 1.0, rng)
    assert state.u.shape == (12,)
    assert state.v.shape == (12,)
    assert state.w.shape == (12,)
    assert state.u[-1] == 0.0
    assert state.v[-1] == 0.0
    assert state.w[-1] == 0.0


def test_sample_exponential_wait_positive():
    rng = OdtRNG(seed_index=1)
    wait = sample_exponential_wait(0.1, rng)
    assert wait > 0.0
