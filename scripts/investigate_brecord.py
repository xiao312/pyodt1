#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B_RECORD = ROOT / "external" / "odt1" / "source1" / "BRecord.f"


def main() -> int:
    gfortran = shutil.which("gfortran")
    if not gfortran:
        print("gfortran not found on PATH")
        return 1

    with tempfile.TemporaryDirectory(prefix="pyodt1-brecord-") as tmp:
        workdir = Path(tmp)
        driver = workdir / "driver.f90"
        driver.write_text(
            """
      program test_brecord_pos
      implicit none
      double precision s(3)
      s(1)=1.d0
      s(2)=0.d0
      s(3)=2.5d0
      open(61,file='brecord.dat',status='unknown')
      call BRecord(61,3,s)
      close(61)
      end
            """.strip()
            + "\n",
            encoding="utf-8",
        )
        exe = workdir / "test.exe"
        cmd = [gfortran, "-O0", "-std=legacy", "-o", str(exe), str(B_RECORD), str(driver)]
        print("# compile")
        print(" ".join(cmd))
        subprocess.run(cmd, check=True, cwd=workdir)
        print("# run")
        run = subprocess.run([str(exe)], cwd=workdir)
        print(f"exit_code={run.returncode}")
        out = workdir / "brecord.dat"
        if out.exists():
            print("# output")
            print(out.read_text(encoding="utf-8"))
        else:
            print("# no output file produced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
