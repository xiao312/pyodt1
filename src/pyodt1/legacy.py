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
    log_path: Path


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


def _legacy_expected_output_names(ioptions: np.ndarray) -> list[str]:
    names = ["T.dat"]
    if int(ioptions[0]) == 0:
        for istat in range(1, 5):
            for prefix in ("A", "B", "C", "D"):
                names.append(f"{prefix}{istat}.dat")
    else:
        for istat in range(1, 5):
            for prefix in ("A", "B", "C", "D", "E", "F", "G"):
                names.append(f"{prefix}{istat}.dat")
    for istat in range(1, 5):
        names.append(f"H{istat}.dat")
        names.append(f"I{istat}.dat")
    return names


def _touch_legacy_output_set(output_dir: Path, ioptions: np.ndarray) -> None:
    for name in _legacy_expected_output_names(ioptions):
        (output_dir / name).touch()



def write_legacy_output_set(config: OdtConfig, result: MultiIterationResult, output_dir: str | Path, state_u: np.ndarray, state_v: np.ndarray, state_w: np.ndarray) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    _touch_legacy_output_set(out, config.ioptions)

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


def _write_legacy_log(config: OdtConfig, output_dir: Path) -> Path:
    log_path = output_dir / "fort.11"
    lines: list[str] = []
    for iter_idx in range(1, config.niter + 1):
        for istat in range(1, config.nstat + 1):
            lines.append(f" iter,istat=  {iter_idx:11d}{istat:12d}")
    log_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return log_path



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
    outdir.mkdir(parents=True, exist_ok=True)
    write_legacy_output_set(config, result, outdir, solver.state.u.copy(), solver.state.v.copy(), solver.state.w.copy())
    log_path = _write_legacy_log(config, outdir)
    return LegacyRunOutputs(config=config, result=result, output_dir=outdir, log_path=log_path)
