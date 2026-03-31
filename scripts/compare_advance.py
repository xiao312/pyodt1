#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from pyodt1.advance import advance_diffusion, compute_initial_dt, compute_td, equation_step, generate_initial_state, sample_exponential_wait
from pyodt1.config import OdtConfig
from pyodt1.rng import OdtRNG
from pyodt1.state import OdtState


ROOT = Path(__file__).resolve().parents[1]
ODT1_SRC = ROOT / "external" / "odt1" / "source1"


def _config(nmesh: int = 8, dom: float = 1.0, visc: float = 0.5, pgrad: float = 1.0) -> OdtConfig:
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
        dom=dom,
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


def python_reference() -> dict:
    adv_in = np.array([1.0, 2.0, 3.0, 4.0], dtype=float)
    adv_out = advance_diffusion(adv_in, tstep=0.01, dom=1.0, visc=0.1, force=0.3)

    cfg = _config()
    state = OdtState(
        u=np.linspace(0.0, 0.7, cfg.nmesh),
        v=np.linspace(1.0, 0.3, cfg.nmesh),
        w=np.linspace(-0.2, 0.2, cfg.nmesh),
        time=0.0,
    )
    eqn_out = equation_step(state, delt=1.0e-4, dom=cfg.dom, visc=cfg.visc, pgrad=cfg.pgrad, rpars=cfg.rpars)

    rng = OdtRNG(seed_index=1)
    init_state = generate_initial_state(cfg.nmesh, cfg.dom, rng)
    initrun_i1, initrun_i2 = rng.get_state()

    rng_exp = OdtRNG(i1=123456789, i2=362436069)
    wait = sample_exponential_wait(0.1, rng_exp)
    bexp_i1, bexp_i2 = rng_exp.get_state()

    rng_iter = OdtRNG(seed_index=1)
    iter_state = generate_initial_state(cfg.nmesh, cfg.dom, rng_iter)
    dt = compute_initial_dt(cfg)
    td = compute_td(dt, cfg)
    t = sample_exponential_wait(dt, rng_iter)
    inititer_i1, inititer_i2 = rng_iter.get_state()

    return {
        "python": {
            "badv": {
                "input": adv_in.tolist(),
                "output": adv_out.tolist(),
            },
            "beqnstep": {
                "u": eqn_out.u.tolist(),
                "v": eqn_out.v.tolist(),
                "w": eqn_out.w.tolist(),
            },
            "bexp": {
                "wait": wait,
                "i1": bexp_i1,
                "i2": bexp_i2,
            },
            "binitrun": {
                "u": init_state.u.tolist(),
                "v": init_state.v.tolist(),
                "w": init_state.w.tolist(),
                "i1": initrun_i1,
                "i2": initrun_i2,
            },
            "binititer": {
                "dt": dt,
                "td": td,
                "t": t,
                "u": iter_state.u.tolist(),
                "v": iter_state.v.tolist(),
                "w": iter_state.w.tolist(),
                "i1": inititer_i1,
                "i2": inititer_i2,
            },
        },
        "fixtures": {
            "badv": {"tstep": 0.01, "dom": 1.0, "visc": 0.1, "force": 0.3},
            "beqnstep": {
                "delt": 1.0e-4,
                "dom": cfg.dom,
                "visc": cfg.visc,
                "pgrad": cfg.pgrad,
                "rpars": cfg.rpars.tolist(),
                "u": state.u.tolist(),
                "v": state.v.tolist(),
                "w": state.w.tolist(),
            },
            "bexp": {"dt": 0.1, "i1": 123456789, "i2": 362436069},
            "binit": {
                "nmesh": cfg.nmesh,
                "dom": cfg.dom,
                "visc": cfg.visc,
                "ipars": cfg.ipars.tolist(),
                "rpars": cfg.rpars.tolist(),
                "nipars": cfg.nipars,
                "nrpars": cfg.nrpars,
            },
        },
    }


def _write_lines(path: Path, values: list[str]) -> None:
    path.write_text("\n".join(values) + "\n", encoding="utf-8")


