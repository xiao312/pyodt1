#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from pyodt1.advance import generate_initial_state
from pyodt1.config import EddySample, OdtConfig
from pyodt1.rng import OdtRNG
from pyodt1.solver import OdtSolver
from pyodt1.state import OdtState


ROOT = Path(__file__).resolve().parents[1]
ODT1_SRC = ROOT / "external" / "odt1" / "source1"


def make_config() -> OdtConfig:
    nmesh = 12
    ioptions = np.zeros(100, dtype=int)
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
        niter=1,
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
        nopt=0,
        nipars=6,
        nrpars=6,
    )


def python_reference() -> dict:
    cfg = make_config()

    lower_rng = OdtRNG(seed_index=1)
    lower_state = OdtState(np.zeros(cfg.nmesh), np.zeros(cfg.nmesh), np.zeros(cfg.nmesh))
    lower_solver = OdtSolver(cfg, lower_state, lower_rng)
    lower_solver.pa = 0.1
    lower_solver.np_nonzero = 1
    sample = EddySample(m=1, l=6, l3=2, acceptance_probability=0.8, u_kernel=0.0, v_kernel=0.0, w_kernel=0.0)
    lowered_sample, lower_dt, lower_td = lower_solver.lower_dt(0.1, 0.05, sample)

    run_rng = OdtRNG(seed_index=1)
    init_state = generate_initial_state(cfg.nmesh, cfg.dom, run_rng)
    solver = OdtSolver(cfg, init_state.copy(), run_rng)
    result = solver.run_scheduled_realization(max_trials=30)
    run_i1, run_i2 = run_rng.get_state()

    return {
        "python": {
            "blowerdt": {
                "dt": lower_dt,
                "td": lower_td,
                "pp": lowered_sample.acceptance_probability,
                "pa": lower_solver.pa,
                "np": lower_solver.np_nonzero,
            },
            "scheduled": {
                "trial_count": result.trial_count,
                "accepted_count": result.accepted_count,
                "rejected_count": result.rejected_count,
                "dt": result.dt,
                "td": result.td,
                "scheduled_time": result.scheduled_time,
                "physical_time": result.physical_time,
                "itime": result.itime,
                "u": result.state.u.tolist(),
                "v": result.state.v.tolist(),
                "w": result.state.w.tolist(),
                "centerline_u_sum": result.centerline_u_sum,
                "centerline_u2_sum": result.centerline_u2_sum,
                "i1": run_i1,
                "i2": run_i2,
            },
        },
        "fixtures": {
            "config": {
                "nmesh": cfg.nmesh,
                "nstat": cfg.nstat,
                "ntseg": cfg.ntseg,
                "tend": cfg.tend,
                "dom": cfg.dom,
                "visc": cfg.visc,
                "pgrad": cfg.pgrad,
                "ratefac": cfg.ratefac,
                "viscpen": cfg.viscpen,
                "ipars": cfg.ipars.tolist(),
                "rpars": cfg.rpars.tolist(),
                "nipars": cfg.nipars,
                "nrpars": cfg.nrpars,
                "max_trials": 30,
            },
            "blowerdt": {
                "dt": 0.1,
                "td": 0.05,
                "pp": 0.8,
                "pa": 0.1,
                "np": 1,
            },
        },
    }


