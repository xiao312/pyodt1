from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from pyodt1.config import OdtConfig, load_legacy_case, read_options
from pyodt1.rng import OdtRNG
from pyodt1.solver import MultiIterationResult, OdtSolver
from pyodt1.statistics import (
    EddyStatistics,
    SeriesData,
    TimeStatistics,
    compute_snap_outputs,
    initialize_eddy_statistics,
    initialize_series,
    initialize_time_statistics,
    write_series_text,
    write_snap_intercomparison,
    write_snap_xmgrace,
)


@dataclass(slots=True)
class LegacyStatsBundle:
    series: SeriesData
    time_statistics: TimeStatistics
    eddy_statistics: EddyStatistics


@dataclass(slots=True)
class LegacyRunOutputs:
    config: OdtConfig
    result: MultiIterationResult
    output_dir: Path


def b_read_options(path: str | Path) -> tuple[np.ndarray, int]:
    return read_options(path)


def b_init_stats(nmesh: int, nstat: int, mval: int = 10, max_points: int = 10000) -> LegacyStatsBundle:
    return LegacyStatsBundle(
        series=initialize_series(max_points=max_points),
        time_statistics=initialize_time_statistics(nmesh=nmesh, nstat=nstat, mval=mval),
        eddy_statistics=initialize_eddy_statistics(nmesh=nmesh, nstat=nstat),
    )


def b_add_term(i: int, nmesh: int, cstat: np.ndarray, term: np.ndarray, istat: int) -> None:
    cstat[: int(nmesh), int(i) - 1, int(istat) - 1] += np.asarray(term, dtype=float)[: int(nmesh)]


def brng_get(rng: OdtRNG) -> tuple[int, int]:
    return rng.get_state()


def brng_put(rng: OdtRNG, i1: int, i2: int) -> None:
    rng.put_state(i1, i2)


def write_legacy_output_set(config: OdtConfig, result: MultiIterationResult, output_dir: str | Path, state_u: np.ndarray, state_v: np.ndarray, state_w: np.ndarray) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    t_text = write_series_text(result.niter, result.itime, config.tend, config.ntseg, result.series, config.ioptions)
    (out / "T.dat").write_text(t_text, encoding="utf-8")

    if result.cstat is None or result.edstat is None:
        return out

    for istat in range(1, config.nstat + 1):
        snap = compute_snap_outputs(
            config.nmesh,
            state_u,
            state_v,
            state_w,
            config.dom,
            config.visc,
            istat,
            result.edstat,
            result.cstat,
        )
        if int(config.ioptions[0]) == 0:
            write_snap_intercomparison(out, istat, snap)
        else:
            write_snap_xmgrace(out, istat, snap)
    return out


def run_legacy_case(case_dir: str | Path, *, seed_index: int = 1, output_dir: str | Path | None = None, max_trials: int | None = None) -> LegacyRunOutputs:
    case_dir = Path(case_dir)
    config = load_legacy_case(case_dir)
    solver = OdtSolver.from_legacy_case(case_dir, seed_index=seed_index)
    result = solver.run_iterations(
        niter=config.niter,
        tend=config.tend,
        nstat=config.nstat,
        ntseg=config.ntseg,
        max_trials=max_trials,
        collect_stats=True,
    )
    outdir = case_dir if output_dir is None else Path(output_dir)
    write_legacy_output_set(config, result, outdir, solver.state.u.copy(), solver.state.v.copy(), solver.state.w.copy())
    return LegacyRunOutputs(config=config, result=result, output_dir=outdir)
