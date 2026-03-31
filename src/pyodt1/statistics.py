from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from pyodt1.state import OdtState


MAX_SERIES_POINTS = 10000
MVAL = 10


@dataclass(slots=True)
class SeriesData:
    sums: np.ndarray


@dataclass(slots=True)
class TimeStatistics:
    cstat: np.ndarray


def initialize_series(max_points: int = MAX_SERIES_POINTS) -> SeriesData:
    return SeriesData(sums=np.zeros((2, int(max_points)), dtype=float))


def initialize_time_statistics(nmesh: int, nstat: int, mval: int = MVAL) -> TimeStatistics:
    return TimeStatistics(cstat=np.zeros((int(nmesh), int(mval), int(nstat)), dtype=float))


def accumulate_series(series: SeriesData, itime: int, u: np.ndarray) -> None:
    if 1 <= itime <= series.sums.shape[1]:
        ictr = max(0, int(0.5 * len(u)) - 1)
        series.sums[0, itime - 1] += float(u[ictr])
        series.sums[1, itime - 1] += float(u[ictr] ** 2)


def accumulate_cstats(stats: TimeStatistics, state: OdtState, tstep: float, istat: int) -> None:
    idx = int(istat) - 1
    cstat = stats.cstat
    u = state.u
    v = state.v
    w = state.w
    cstat[:, 0, idx] += float(tstep)
    cstat[:, 1, idx] += u * float(tstep)
    cstat[:, 2, idx] += v * float(tstep)
    cstat[:, 3, idx] += w * float(tstep)
    cstat[:, 4, idx] += (u * u) * float(tstep)
    cstat[:, 5, idx] += (v * v) * float(tstep)
    cstat[:, 6, idx] += (w * w) * float(tstep)

    du2 = np.empty_like(u)
    dv2 = np.empty_like(v)
    dw2 = np.empty_like(w)
    du2[0] = u[0] ** 2
    dv2[0] = v[0] ** 2
    dw2[0] = w[0] ** 2
    du2[1:] = (u[1:] - u[:-1]) ** 2
    dv2[1:] = (v[1:] - v[:-1]) ** 2
    dw2[1:] = (w[1:] - w[:-1]) ** 2
    cstat[:, 7, idx] += du2 * float(tstep)
    cstat[:, 8, idx] += dv2 * float(tstep)
    cstat[:, 9, idx] += dw2 * float(tstep)


def finalize_series_variance(niter: int, itime: int, tend: float, umoms: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if itime <= 0:
        return np.zeros(0, dtype=float), np.zeros(0, dtype=float)
    time = np.array([(j + 1) * (float(tend) / float(itime)) for j in range(itime)], dtype=float)
    mean_u = umoms[0, :itime] / float(niter)
    var_u = (umoms[1, :itime] / float(niter)) - mean_u**2
    return time, var_u


def write_series_text(niter: int, itime: int, tend: float, ntseg: int, umoms: np.ndarray, ioptions: np.ndarray) -> str:
    del ntseg  # matches Fortran signature; not used in output formula
    time, variance = finalize_series_variance(niter, itime, tend, umoms)
    if int(ioptions[0]) == 0:
        lines = [str(itime)]
        lines.append("".join(f"{x:15.7E}\n" for x in time).rstrip("\n"))
        lines.append("".join(f"{x:15.7E}\n" for x in variance).rstrip("\n"))
        return "\n".join(lines) + "\n"

    return "".join(f"{t:15.7E}{v:15.7E}\n" for t, v in zip(time, variance, strict=False))
