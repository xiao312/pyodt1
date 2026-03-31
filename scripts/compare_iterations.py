#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from pyodt1.advance import generate_initial_state
from pyodt1.config import OdtConfig
from pyodt1.rng import OdtRNG
from pyodt1.solver import OdtSolver


ROOT = Path(__file__).resolve().parents[1]
ODT1_SRC = ROOT / "external" / "odt1" / "source1"


def make_config() -> OdtConfig:
    nmesh = 12
    ioptions = np.zeros(100, dtype=int)
    ioptions[0] = 0
    ipars = np.zeros(100, dtype=int)
    ipars[0] = nmesh
    ipars[1] = 2
    ipars[2] = 2
    ipars[3] = 3
    ipars[4] = nmesh
    ipars[5] = 1
    rpars = np.zeros(100, dtype=float)
    rpars[0] = 0.4
    rpars[1] = 0.2
    rpars[2] = 1.5
    rpars[3] = 0.5
    rpars[4] = 0.5
    rpars[5] = 2.0e-4
    return OdtConfig(
        niter=2,
        nstat=2,
        ntseg=3,
        tend=2.0e-3,
        dom=1.0,
        visc=1.0e-5,
        pgrad=0.25,
        ratefac=3.0,
        viscpen=0.0,
        nmesh=nmesh,
        ioptions=ioptions,
        ipars=ipars,
        rpars=rpars,
        nopt=1,
        nipars=6,
        nrpars=6,
    )


def parse_t_dat(text: str) -> tuple[int, list[float], list[float]]:
    vals = text.split()
    itime = int(vals[0])
    floats = [float(x) for x in vals[1:]]
    time = floats[:itime]
    var = floats[itime : 2 * itime]
    return itime, time, var


def python_reference() -> dict:
    cfg = make_config()
    rng = OdtRNG(seed_index=1)
    init_state = generate_initial_state(cfg.nmesh, cfg.dom, rng)
    solver = OdtSolver(cfg, init_state, rng)
    result = solver.run_iterations(niter=cfg.niter, max_trials=5, collect_stats=True)
    series_text = solver.write_series_output(result)
    itime, time, var = parse_t_dat(series_text)
    return {
        "python": {
            "itime": itime,
            "time": time,
            "variance": var,
            "series": result.series[:, :itime].tolist(),
            "cstat": None if result.cstat is None else result.cstat.tolist(),
            "i1": result.final_rng_state[0],
            "i2": result.final_rng_state[1],
        },
        "fixtures": {
            "config": {
                "niter": cfg.niter,
                "nstat": cfg.nstat,
                "ntseg": cfg.ntseg,
                "tend": cfg.tend,
                "dom": cfg.dom,
                "visc": cfg.visc,
                "pgrad": cfg.pgrad,
                "ratefac": cfg.ratefac,
                "viscpen": cfg.viscpen,
                "nipars": cfg.nipars,
                "nrpars": cfg.nrpars,
                "ipars": cfg.ipars.tolist(),
                "rpars": cfg.rpars.tolist(),
                "ioptions": cfg.ioptions.tolist(),
                "max_trials": 5,
            }
        },
    }


