#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from pyodt1.statistics import compute_snap_outputs, parse_snap_intercomparison, write_snap_intercomparison

ROOT = Path(__file__).resolve().parents[1]
ODT1_SRC = ROOT / "external" / "odt1" / "source1"


def max_abs_diff(a, b) -> float:
    arr_a = np.asarray(a, dtype=float)
    arr_b = np.asarray(b, dtype=float)
    return float(np.max(np.abs(arr_a - arr_b))) if arr_a.size else 0.0


def make_fixture() -> tuple[np.ndarray, np.ndarray]:
    n = 7
    cstat = np.ones((n, 10, 2), dtype=float)
    cstat[:, 0, 1] = 2.5
    cstat[:, 1, 1] = np.array([0.3, -0.1, 0.2, 0.6, 0.4, 0.1, -0.2]) * cstat[:, 0, 1]
    cstat[:, 2, 1] = np.array([0.0, 0.2, 0.1, -0.1, 0.3, 0.4, 0.2]) * cstat[:, 0, 1]
    cstat[:, 3, 1] = np.array([0.2, 0.1, -0.2, 0.0, 0.2, 0.5, 0.1]) * cstat[:, 0, 1]
    ubar = cstat[:, 1, 1] / cstat[:, 0, 1]
    vbar = cstat[:, 2, 1] / cstat[:, 0, 1]
    wbar = cstat[:, 3, 1] / cstat[:, 0, 1]
    cstat[:, 4, 1] = (ubar**2 + np.array([0.04, 0.02, 0.03, 0.01, 0.05, 0.02, 0.04])) * cstat[:, 0, 1]
    cstat[:, 5, 1] = (vbar**2 + np.array([0.03, 0.04, 0.02, 0.02, 0.01, 0.03, 0.02])) * cstat[:, 0, 1]
    cstat[:, 6, 1] = (wbar**2 + np.array([0.05, 0.01, 0.02, 0.03, 0.02, 0.01, 0.04])) * cstat[:, 0, 1]
    cstat[:, 7, 1] = np.array([0.07, 0.04, 0.06, 0.05, 0.03, 0.08, 0.04]) * cstat[:, 0, 1]
    cstat[:, 8, 1] = np.array([0.06, 0.05, 0.04, 0.03, 0.05, 0.04, 0.06]) * cstat[:, 0, 1]
    cstat[:, 9, 1] = np.array([0.05, 0.07, 0.03, 0.04, 0.06, 0.05, 0.03]) * cstat[:, 0, 1]
    edstat = np.zeros((n, 4, 4, 2), dtype=float)
    edstat[:, 0, 0, 1] = np.linspace(0.03, -0.01, n)
    edstat[:, 0, 1, 1] = np.linspace(0.01, 0.02, n)
    edstat[:, 0, 2, 1] = np.linspace(-0.02, 0.03, n)
    edstat[:, 1, 0, 1] = np.linspace(0.02, 0.05, n)
    edstat[:, 1, 1, 1] = np.linspace(0.03, -0.01, n)
    edstat[:, 1, 2, 1] = np.linspace(0.00, 0.04, n)
    edstat[:, 2, 0, 1] = np.linspace(0.01, 0.03, n)
    edstat[:, 2, 1, 1] = np.linspace(0.02, 0.01, n)
    edstat[:, 2, 2, 1] = np.linspace(0.04, 0.02, n)
    edstat[:, 3, 0, 1] = np.linspace(0.05, 0.02, n)
    edstat[:, 3, 1, 1] = np.linspace(0.01, 0.03, n)
    edstat[:, 3, 2, 1] = np.linspace(0.02, 0.05, n)
    edstat[0, 0, 3, 1] = 3.0
    edstat[1, 1, 3, 1] = 2.0
    edstat[2, 0, 3, 1] = 1.0
    edstat[3, 1, 3, 1] = 4.0
    return cstat, edstat


def write_driver(workdir: Path) -> None:
    (workdir / "driver.f90").write_text(
        """
      program driver_intercomparison
      implicit none
      integer, parameter :: N2=7, MVAL=10, NSTATVAL=2
      integer j,k,m,is,io(100)
      double precision cstat(N2,10,NSTATVAL), ed2(N2,4,4,NSTATVAL), u2(N2), v2(N2), w2(N2), dom, visc
      open(10,file='fixture.dat',status='old')
      do is=1,NSTATVAL
         do j=1,N2
            do k=1,10
               read(10,*) cstat(j,k,is)
            enddo
         enddo
      enddo
      do is=1,NSTATVAL
         do j=1,N2
            do k=1,4
               do m=1,4
                  read(10,*) ed2(j,k,m,is)
               enddo
            enddo
         enddo
      enddo
      close(10)
      io = 0
      io(1) = 0
      open(45,file='A2.dat',status='unknown')
      open(46,file='B2.dat',status='unknown')
      open(47,file='C2.dat',status='unknown')
      open(48,file='D2.dat',status='unknown')
      open(82,file='H2.dat',status='unknown')
      open(92,file='I2.dat',status='unknown')
      u2 = 0.d0
      v2 = 0.d0
      w2 = 0.d0
      dom = 1.5d0
      visc = 2.5d-5
      call BSnap(N2,u2,v2,w2,dom,visc,2,ed2,cstat,io,N2,MVAL,NSTATVAL)
      end
        """.strip()
        + "\n",
        encoding="utf-8",
    )


def compile_and_run(workdir: Path) -> None:
    exe = workdir / "snap.exe"
    cmd = [
        shutil.which("gfortran") or "gfortran",
        "-O0",
        "-std=legacy",
        "-o",
        str(exe),
        str(ODT1_SRC / "BRecord.f"),
        str(ODT1_SRC / "XRecord.f"),
        str(ODT1_SRC / "BSnap.f"),
        str(workdir / "driver.f90"),
    ]
    subprocess.run(cmd, check=True, cwd=workdir)
    subprocess.run([str(exe)], check=True, cwd=workdir)


def main() -> int:
    cstat, edstat = make_fixture()
    snap = compute_snap_outputs(7, np.zeros(7), np.zeros(7), np.zeros(7), 1.5, 2.5e-5, 2, edstat, cstat)
    with tempfile.TemporaryDirectory(prefix="pyodt1-bsnap-inter-") as tmp:
        workdir = Path(tmp)
        py_dir = workdir / "py"
        py_dir.mkdir()
        write_snap_intercomparison(py_dir, 2, snap)
        py_records = parse_snap_intercomparison(py_dir, 2).records

        lines = [str(float(cstat[j, k, is_])) for is_ in range(cstat.shape[2]) for j in range(7) for k in range(10)]
        lines.extend(str(float(edstat[j, k, m, is_])) for is_ in range(edstat.shape[3]) for j in range(7) for k in range(4) for m in range(4))
        (workdir / "fixture.dat").write_text("\n".join(lines) + "\n", encoding="utf-8")
        write_driver(workdir)
        compile_and_run(workdir)
        ft_records = parse_snap_intercomparison(workdir, 2).records

        print("# Patched BSnap intercomparison comparison")
        for key in ["ht", "mean_u", "variances", "advective_flux_u", "budget_terms", "balance_xy", "eddy_counts"]:
            print(f"{key}: max_abs_diff={max_abs_diff(py_records[key], ft_records[key]):.6e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
