from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np


@dataclass(slots=True)
class OdtConfig:
    niter: int
    nstat: int
    ntseg: int
    tend: float
    dom: float
    visc: float
    pgrad: float
    ratefac: float
    viscpen: float
    nmesh: int
    ioptions: np.ndarray
    ipars: np.ndarray
    rpars: np.ndarray
    nopt: int
    nipars: int
    nrpars: int


@dataclass(slots=True)
class EddySizeDistribution:
    io: int
    ip: int
    iv: int
    co: float
    cv: float
    pl: np.ndarray


@dataclass(slots=True)
class EddySample:
    m: int
    l: int
    l3: int
    acceptance_probability: float
    u_kernel: float
    v_kernel: float
    w_kernel: float


def _read_scalar_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]


def read_options(path: str | Path) -> tuple[np.ndarray, int]:
    lines = _read_scalar_lines(Path(path))
    nopt = int(lines[0])
    arr = np.zeros(100, dtype=int)
    for idx in range(min(nopt, 100)):
        arr[idx] = int(lines[idx + 1])
    return arr, nopt


def read_pars(path: str | Path) -> tuple[np.ndarray, np.ndarray, int, int]:
    lines = _read_scalar_lines(Path(path))
    nipars = int(lines[0])
    ipars = np.zeros(100, dtype=int)
    ipars[2] = 2
    ipars[3] = 3
    ipars[5] = 1
    pos = 1
    for idx in range(min(nipars, 100)):
        ipars[idx] = int(lines[pos])
        pos += 1
    nrpars = int(lines[pos])
    pos += 1
    rpars = np.zeros(100, dtype=float)
    rpars[4] = 0.5
    rpars[5] = -1.0
    for idx in range(min(nrpars, 100)):
        rpars[idx] = float(lines[pos])
        pos += 1
    return ipars, rpars, nipars, nrpars


def read_config(path: str | Path, nmesh: int) -> tuple[int, int, int, float, float, float, float, float, float]:
    lines = _read_scalar_lines(Path(path))
    niter = int(lines[0])
    nstat = int(lines[1])
    ntseg = int(lines[2])
    tend = float(lines[3])
    dom = float(lines[4])
    visc = float(lines[5])
    pgrad = float(lines[6])
    c_param = float(lines[7])
    z_param = float(lines[8])
    ratefac = 3.0 * c_param * float(nmesh) / dom
    viscpen = z_param * (visc * float(nmesh) / dom) ** 2
    return niter, nstat, ntseg, tend, dom, visc, pgrad, ratefac, viscpen


def load_legacy_case(directory: str | Path) -> OdtConfig:
    directory = Path(directory)
    ipars, rpars, nipars, nrpars = read_pars(directory / "BPars.dat")
    nmesh = int(ipars[0])
    if nipars < 5:
        ipars[4] = nmesh
    ioptions, nopt = read_options(directory / "BOptions.dat")
    niter, nstat, ntseg, tend, dom, visc, pgrad, ratefac, viscpen = read_config(directory / "BConfig.dat", nmesh)
    return OdtConfig(
        niter=niter,
        nstat=nstat,
        ntseg=ntseg,
        tend=tend,
        dom=dom,
        visc=visc,
        pgrad=pgrad,
        ratefac=ratefac,
        viscpen=viscpen,
        nmesh=nmesh,
        ioptions=ioptions,
        ipars=ipars,
        rpars=rpars,
        nopt=nopt,
        nipars=nipars,
        nrpars=nrpars,
    )