def write_driver(workdir: Path) -> None:
    (workdir / "driver_iterations.f90").write_text(
        """
      program driver_iterations
      implicit none
      integer, parameter :: N=12, NVAL=12, MVAL=10, NSTATVAL=4
      integer iter, istat, itseg, itime, ii, Np, niter, nstat, ntseg, max_trials
      integer M, L, Io, Ip, i1, i2, j
      double precision tend, dom, visc, pgrad, ratefac, viscpen
      double precision dt, td, t, to, tmark, delt, pp, pa, rannum, Co, Cv
      double precision BExp, u(N), v(N), w(N), PL(N)
      double precision cstat(NVAL,MVAL,NSTATVAL), umoms(2,10000), edstat(NVAL,2,4,NSTATVAL)
      double precision uK, vK, wK
      integer ipars(100), nipars, nrpars, ioptions(100)
      double precision rpars(100)
      open(10,file='fixture_iterations.dat',status='old')
      read(10,*) niter, nstat, ntseg, max_trials
      read(10,*) tend, dom, visc, pgrad, ratefac, viscpen, nipars, nrpars
      do j=1,100
         read(10,*) ipars(j)
      enddo
      do j=1,100
         read(10,*) rpars(j)
      enddo
      do j=1,100
         read(10,*) ioptions(j)
      enddo
      close(10)
      open(40,file='T.dat',status='unknown')
      call BSeeds(ipars,i1,i2)
      call BInitRun(N,i1,i2,dom)
      call BInitStats(N,NVAL,MVAL,NSTATVAL,edstat,cstat,umoms)
      call BLenProb(N,Io,Ip,PL,Co,Cv,ipars,nipars)
      do iter=1,niter
         call BInitIter(N,u,v,w,itime,ii,Np,pa,tmark,t,to,dt,td,nrpars,rpars,dom,visc,i1,i2)
         do istat=1,nstat
            do itseg=1,ntseg
               tmark=tmark+tend/dfloat(nstat*ntseg)
               itime=itime+1
               do while (t .le. tmark .and. ii .lt. max_trials)
                  if ((t-to) .ge. td) then
                     delt=t-to
                     call BEqnStep(N,u,v,w,delt,dom,visc,pgrad,rpars,istat,cstat,NVAL,MVAL,NSTATVAL)
                     to=t
                  endif
                  call BSampleEddy(N,M,L,u,v,w,dt,td,PL,ratefac,viscpen,uK,vK,wK,pp,ii,pa,Np,rpars,Io,Ip,Cv,Co,i1,i2)
                  call Brng(rannum,i1,i2)
                  if (rannum .lt. pp) then
                     call BEddy(N,M,L,u,v,w,uK,vK,wK)
                     delt=t-to
                     call BEqnStep(N,u,v,w,delt,dom,visc,pgrad,rpars,istat,cstat,NVAL,MVAL,NSTATVAL)
                     to=t
                  endif
                  t=t+BExp(dt,i1,i2)
                  call BRaisedt(Np,dt,td,pa,ii,ipars,rpars)
               enddo
               delt=tmark-to
               if (delt .gt. 0.d0) then
                  call BEqnStep(N,u,v,w,delt,dom,visc,pgrad,rpars,istat,cstat,NVAL,MVAL,NSTATVAL)
                  to=tmark
               endif
               call BSeries(NVAL,N,itime,u,umoms)
            enddo
         enddo
      enddo
      call BWriteSeries(niter,itime,tend,ntseg,umoms,ioptions)
      open(20,file='iterations_out.json',status='unknown')
      write(20,'(A)') '{'
      write(20,'(A,I0,A)') '  "itime": ', itime, ','
      write(20,'(A)') '  "series_u": ['
      do j=1,itime
         if (j.lt.itime) then
            write(20,'(ES24.16,A)') umoms(1,j),','
         else
            write(20,'(ES24.16)') umoms(1,j)
         endif
      enddo
      write(20,'(A)') '  ],'
      write(20,'(A)') '  "series_u2": ['
      do j=1,itime
         if (j.lt.itime) then
            write(20,'(ES24.16,A)') umoms(2,j),','
         else
            write(20,'(ES24.16)') umoms(2,j)
         endif
      enddo
      write(20,'(A)') '  ],'
      write(20,'(A)') '  "cstat": ['
      do istat=1,nstat
         write(20,'(A)') '    ['
         do j=1,N
            write(20,'(A)') '      ['
            do M=1,MVAL
               if (M.lt.MVAL) then
                  write(20,'(ES24.16,A)') cstat(j,M,istat),','
               else
                  write(20,'(ES24.16)') cstat(j,M,istat)
               endif
            enddo
            if (j.lt.N) then
               write(20,'(A)') '      ],'
            else
               write(20,'(A)') '      ]'
            endif
         enddo
         if (istat.lt.nstat) then
            write(20,'(A)') '    ],'
         else
            write(20,'(A)') '    ]'
         endif
      enddo
      write(20,'(A)') '  ],'
      write(20,'(A,I0,A)') '  "i1": ', i1, ','
      write(20,'(A,I0)') '  "i2": ', i2
      write(20,'(A)') '}'
      close(20)
      close(40)
      end
        """.strip()
        + "\n",
        encoding="utf-8",
    )


