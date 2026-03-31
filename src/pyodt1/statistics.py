from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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


@dataclass(slots=True)
class EddyStatistics:
    edstat: np.ndarray
    old: np.ndarray


@dataclass(slots=True)
class SnapOutputs:
    ht: np.ndarray
    mean_u: np.ndarray
    variances: np.ndarray
    advective_flux_u: np.ndarray
    shear_production: np.ndarray
    advective_transport: np.ndarray
    viscous_transport: np.ndarray
    dissipation: np.ndarray
    balance: np.ndarray
    eddy_count_near_wall: np.ndarray
    eddy_count_far_wall: np.ndarray


@dataclass(slots=True)
class ParsedBRecord:
    header_n: int | None
    records: np.ndarray


@dataclass(slots=True)
class ParsedSnapFiles:
    mode: str
    istat: int
    records: dict[str, np.ndarray]


def initialize_series(max_points: int = MAX_SERIES_POINTS) -> SeriesData:
    return SeriesData(sums=np.zeros((2, int(max_points)), dtype=float))



def initialize_time_statistics(nmesh: int, nstat: int, mval: int = MVAL) -> TimeStatistics:
    return TimeStatistics(cstat=np.zeros((int(nmesh), int(mval), int(nstat)), dtype=float))



def initialize_eddy_statistics(nmesh: int, nstat: int) -> EddyStatistics:
    return EddyStatistics(
        edstat=np.zeros((int(nmesh), 4, 4, int(nstat)), dtype=float),
        old=np.zeros((int(nmesh), 3), dtype=float),
    )



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



def save_old_values(eddy_stats: EddyStatistics, state: OdtState, m: int, l: int) -> None:
    start = int(m) - 1
    stop = start + int(l)
    eddy_stats.old[start:stop, 0] = state.u[start:stop]
    eddy_stats.old[start:stop, 1] = state.v[start:stop]
    eddy_stats.old[start:stop, 2] = state.w[start:stop]



def accumulate_change(
    eddy_stats: EddyStatistics,
    state: OdtState,
    m: int,
    l: int,
    istat: int,
    jj: int,
) -> None:
    idx = int(istat) - 1
    start = int(m) - 1
    stop = start + int(l)
    u = state.u[start:stop]
    v = state.v[start:stop]
    w = state.w[start:stop]
    old = eddy_stats.old[start:stop]

    for j in (1, 2):
        row = j + int(jj) - 1
        eddy_stats.edstat[start:stop, row, 0, idx] += u**j - old[:, 0] ** j
        eddy_stats.edstat[start:stop, row, 1, idx] += v**j - old[:, 1] ** j
        eddy_stats.edstat[start:stop, row, 2, idx] += w**j - old[:, 2] ** j

    if int(jj) == 2:
        return

    n = state.nmesh
    idist = min(int(m), n - int(m) - int(l) + 1)
    j = 0 if idist <= int(l) else 1
    ll = int(l) // 3
    eddy_stats.edstat[ll - 1, j, 3, idx] += 1.0