def write_drivers(workdir: Path) -> None:
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

    (workdir / "driver_badv.f90").write_text(
        """
      program driver_badv
      implicit none
      integer, parameter :: N=4
      integer j
      double precision r(N), tstep, dom, visc, force
      open(10,file='fixture_badv.dat',status='old')
      read(10,*) tstep, dom, visc, force
      do j=1,N
         read(10,*) r(j)
      enddo
      close(10)
      call BAdv(N,r,tstep,dom,visc,force)
      open(20,file='out_badv.json',status='unknown')
      write(20,'(A)') '{'
      write(20,'(A)') '  "output": ['
      do j=1,N
         if (j.lt.N) then
            write(20,'(ES24.16,A)') r(j),','
         else
            write(20,'(ES24.16)') r(j)
         endif
      enddo
      write(20,'(A)') '  ]'
      write(20,'(A)') '}'
      close(20)
      end
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    (workdir / "driver_beqnstep.f90").write_text(
        """
      program driver_beqnstep
      implicit none
      integer, parameter :: N=8, NVAL=8, MVAL=10, NSTATVAL=4
      integer j, istat
      double precision delt, dom, visc, pgrad
      double precision u(N), v(N), w(N), rpars(100)
      double precision cstat(NVAL,MVAL,NSTATVAL)
      open(10,file='fixture_beqnstep.dat',status='old')
      read(10,*) delt, dom, visc, pgrad, istat
      do j=1,100
         read(10,*) rpars(j)
      enddo
      do j=1,N
         read(10,*) u(j)
      enddo
      do j=1,N
         read(10,*) v(j)
      enddo
      do j=1,N
         read(10,*) w(j)
      enddo
      close(10)
      cstat = 0.d0
      call BEqnStep(N,u,v,w,delt,dom,visc,pgrad,rpars,istat,cstat,NVAL,MVAL,NSTATVAL)
      open(20,file='out_beqnstep.json',status='unknown')
      write(20,'(A)') '{'
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
      write(20,'(A)') '  ]'
      write(20,'(A)') '}'
      close(20)
      end
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    (workdir / "driver_bexp.f90").write_text(
        """
      program driver_bexp
      implicit none
      integer i1, i2
      double precision dt, wait, BExp
      open(10,file='fixture_bexp.dat',status='old')
      read(10,*) dt, i1, i2
      close(10)
      wait = BExp(dt,i1,i2)
      open(20,file='out_bexp.json',status='unknown')
      write(20,'(A)') '{'
      write(20,'(A,ES24.16,A)') '  "wait": ', wait, ','
      write(20,'(A,I0,A)') '  "i1": ', i1, ','
      write(20,'(A,I0)') '  "i2": ', i2
      write(20,'(A)') '}'
      close(20)
      end
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    (workdir / "driver_binitrun.f90").write_text(
        """
      program driver_binitrun
      implicit none
      integer, parameter :: N=8
      integer j, i1, i2, nipars
      integer ipars(100)
      double precision x, u(N), v(N), w(N), dom
      open(10,file='fixture_binit.dat',status='old')
      read(10,*) dom, nipars
      do j=1,100
         read(10,*) ipars(j)
      enddo
      close(10)
      call BSeeds(ipars,i1,i2)
      call BInitRun(N,i1,i2,dom)
      open(1,file='U.dat',status='old')
      open(2,file='V.dat',status='old')
      open(3,file='W.dat',status='old')
      do j=1,N
         read(1,*) x, u(j)
         read(2,*) x, v(j)
         read(3,*) x, w(j)
      enddo
      close(1)
      close(2)
      close(3)
      open(20,file='out_binitrun.json',status='unknown')
      write(20,'(A)') '{'
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
      write(20,'(A,I0,A)') '  "i1": ', i1, ','
      write(20,'(A,I0)') '  "i2": ', i2
      write(20,'(A)') '}'
      close(20)
      end
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    (workdir / "driver_binititer.f90").write_text(
        """
      program driver_binititer
      implicit none
      integer, parameter :: N=8
      integer j, i1, i2, nipars, nrpars, itime, ii, Np
      integer ipars(100)
      double precision dom, visc, pa, tmark, t, to, dt, td, x
      double precision u(N), v(N), w(N), rpars(100)
      open(10,file='fixture_binititer.dat',status='old')
      read(10,*) dom, visc, nipars, nrpars
      do j=1,100
         read(10,*) ipars(j)
      enddo
      do j=1,100
         read(10,*) rpars(j)
      enddo
      close(10)
      call BSeeds(ipars,i1,i2)
      call BInitRun(N,i1,i2,dom)
      call BInitIter(N,u,v,w,itime,ii,Np,pa,tmark,t,to,dt,td,nrpars,rpars,dom,visc,i1,i2)
      open(20,file='out_binititer.json',status='unknown')
      write(20,'(A)') '{'
      write(20,'(A,ES24.16,A)') '  "dt": ', dt, ','
      write(20,'(A,ES24.16,A)') '  "td": ', td, ','
      write(20,'(A,ES24.16,A)') '  "t": ', t, ','
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
    fixtures = ref["fixtures"]
    _write_lines(
        workdir / "fixture_badv.dat",
        [
            f"{fixtures['badv']['tstep']} {fixtures['badv']['dom']} {fixtures['badv']['visc']} {fixtures['badv']['force']}"
        ]
        + [str(x) for x in ref["python"]["badv"]["input"]],
    )
    _write_lines(
        workdir / "fixture_beqnstep.dat",
        [
            f"{fixtures['beqnstep']['delt']} {fixtures['beqnstep']['dom']} {fixtures['beqnstep']['visc']} {fixtures['beqnstep']['pgrad']} 1"
        ]
        + [str(x) for x in fixtures["beqnstep"]["rpars"]]
        + [str(x) for x in fixtures["beqnstep"]["u"]]
        + [str(x) for x in fixtures["beqnstep"]["v"]]
        + [str(x) for x in fixtures["beqnstep"]["w"]],
    )
    _write_lines(
        workdir / "fixture_bexp.dat",
        [f"{fixtures['bexp']['dt']} {fixtures['bexp']['i1']} {fixtures['bexp']['i2']}"]
    )
    _write_lines(
        workdir / "fixture_binit.dat",
        [f"{fixtures['binit']['dom']} {fixtures['binit']['nipars']}"]
        + [str(x) for x in fixtures["binit"]["ipars"]],
    )
    _write_lines(
        workdir / "fixture_binititer.dat",
        [
            f"{fixtures['binit']['dom']} {fixtures['binit']['visc']} {fixtures['binit']['nipars']} {fixtures['binit']['nrpars']}"
        ]
        + [str(x) for x in fixtures["binit"]["ipars"]]
        + [str(x) for x in fixtures["binit"]["rpars"]],
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
    return float(np.max(np.abs(np.asarray(a, dtype=float) - np.asarray(b, dtype=float))))


def main() -> int:
    ref = python_reference()
    with tempfile.TemporaryDirectory(prefix="pyodt1-advance-") as tmp:
        workdir = Path(tmp)
        write_drivers(workdir)
        write_fixtures(workdir, ref)

        badv = compile_and_run(
            workdir,
            "badv.exe",
            [ODT1_SRC / "BAdv.f", workdir / "driver_badv.f90"],
            "out_badv.json",
        )
        beqnstep = compile_and_run(
            workdir,
            "beqnstep.exe",
            [ODT1_SRC / "BAdv.f", ODT1_SRC / "BEqnStep.f", workdir / "bstats_stub.f90", workdir / "driver_beqnstep.f90"],
            "out_beqnstep.json",
        )
        bexp = compile_and_run(
            workdir,
            "bexp.exe",
            [ODT1_SRC / "Brng.f", ODT1_SRC / "BExp.f", workdir / "driver_bexp.f90"],
            "out_bexp.json",
        )
        binitrun = compile_and_run(
            workdir,
            "binitrun.exe",
            [ODT1_SRC / "Brng.f", ODT1_SRC / "BSeeds.f", ODT1_SRC / "BInitRun.f", workdir / "driver_binitrun.f90"],
            "out_binitrun.json",
        )
        binititer = compile_and_run(
            workdir,
            "binititer.exe",
            [ODT1_SRC / "Brng.f", ODT1_SRC / "BSeeds.f", ODT1_SRC / "BExp.f", ODT1_SRC / "BInitRun.f", ODT1_SRC / "BInitIter.f", workdir / "driver_binititer.f90"],
            "out_binititer.json",
        )

    py = ref["python"]
    print("# Python reference")
    print(json.dumps(py, indent=2))
    print("\n# Fortran results")
    print(json.dumps({"badv": badv, "beqnstep": beqnstep, "bexp": bexp, "binitrun": binitrun, "binititer": binititer}, indent=2))

    print("\n# Differences")
    print(f"badv.output: max_abs_diff={max_abs_diff(py['badv']['output'], badv['output']):.6e}")
    for key in ["u", "v", "w"]:
        print(f"beqnstep.{key}: max_abs_diff={max_abs_diff(py['beqnstep'][key], beqnstep[key]):.6e}")
    print(f"bexp.wait: abs_diff={abs(py['bexp']['wait'] - bexp['wait']):.6e}")
    print(f"bexp.i1 diff={py['bexp']['i1'] - bexp['i1']}")
    print(f"bexp.i2 diff={py['bexp']['i2'] - bexp['i2']}")
    for key in ["u", "v", "w"]:
        print(f"binitrun.{key}: max_abs_diff={max_abs_diff(py['binitrun'][key], binitrun[key]):.6e}")
    print(f"binitrun.i1 diff={py['binitrun']['i1'] - binitrun['i1']}")
    print(f"binitrun.i2 diff={py['binitrun']['i2'] - binitrun['i2']}")
    for scalar in ["dt", "td", "t"]:
        print(f"binititer.{scalar}: abs_diff={abs(py['binititer'][scalar] - binititer[scalar]):.6e}")
    for key in ["u", "v", "w"]:
        print(f"binititer.{key}: max_abs_diff={max_abs_diff(py['binititer'][key], binititer[key]):.6e}")
    print(f"binititer.i1 diff={py['binititer']['i1'] - binititer['i1']}")
    print(f"binititer.i2 diff={py['binititer']['i2'] - binititer['i2']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
