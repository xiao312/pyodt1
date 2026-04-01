#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from pyodt1.config import read_config, read_options, read_pars
from pyodt1.legacy import b_add_term, b_init_stats, brng_get, brng_put
from pyodt1.rng import OdtRNG

ROOT = Path(__file__).resolve().parents[1]
ODT1_SRC = ROOT / "external" / "odt1" / "source1"


def max_abs_diff(a, b) -> float:
    arr_a = np.asarray(a, dtype=float)
    arr_b = np.asarray(b, dtype=float)
    return float(np.max(np.abs(arr_a - arr_b))) if arr_a.size else 0.0


def write_fixture_files(workdir: Path) -> None:
    (workdir / "BOptions.dat").write_text("2\n1\n7\n", encoding="utf-8")
    (workdir / "BPars.dat").write_text(
        "6\n18\n2\n2\n4\n8\n1\n6\n0.4\n0.2\n1.5\n0.5\n2.0e-4\n-1.0\n",
        encoding="utf-8",
    )
    (workdir / "BConfig.dat").write_text(
        "2\n2\n3\n6.0e-4\n1.0\n1.0e-5\n0.0\n1.0\n0.0\n",
        encoding="utf-8",
    )


def python_reference(workdir: Path) -> dict:
    ioptions, nopt = read_options(workdir / "BOptions.dat")
    ipars, rpars, nipars, nrpars = read_pars(workdir / "BPars.dat")
    cfg = read_config(workdir / "BConfig.dat", int(ipars[0]))

    stats = b_init_stats(nmesh=5, nstat=2, mval=10, max_points=10)
    term = np.array([1.0, -2.0, 3.0, -4.0, 5.0])
    b_add_term(3, 5, stats.time_statistics.cstat, term, 2)

    rng = OdtRNG(seed_index=1)
    state0 = brng_get(rng)
    rng.uniform()
    brng_put(rng, *state0)
    state1 = brng_get(rng)

    return {
        "options": ioptions,
        "nopt": nopt,
        "ipars": ipars,
        "rpars": rpars,
        "nipars": nipars,
        "nrpars": nrpars,
        "config": cfg,
        "cstat_term": stats.time_statistics.cstat[:5, 2, 1].copy(),
        "cstat_zero": stats.time_statistics.cstat[:5, :, 0].copy(),
        "edstat_zero": stats.eddy_statistics.edstat[:5, :2, :, :2].copy(),
        "series_zero": stats.series.sums[:, :10].copy(),
        "rng_before": state0,
        "rng_after_put": state1,
    }


def write_driver(workdir: Path) -> None:
    (workdir / "driver.f90").write_text(
        """
      program driver_helpers
      implicit none
      integer, parameter :: N=5, NVAL=5, MVAL=10, NSTATVAL=2
      integer i, j, k, nopt, nipars, nrpars
      integer ioptions(100), ipars(100)
      double precision rpars(100)
      integer niter, nstat, ntseg
      double precision tend, dom, visc, pgrad, ratefac, viscpen
      double precision cstat(NVAL,MVAL,NSTATVAL), edstat(NVAL,2,4,NSTATVAL), umoms(2,10000)
      double precision term(N)
      integer ig1, ig2

      call BReadOptions(ioptions,nopt)
      call BReadPars(ipars,rpars,nipars,nrpars)
      call BReadConfig(niter,nstat,ntseg,tend,dom,visc,pgrad,ratefac,viscpen,ipars(1))
      call BInitStats(N,NVAL,MVAL,NSTATVAL,edstat,cstat,umoms)
      term(1)=1.d0
      term(2)=-2.d0
      term(3)=3.d0
      term(4)=-4.d0
      term(5)=5.d0
      call BAddTerm(3,N,cstat,term,NVAL,MVAL,NSTATVAL,2)
      call BSeeds(ipars,ig1,ig2)
      call BrngPut(ig1,ig2)
      call BrngGet(ig1,ig2)

      open(20,file='helpers.out',status='unknown')
      write(20,*) nopt
      write(20,*) (ioptions(i), i=1,100)
      write(20,*) nipars, nrpars
      write(20,*) (ipars(i), i=1,100)
      write(20,*) (rpars(i), i=1,100)
      write(20,*) niter, nstat, ntseg, tend, dom, visc, pgrad, ratefac, viscpen
      do j=1,N
         write(20,*) (cstat(j,k,2), k=1,MVAL)
      enddo
      do j=1,N
         do i=1,2
            write(20,*) (edstat(j,i,k,1), k=1,4)
            write(20,*) (edstat(j,i,k,2), k=1,4)
         enddo
      enddo
      write(20,*) (umoms(1,k), k=1,10)
      write(20,*) (umoms(2,k), k=1,10)
      write(20,*) ig1, ig2
      close(20)
      end
        """.strip()
        + "\n",
        encoding="utf-8",
    )