def write_driver_files(workdir: Path) -> None:
    (workdir / "bstats_stub.f90").write_text(
        """
      subroutine BStats(N,u,v,w,dom,visc,cstat,et,NVAL,mVAL,nstatVAL,istat)
      implicit none
      integer N, NVAL, mVAL, nstatVAL, istat
      double precision u(N), v(N), w(N), dom, visc, et
      double precision cstat(NVAL,mVAL,nstatVAL)
      return
      end
        """.strip()
        + "\n",
        encoding="utf-8",
    )
    (workdir / "driver_blowerdt.f90").write_text(
        """
      program driver_blowerdt
      implicit none
      integer Np, j
      double precision dt, td, pp, pa, rpars(100)
      open(10,file='fixture_blowerdt.dat',status='old')
      read(10,*) dt, td, pp, pa, Np
      do j=1,100
         read(10,*) rpars(j)
      enddo
      close(10)
      call BLowerdt(dt,td,pp,pa,Np,rpars)
      open(20,file='out_blowerdt.json',status='unknown')
      write(20,'(A)') '{'
      write(20,'(A,ES24.16,A)') '  "dt": ', dt, ','
      write(20,'(A,ES24.16,A)') '  "td": ', td, ','
      write(20,'(A,ES24.16,A)') '  "pp": ', pp, ','
      write(20,'(A,ES24.16,A)') '  "pa": ', pa, ','
      write(20,'(A,I0)') '  "np": ', Np
      write(20,'(A)') '}'
      close(20)
      end
        """.strip()
        + "\n",
        encoding="utf-8",
    )
    (workdir / "driver_scheduled.f90").write_text(
        """
      program driver_scheduled
      implicit none
      integer, parameter :: N=12
      integer j, ii, Np, itime, istat, itseg, nstat, ntseg, max_trials
      integer M, L, Io, Ip, i1, i2, accepted_count, ictr
      double precision tend, dom, visc, pgrad, ratefac, viscpen
      double precision dt, td, t, to, tmark, delt, pp, pa, rannum, Co, Cv
      double precision BExp
      double precision u(N), v(N), w(N), old(12,3), PL(N), umoms(2,10000)
      integer ipars(100), nipars, nrpars
      double precision rpars(100)
      double precision cstat(12,10,4)
      double precision uK, vK, wK
      open(10,file='fixture_scheduled.dat',status='old')
      read(10,*) nstat, ntseg, max_trials
      read(10,*) tend, dom, visc, pgrad, ratefac, viscpen, nipars, nrpars
      do j=1,100
         read(10,*) ipars(j)
      enddo
      do j=1,100
         read(10,*) rpars(j)
      enddo
      close(10)
      call BSeeds(ipars,i1,i2)
      call BInitRun(N,i1,i2,dom)
      call BLenProb(N,Io,Ip,PL,Co,Cv,ipars,nipars)
      call BInitIter(N,u,v,w,itime,ii,Np,pa,tmark,t,to,dt,td,nrpars,rpars,dom,visc,i1,i2)
      accepted_count = 0
      umoms = 0.d0
      cstat = 0.d0
      do istat=1,nstat
         do itseg=1,ntseg
            tmark=tmark+tend/dfloat(nstat*ntseg)
            itime=itime+1
            do while (t .le. tmark .and. ii .lt. max_trials)
               if ((t-to) .ge. td) then
                  delt=t-to
                  call BEqnStep(N,u,v,w,delt,dom,visc,pgrad,rpars,1,cstat,12,10,4)
                  to=t
               endif
               call BSampleEddy(N,M,L,u,v,w,dt,td,PL,ratefac,viscpen,uK,vK,wK,pp,ii,pa,Np,rpars,Io,Ip,Cv,Co,i1,i2)
               call Brng(rannum,i1,i2)
               if (rannum .lt. pp) then
                  call BEddy(N,M,L,u,v,w,uK,vK,wK)
                  accepted_count = accepted_count + 1
                  delt=t-to
                  call BEqnStep(N,u,v,w,delt,dom,visc,pgrad,rpars,1,cstat,12,10,4)
                  to=t
               endif
               t=t+BExp(dt,i1,i2)
               call BRaisedt(Np,dt,td,pa,ii,ipars,rpars)
            enddo
            delt=tmark-to
            if (delt .gt. 0.d0) then
               call BEqnStep(N,u,v,w,delt,dom,visc,pgrad,rpars,1,cstat,12,10,4)
               to=tmark
            endif
            call BSeries(12,N,itime,u,umoms)
         enddo
      enddo
      open(20,file='out_scheduled.json',status='unknown')
      write(20,'(A)') '{'
      write(20,'(A,I0,A)') '  "trial_count": ', ii, ','
      write(20,'(A,I0,A)') '  "accepted_count": ', accepted_count, ','
      write(20,'(A,I0,A)') '  "rejected_count": ', ii-accepted_count, ','
      write(20,'(A,ES24.16,A)') '  "dt": ', dt, ','
      write(20,'(A,ES24.16,A)') '  "td": ', td, ','
      write(20,'(A,ES24.16,A)') '  "scheduled_time": ', t, ','
      write(20,'(A,ES24.16,A)') '  "physical_time": ', to, ','
      write(20,'(A,I0,A)') '  "itime": ', itime, ','
      write(20,'(A)') '  "u": ['
      do j=1,N
         if (j.lt.N) then
            write(20,'(ES24.16,A)') u(j),','
         else
            write(20,'(ES24.16)') u(j)
         endif
      enddo
      write(20,'(A)') '  ],'
      write(20,'(A)') '  "v": ['
      do j=1,N
         if (j.lt.N) then
            write(20,'(ES24.16,A)') v(j),','
         else
            write(20,'(ES24.16)') v(j)
         endif
      enddo
      write(20,'(A)') '  ],'
      write(20,'(A)') '  "w": ['
      do j=1,N
         if (j.lt.N) then
            write(20,'(ES24.16,A)') w(j),','
         else
            write(20,'(ES24.16)') w(j)
         endif
      enddo
      write(20,'(A)') '  ],'
      write(20,'(A)') '  "centerline_u_sum": ['
      do j=1,itime
         if (j.lt.itime) then
            write(20,'(ES24.16,A)') umoms(1,j),','
         else
            write(20,'(ES24.16)') umoms(1,j)
         endif
      enddo
      write(20,'(A)') '  ],'
      write(20,'(A)') '  "centerline_u2_sum": ['
      do j=1,itime
         if (j.lt.itime) then
            write(20,'(ES24.16,A)') umoms(2,j),','
         else
            write(20,'(ES24.16)') umoms(2,j)
         endif
      enddo
      write(20,'(A)') '  ],'
      write(20,'(A,I0,A)') '  "i1": ', i1, ','
      write(20,'(A,I0)') '  "i2": ', i2
      write(20,'(A)') '}'
      close(20)
      end
        """.strip()
        + "\n",
        encoding="utf-8",
    )