def finalize_series_variance(niter: int, itime: int, tend: float, umoms: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if itime <= 0:
        return np.zeros(0, dtype=float), np.zeros(0, dtype=float)
    time = np.array([(j + 1) * (float(tend) / float(itime)) for j in range(itime)], dtype=float)
    mean_u = umoms[0, :itime] / float(niter)
    var_u = (umoms[1, :itime] / float(niter)) - mean_u**2
    return time, var_u



def write_series_text(niter: int, itime: int, tend: float, ntseg: int, umoms: np.ndarray, ioptions: np.ndarray) -> str:
    del ntseg
    time, variance = finalize_series_variance(niter, itime, tend, umoms)
    if int(ioptions[0]) == 0:
        lines = [str(itime)]
        lines.append("".join(f"{x:15.7E}\n" for x in time).rstrip("\n"))
        lines.append("".join(f"{x:15.7E}\n" for x in variance).rstrip("\n"))
        return "\n".join(lines) + "\n"
    return "".join(f"{t:15.7E}{v:15.7E}\n" for t, v in zip(time, variance, strict=False))



def brecord_text(n: int, s: np.ndarray) -> str:
    values = np.asarray(s, dtype=float).copy()
    values[np.abs(values) < 1.0e-30] = 0.0
    lines: list[str] = []
    if int(n) < 0:
        lines.append(f"{int(n):6d}")
    for val in values[: abs(int(n))]:
        lines.append(f"{val:15.7E}")
    return "\n".join(lines) + "\n"



def xrecord_text(n: int, x: np.ndarray, s: np.ndarray) -> str:
    xv = np.asarray(x, dtype=float)
    values = np.asarray(s, dtype=float).copy()
    values[np.abs(values) < 1.0e-30] = 0.0
    lines = [f"{xv[j]:15.7E}{values[j]:15.7E}" for j in range(int(n))]
    return "\n".join(lines) + "\n"



def parse_brecord_text(text: str) -> ParsedBRecord:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ParsedBRecord(header_n=None, records=np.zeros((0, 0), dtype=float))

    header_n: int | None = None
    start = 0
    first = lines[0]
    if "E" not in first.upper() and "." not in first:
        header_n = int(first)
        start = 1
    if header_n is None:
        nvals = len(lines) if len(lines) > 0 else 0
    else:
        nvals = abs(header_n)
    values = np.asarray([float(line) for line in lines[start:]], dtype=float)
    if nvals == 0:
        records = np.zeros((0, 0), dtype=float)
    else:
        if values.size % nvals != 0:
            raise ValueError("BRecord text does not contain a whole number of records")
        records = values.reshape(values.size // nvals, nvals)
    return ParsedBRecord(header_n=header_n, records=records)



def parse_xrecord_text(text: str) -> np.ndarray:
    rows = [[float(tok) for tok in line.split()] for line in text.splitlines() if line.strip()]
    if not rows:
        return np.zeros((0, 2), dtype=float)
    return np.asarray(rows, dtype=float)



def parse_eddy_count_text(text: str) -> np.ndarray:
    rows = [[float(tok) for tok in line.split()] for line in text.splitlines() if line.strip()]
    if not rows:
        return np.zeros((0, 3), dtype=float)
    return np.asarray(rows, dtype=float)



def parse_snap_intercomparison(output_dir: str | Path, istat: int) -> ParsedSnapFiles:
    out = Path(output_dir)
    parsed_a = parse_brecord_text((out / f"A{istat}.dat").read_text(encoding="utf-8"))
    parsed_b = parse_brecord_text((out / f"B{istat}.dat").read_text(encoding="utf-8"))
    parsed_c = parse_brecord_text((out / f"C{istat}.dat").read_text(encoding="utf-8"))
    parsed_d = parse_brecord_text((out / f"D{istat}.dat").read_text(encoding="utf-8"))
    parsed_h = parse_xrecord_text((out / f"H{istat}.dat").read_text(encoding="utf-8"))
    parsed_i = parse_eddy_count_text((out / f"I{istat}.dat").read_text(encoding="utf-8"))
    return ParsedSnapFiles(
        mode="intercomparison",
        istat=int(istat),
        records={
            "ht": parsed_a.records[0],
            "mean_u": parsed_a.records[1],
            "variances": parsed_b.records[1:],
            "advective_flux_u": parsed_c.records[1],
            "budget_terms": parsed_d.records[1:],
            "balance_xy": parsed_h,
            "eddy_counts": parsed_i,
        },
    )



def parse_snap_xmgrace(output_dir: str | Path, istat: int) -> ParsedSnapFiles:
    out = Path(output_dir)
    parsed = {
        name: parse_xrecord_text((out / f"{name}{istat}.dat").read_text(encoding="utf-8"))
        for name in ["A", "B", "C", "D", "E", "F", "G", "H"]
    }
    parsed_i = parse_eddy_count_text((out / f"I{istat}.dat").read_text(encoding="utf-8"))
    return ParsedSnapFiles(
        mode="xmgrace",
        istat=int(istat),
        records={
            "A": parsed["A"],
            "B": parsed["B"],
            "C": parsed["C"],
            "D": parsed["D"],
            "E": parsed["E"],
            "F": parsed["F"],
            "G": parsed["G"],
            "H": parsed["H"],
            "eddy_counts": parsed_i,
        },
    )



def compute_snap_outputs(
    nmesh: int,
    u: np.ndarray,
    v: np.ndarray,
    w: np.ndarray,
    dom: float,
    visc: float,
    istat: int,
    edstat: np.ndarray,
    cstat: np.ndarray,
) -> SnapOutputs:
    idx = int(istat) - 1
    width = float(dom) / float(nmesh)
    fluxfac2 = float(visc) / width**2
    cavg = np.zeros((int(nmesh), MVAL), dtype=float)
    for j in range(1, MVAL):
        cavg[:, j] = cstat[:, j, idx] / cstat[:, 0, idx]

    eavg = np.zeros((int(nmesh), 4, 3), dtype=float)
    for k in range(3):
        for j in range(4):
            eavg[:, j, k] = edstat[:, j, k, idx] / cstat[:, 0, idx]

    temp = cavg[:, 4] - cavg[:, 1] ** 2
    temp = temp + cavg[:, 5] - cavg[:, 2] ** 2
    temp = temp + cavg[:, 6] - cavg[:, 3] ** 2

    tv = np.zeros(int(nmesh), dtype=float)
    if nmesh >= 2:
        tv[1:-1] = 0.5 * fluxfac2 * (temp[2:] + temp[:-2] - 2.0 * temp[1:-1])
        tv[0] = 0.5 * fluxfac2 * (temp[1] - 2.0 * temp[0])
        tv[-1] = tv[-2]

    temp_d = np.empty(int(nmesh), dtype=float)
    temp_d[0] = cavg[0, 7] - cavg[0, 1] ** 2
    temp_d[1:] = cavg[1:, 7] - (cavg[1:, 1] - cavg[:-1, 1]) ** 2
    temp_d[0] += cavg[0, 8] - cavg[0, 2] ** 2
    temp_d[1:] += cavg[1:, 8] - (cavg[1:, 2] - cavg[:-1, 2]) ** 2
    temp_d[0] += cavg[0, 9] - cavg[0, 3] ** 2
    temp_d[1:] += cavg[1:, 9] - (cavg[1:, 3] - cavg[:-1, 3]) ** 2
    d = fluxfac2 * temp_d

    p = np.zeros(int(nmesh), dtype=float)
    acc = np.empty(int(nmesh), dtype=float)
    acc[-1] = 0.5 * eavg[-1, 0, 0]
    for j in range(nmesh - 2, -1, -1):
        acc[j] = acc[j + 1] + 0.5 * (eavg[j, 0, 0] + eavg[j + 1, 0, 0])
    if nmesh >= 2:
        p[1:-1] = -0.5 * (cavg[2:, 1] - cavg[:-2, 1]) * acc[1:-1]
        p[0] = -0.5 * cavg[1, 1] * acc[0]
    for comp in (1, 2):
        acc[-1] = 0.5 * eavg[-1, 0, comp]
        for j in range(nmesh - 2, -1, -1):
            acc[j] = acc[j + 1] + 0.5 * (eavg[j, 0, comp] + eavg[j + 1, 0, comp])
        if nmesh >= 2:
            p[1:-1] -= 0.5 * (cavg[2:, comp + 1] - cavg[:-2, comp + 1]) * acc[1:-1]
            p[0] -= 0.5 * cavg[1, comp + 1] * acc[0]
    p[-1] = 0.0

    ta = 0.5 * eavg[:, 1, 0] - cavg[:, 1] * eavg[:, 0, 0] - p
    for comp in (1, 2):
        ta += 0.5 * eavg[:, 1, comp] - cavg[:, comp + 1] * eavg[:, 0, comp]

    d = -0.5 * eavg[:, 3, 0] + cavg[:, 1] * eavg[:, 2, 0] + tv
    for comp in (1, 2):
        d += -0.5 * eavg[:, 3, comp] + cavg[:, comp + 1] * eavg[:, 2, comp]

    ht = np.array([float(dom) * (j + 1) / float(nmesh) for j in range(int(nmesh))], dtype=float)
    mean_u = cavg[:, 1].copy()
    variances = np.vstack([
        cavg[:, 4] - cavg[:, 1] ** 2,
        cavg[:, 5] - cavg[:, 2] ** 2,
        cavg[:, 6] - cavg[:, 3] ** 2,
    ])
    adv_flux = np.empty(int(nmesh), dtype=float)
    adv_flux[-1] = width * eavg[-1, 0, 0]
    for j in range(nmesh - 2, -1, -1):
        adv_flux[j] = adv_flux[j + 1] + width * eavg[j, 0, 0]
    bal = ta + tv + p - d
    return SnapOutputs(
        ht=ht,
        mean_u=mean_u,
        variances=variances,
        advective_flux_u=adv_flux,
        shear_production=p,
        advective_transport=ta,
        viscous_transport=tv,
        dissipation=d,
        balance=bal,
        eddy_count_near_wall=edstat[: nmesh - 1, 0, 3, idx].copy(),
        eddy_count_far_wall=edstat[: nmesh - 1, 1, 3, idx].copy(),
    )



def write_snap_intercomparison(output_dir: str | Path, istat: int, snap: SnapOutputs) -> None:
    out = Path(output_dir)
    (out / f"A{istat}.dat").write_text(
        brecord_text(-len(snap.ht), snap.ht) + brecord_text(len(snap.ht), snap.mean_u),
        encoding="utf-8",
    )
    b_text = brecord_text(-len(snap.ht), snap.ht)
    for row in snap.variances:
        b_text += brecord_text(len(snap.ht), row)
    (out / f"B{istat}.dat").write_text(b_text, encoding="utf-8")
    c_text = brecord_text(-len(snap.ht), snap.ht) + brecord_text(len(snap.ht), snap.advective_flux_u)
    (out / f"C{istat}.dat").write_text(c_text, encoding="utf-8")
    d_text = brecord_text(-len(snap.ht), snap.ht)
    for row in (snap.shear_production, snap.advective_transport, snap.viscous_transport, snap.dissipation):
        d_text += brecord_text(len(snap.ht), row)
    (out / f"D{istat}.dat").write_text(d_text, encoding="utf-8")
    h_text = xrecord_text(1, np.array([0.0]), np.array([0.0])) + xrecord_text(len(snap.ht), snap.ht, snap.balance)
    (out / f"H{istat}.dat").write_text(h_text, encoding="utf-8")
    i_lines = [f"{j + 1} {snap.eddy_count_near_wall[j]} {snap.eddy_count_far_wall[j]}" for j in range(len(snap.eddy_count_near_wall))]
    (out / f"I{istat}.dat").write_text("\n".join(i_lines) + "\n", encoding="utf-8")



def write_snap_xmgrace(output_dir: str | Path, istat: int, snap: SnapOutputs) -> None:
    out = Path(output_dir)
    zero_x = np.array([0.0])
    zero_y = np.array([0.0])
    (out / f"A{istat}.dat").write_text(
        xrecord_text(1, zero_x, zero_y) + xrecord_text(len(snap.ht), snap.ht, snap.mean_u),
        encoding="utf-8",
    )
    b_text = xrecord_text(1, zero_x, zero_y)
    for row in snap.variances:
        b_text += xrecord_text(len(snap.ht), snap.ht, row)
    (out / f"B{istat}.dat").write_text(b_text, encoding="utf-8")
    c_text = xrecord_text(1, zero_x, zero_y) + xrecord_text(len(snap.ht), snap.ht, snap.advective_flux_u)
    (out / f"C{istat}.dat").write_text(c_text, encoding="utf-8")
    (out / f"D{istat}.dat").write_text(
        xrecord_text(1, zero_x, zero_y) + xrecord_text(len(snap.ht), snap.ht, snap.shear_production),
        encoding="utf-8",
    )
    (out / f"E{istat}.dat").write_text(
        xrecord_text(1, zero_x, zero_y) + xrecord_text(len(snap.ht), snap.ht, snap.advective_transport),
        encoding="utf-8",
    )
    (out / f"F{istat}.dat").write_text(
        xrecord_text(1, zero_x, np.array([snap.viscous_transport[-1]])) + xrecord_text(len(snap.ht), snap.ht, snap.viscous_transport),
        encoding="utf-8",
    )
    (out / f"G{istat}.dat").write_text(
        xrecord_text(1, zero_x, np.array([snap.dissipation[-1]])) + xrecord_text(len(snap.ht), snap.ht, snap.dissipation),
        encoding="utf-8",
    )
    (out / f"H{istat}.dat").write_text(
        xrecord_text(1, zero_x, zero_y) + xrecord_text(len(snap.ht), snap.ht, snap.balance),
        encoding="utf-8",
    )
    i_lines = [f"{j + 1} {snap.eddy_count_near_wall[j]} {snap.eddy_count_far_wall[j]}" for j in range(len(snap.eddy_count_near_wall))]
    (out / f"I{istat}.dat").write_text("\n".join(i_lines) + "\n", encoding="utf-8")
