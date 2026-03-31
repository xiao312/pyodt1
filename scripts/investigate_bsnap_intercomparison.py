#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ODT1_SRC = ROOT / "external" / "odt1" / "source1"


B_RECORD_NEG_DRIVER = """
      program investigate_brecord_negative
      implicit none
      integer n
      double precision s(6)
      n = -6
      s(1)=1.d0
      s(2)=2.d0
      s(3)=3.d0
      s(4)=4.d0
      s(5)=5.d0
      s(6)=6.d0
      open(61,file='brecord_neg6.dat',status='unknown')
      call BRecord(61,n,s)
      close(61)
      end
"""


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
    gfortran = shutil.which("gfortran")
    if not gfortran:
        print("gfortran not found on PATH")
        return 1
    with tempfile.TemporaryDirectory(prefix="pyodt1-bsnap-") as tmp:
        workdir = Path(tmp)
        inter_code = compile_and_run(workdir, 0)
        xmgr_code = compile_and_run(workdir, 1)

        neg_driver = workdir / "driver_brecord_neg.f90"
        neg_driver.write_text(B_RECORD_NEG_DRIVER.strip() + "\n", encoding="utf-8")
        neg_exe = workdir / "brecord_neg.exe"
        subprocess.run(
            [gfortran, "-O0", "-std=legacy", "-o", str(neg_exe), str(ODT1_SRC / "BRecord.f"), str(neg_driver)],
            check=True,
            cwd=workdir,
        )
        neg_result = subprocess.run([str(neg_exe)], cwd=workdir)

        print("# BSnap intercomparison investigation")
        print(f"intercomparison_exit_code={inter_code}")
        print(f"xmgrace_exit_code={xmgr_code}")
        print(f"brecord_negative_header_exit_code={int(neg_result.returncode)}")
        print("The crash is traced to the intercomparison-mode header convention: BSnap calls BRecord with negative N to request a header, and BRecord uses that negative N in automatic array extents before taking abs(N). This is undefined behavior and crashes here for sufficiently large |N|.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