def write_fixtures(workdir: Path, ref: dict) -> None:
    cfg = ref["fixtures"]["config"]
    lower = ref["fixtures"]["blowerdt"]
    (workdir / "fixture_blowerdt.dat").write_text(
        "\n".join(
            [f"{lower['dt']} {lower['td']} {lower['pp']} {lower['pa']} {lower['np']}"]
            + [str(x) for x in cfg["rpars"]]
        )
        + "\n",
        encoding="utf-8",
    )
    (workdir / "fixture_scheduled.dat").write_text(
        "\n".join(
            [
                f"{cfg['nstat']} {cfg['ntseg']} {cfg['max_trials']}",
                f"{cfg['tend']} {cfg['dom']} {cfg['visc']} {cfg['pgrad']} {cfg['ratefac']} {cfg['viscpen']} {cfg['nipars']} {cfg['nrpars']}",
            ]
            + [str(x) for x in cfg["ipars"]]
            + [str(x) for x in cfg["rpars"]]
        )
        + "\n",
        encoding="utf-8",
    )


def compile_and_run(workdir: Path, exe_name: str, sources: list[Path], out_name: str) -> dict:
    gfortran = shutil.which("gfortran")
    if not gfortran:
        raise RuntimeError("gfortran not found on PATH")
    exe = workdir / exe_name
    cmd = [gfortran, "-O0", "-std=legacy", "-o", str(exe)] + [str(s) for s in sources]
    subprocess.run(cmd, check=True, cwd=workdir)
    subprocess.run([str(exe)], check=True, cwd=workdir)
    return json.loads((workdir / out_name).read_text(encoding="utf-8"))


def max_abs_diff(a: list[float], b: list[float]) -> float:
    return float(np.max(np.abs(np.asarray(a, dtype=float) - np.asarray(b, dtype=float)))) if a else 0.0


def main() -> int:
    ref = python_reference()
    with tempfile.TemporaryDirectory(prefix="pyodt1-multi-") as tmp:
        workdir = Path(tmp)
        write_driver_files(workdir)
        write_fixtures(workdir, ref)
        blowerdt = compile_and_run(
            workdir,
            "blowerdt.exe",
            [ODT1_SRC / "BLowerdt.f", workdir / "driver_blowerdt.f90"],
            "out_blowerdt.json",
        )
        scheduled = compile_and_run(
            workdir,
            "scheduled.exe",
            [
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
                ODT1_SRC / "BInitRun.f",
                ODT1_SRC / "BInitIter.f",
                workdir / "bstats_stub.f90",
                workdir / "driver_scheduled.f90",
            ],
            "out_scheduled.json",
        )

    py = ref["python"]
    print("# Python reference")
    print(json.dumps(py, indent=2))
    print("\n# Fortran results")
    print(json.dumps({"blowerdt": blowerdt, "scheduled": scheduled}, indent=2))
    print("\n# Differences")
    for key in ["dt", "td", "pp", "pa"]:
        print(f"blowerdt.{key}: abs_diff={abs(py['blowerdt'][key] - blowerdt[key]):.6e}")
    print(f"blowerdt.np diff={py['blowerdt']['np'] - blowerdt['np']}")
    for key in ["trial_count", "accepted_count", "rejected_count", "itime", "i1", "i2"]:
        print(f"scheduled.{key} diff={py['scheduled'][key] - scheduled[key]}")
    for key in ["dt", "td", "scheduled_time", "physical_time"]:
        print(f"scheduled.{key}: abs_diff={abs(py['scheduled'][key] - scheduled[key]):.6e}")
    for key in ["u", "v", "w", "centerline_u_sum", "centerline_u2_sum"]:
        print(f"scheduled.{key}: max_abs_diff={max_abs_diff(py['scheduled'][key], scheduled[key]):.6e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