def compile_and_run(workdir: Path) -> None:
    exe = workdir / "helpers.exe"
    cmd = [
        shutil.which("gfortran") or "gfortran",
        "-O0",
        "-std=legacy",
        "-o",
        str(exe),
        str(ODT1_SRC / "BReadOptions.f"),
        str(ODT1_SRC / "BReadPars.f"),
        str(ODT1_SRC / "BReadConfig.f"),
        str(ODT1_SRC / "BInitStats.f"),
        str(ODT1_SRC / "BAddTerm.f"),
        str(ODT1_SRC / "BSeeds.f"),
        str(ODT1_SRC / "Brng.f"),
        str(ODT1_SRC / "BrngGet.f"),
        str(ODT1_SRC / "BrngPut.f"),
        str(workdir / "driver.f90"),
    ]
    subprocess.run(cmd, check=True, cwd=workdir)
    subprocess.run([str(exe)], check=True, cwd=workdir)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="pyodt1-helpers-") as tmpdir:
        workdir = Path(tmpdir)
        write_fixture_files(workdir)
        py = python_reference(workdir)
        write_driver(workdir)
        compile_and_run(workdir)

        lines = (workdir / "helpers.out").read_text(encoding="utf-8").splitlines()
        pos = 0
        ft_nopt = int(lines[pos].split()[0]); pos += 1
        ft_ioptions = np.asarray([int(x) for x in lines[pos].split()], dtype=int); pos += 1
        tmp = lines[pos].split(); ft_nipars = int(tmp[0]); ft_nrpars = int(tmp[1]); pos += 1
        ft_ipars = np.asarray([int(x) for x in lines[pos].split()], dtype=int); pos += 1
        ft_rpars = np.asarray([float(x) for x in lines[pos].split()], dtype=float); pos += 1
        cfg = [float(x) for x in lines[pos].split()]; pos += 1
        ft_cstat = np.asarray([[float(x) for x in lines[pos + j].split()] for j in range(5)], dtype=float); pos += 5
        ft_ed = []
        for _j in range(5):
            cell = []
            for _i in range(2):
                cell.append([float(x) for x in lines[pos].split()]); pos += 1
                cell.append([float(x) for x in lines[pos].split()]); pos += 1
            ft_ed.append(cell)
        ft_ed = np.asarray(ft_ed, dtype=float).reshape(5, 2, 2, 4).transpose(0,1,3,2)
        ft_um1 = np.asarray([float(x) for x in lines[pos].split()], dtype=float); pos += 1
        ft_um2 = np.asarray([float(x) for x in lines[pos].split()], dtype=float); pos += 1
        rng_vals = tuple(int(x) for x in lines[pos].split())

        print("# Legacy helper comparison")
        print(f"BReadOptions.nopt_equal={py['nopt'] == ft_nopt}")
        print(f"BReadOptions.ioptions_max_abs_diff={max_abs_diff(py['options'], ft_ioptions):.6e}")
        print(f"BReadPars.counts_equal={(py['nipars'] == ft_nipars) and (py['nrpars'] == ft_nrpars)}")
        print(f"BReadPars.ipars_max_abs_diff={max_abs_diff(py['ipars'], ft_ipars):.6e}")
        print(f"BReadPars.rpars_max_abs_diff={max_abs_diff(py['rpars'], ft_rpars):.6e}")
        print(f"BReadConfig.max_abs_diff={max_abs_diff(py['config'], cfg):.6e}")
        print(f"BAddTerm.cstat_max_abs_diff={max_abs_diff(py['cstat_term'], ft_cstat[:,2]):.6e}")
        print(f"BInitStats.cstat_zero_max_abs_diff={max_abs_diff(py['cstat_zero'], ft_cstat[:, :10]*0.0):.6e}")
        print(f"BInitStats.edstat_zero_max_abs_diff={max_abs_diff(py['edstat_zero'], ft_ed):.6e}")
        print(f"BInitStats.umoms_zero_max_abs_diff={max_abs_diff(py['series_zero'], np.vstack([ft_um1, ft_um2])):.6e}")
        print(f"BrngGetPut.state_equal={py['rng_after_put'] == rng_vals}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
