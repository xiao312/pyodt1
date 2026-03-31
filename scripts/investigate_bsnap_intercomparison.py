#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ODT1_SRC = ROOT / "external" / "odt1" / "source1"


def write_driver(path: Path, mode: int) -> None:
    path.write_text(
        f"""
      program investigate_bsnap
      implicit none
      integer, parameter :: N=6, MVAL=10, NSTATVAL=1
      integer i,j,k,io(100)
      double precision u(N),v(N),w(N),dom,visc
      double precision cstat(N,10,NSTATVAL), edstat(N,4,4,NSTATVAL)
      io = 0
      io(1) = {mode}
      do i=1,N
         u(i)=0.d0
         v(i)=0.d0
         w(i)=0.d0
         cstat(i,1,1)=1.d0
         cstat(i,2,1)=0.1d0*i
         cstat(i,3,1)=0.05d0*i
         cstat(i,4,1)=0.02d0*i
         cstat(i,5,1)=cstat(i,2,1)**2 + 0.01d0
         cstat(i,6,1)=cstat(i,3,1)**2 + 0.02d0
         cstat(i,7,1)=cstat(i,4,1)**2 + 0.03d0
         cstat(i,8,1)=0.04d0
         cstat(i,9,1)=0.05d0
         cstat(i,10,1)=0.06d0
         do j=1,4
            do k=1,4
               edstat(i,j,k,1)=0.d0
            enddo
         enddo
      enddo
      edstat(1,1,4,1)=1.d0
      dom = 1.d0
      visc = 1.d-5
      if (io(1).eq.0) then
         open(41,file='A1.dat',status='unknown')
         open(42,file='B1.dat',status='unknown')
         open(43,file='C1.dat',status='unknown')
         open(44,file='D1.dat',status='unknown')
      else
         open(41,file='A1.dat',status='unknown')
         open(42,file='B1.dat',status='unknown')
         open(43,file='C1.dat',status='unknown')
         open(44,file='D1.dat',status='unknown')
         open(45,file='E1.dat',status='unknown')
         open(46,file='F1.dat',status='unknown')
         open(47,file='G1.dat',status='unknown')
      endif
      open(81,file='H1.dat',status='unknown')
      open(91,file='I1.dat',status='unknown')
      call BSnap(N,u,v,w,dom,visc,1,edstat,cstat,io,N,MVAL,NSTATVAL)
      end
        """.strip()
        + "\n",
        encoding="utf-8",
    )


def compile_and_run(workdir: Path, mode: int) -> int:
    driver = workdir / f"driver_mode_{mode}.f90"
    exe = workdir / f"mode_{mode}.exe"
    write_driver(driver, mode)
    cmd = [
        shutil.which("gfortran") or "gfortran",
        "-O0",
        "-std=legacy",
        "-o",
        str(exe),
        str(ODT1_SRC / "BRecord.f"),
        str(ODT1_SRC / "XRecord.f"),
        str(ODT1_SRC / "BSnap.f"),
        str(driver),
    ]
    subprocess.run(cmd, check=True, cwd=workdir)
    result = subprocess.run([str(exe)], cwd=workdir)
    return int(result.returncode)


def main() -> int:
    if not shutil.which("gfortran"):
        print("gfortran not found on PATH")
        return 1
    with tempfile.TemporaryDirectory(prefix="pyodt1-bsnap-") as tmp:
        workdir = Path(tmp)
        inter_code = compile_and_run(workdir, 0)
        xmgr_code = compile_and_run(workdir, 1)
        print("# BSnap intercomparison investigation")
        print(f"intercomparison_exit_code={inter_code}")
        print(f"xmgrace_exit_code={xmgr_code}")
        print("intercomparison mode currently crashes under the local toolchain, while xmgrace mode runs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