def write_fixture(workdir: Path, ref: dict) -> None:
    cfg = ref["fixtures"]["config"]
    lines = [
        f"{cfg['niter']} {cfg['nstat']} {cfg['ntseg']} {cfg['max_trials']}",
        f"{cfg['tend']} {cfg['dom']} {cfg['visc']} {cfg['pgrad']} {cfg['ratefac']} {cfg['viscpen']} {cfg['nipars']} {cfg['nrpars']}",
    ]
    lines.extend(str(x) for x in cfg["ipars"])
    lines.extend(str(x) for x in cfg["rpars"])
    lines.extend(str(x) for x in cfg["ioptions"])
    (workdir / "fixture_iterations.dat").write_text("\n".join(lines) + "\n", encoding="utf-8")


def compile_and_run(workdir: Path) -> tuple[dict, str]:
    gfortran = shutil.which("gfortran")
    if not gfortran:
        raise RuntimeError("gfortran not found on PATH")
    exe = workdir / "iterations.exe"
    sources = [
        ODT1_SRC / "BAddTerm.f",
        ODT1_SRC / "BStats.f",
        ODT1_SRC / "Brng.f",
        ODT1_SRC / "BSeeds.f",
        ODT1_SRC / "BExp.f",
        ODT1_SRC / "BAdv.f",
        ODT1_SRC / "BEqnStep.f",
        ODT1_SRC / "BTriplet.f",
        ODT1_SRC / "BAddK.f",
        ODT1_SRC / "BsKd.f",
        ODT1_SRC / "BProb.f",
        ODT1_SRC / "BEddy.f",
        ODT1_SRC / "BLowerdt.f",
        ODT1_SRC / "BRaisedt.f",
        ODT1_SRC / "BLenProb.f",
        ODT1_SRC / "BLength.f",
        ODT1_SRC / "BSampleEddy.f",
        ODT1_SRC / "BSeries.f",
        ODT1_SRC / "BWriteSeries.f",
        ODT1_SRC / "BInitRun.f",
        ODT1_SRC / "BInitIter.f",
        ODT1_SRC / "BInitStats.f",
        workdir / "driver_iterations.f90",
    ]
    cmd = [gfortran, "-O0", "-std=legacy", "-o", str(exe)] + [str(s) for s in sources]
    subprocess.run(cmd, check=True, cwd=workdir)
    subprocess.run([str(exe)], check=True, cwd=workdir)
    out = json.loads((workdir / "iterations_out.json").read_text(encoding="utf-8"))
    tdat = (workdir / "T.dat").read_text(encoding="utf-8")
    return out, tdat


def max_abs_diff(a: list[float] | list[list] | list[list[list]], b: list[float] | list[list] | list[list[list]]) -> float:
    return float(np.max(np.abs(np.asarray(a, dtype=float) - np.asarray(b, dtype=float))))


def main() -> int:
    ref = python_reference()
    with tempfile.TemporaryDirectory(prefix="pyodt1-iter-") as tmp:
        workdir = Path(tmp)
        write_driver(workdir)
        write_fixture(workdir, ref)
        fortran, tdat = compile_and_run(workdir)

    py = ref["python"]
    f_itime, f_time, f_var = parse_t_dat(tdat)
    py_series_u = py["series"][0]
    py_series_u2 = py["series"][1]

    print("# Python reference")
    print(json.dumps(py, indent=2))
    print("\n# Fortran result")
    print(json.dumps(fortran, indent=2))
    print("\n# BWriteSeries parsed output")
    print(json.dumps({"itime": f_itime, "time": f_time, "variance": f_var}, indent=2))

    print("\n# Differences")
    print(f"itime diff={py['itime'] - fortran['itime']}")
    print(f"series_u: max_abs_diff={max_abs_diff(py_series_u, fortran['series_u']):.6e}")
    print(f"series_u2: max_abs_diff={max_abs_diff(py_series_u2, fortran['series_u2']):.6e}")
    fortran_cstat = np.transpose(np.asarray(fortran['cstat'], dtype=float), (1, 2, 0))
    print(f"cstat: max_abs_diff={max_abs_diff(py['cstat'], fortran_cstat.tolist()):.6e}")
    print(f"i1 diff={py['i1'] - fortran['i1']}")
    print(f"i2 diff={py['i2'] - fortran['i2']}")
    print(f"BWriteSeries.itime diff={py['itime'] - f_itime}")
    print(f"BWriteSeries.time: max_abs_diff={max_abs_diff(py['time'], f_time):.6e}")
    print(f"BWriteSeries.variance: max_abs_diff={max_abs_diff(py['variance'], f_var):.6e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
