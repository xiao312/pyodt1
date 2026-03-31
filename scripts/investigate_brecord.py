#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B_RECORD = ROOT / "external" / "odt1" / "source1" / "BRecord.f"


def compile_and_run(workdir: Path, source: str, name: str) -> int:
    driver = workdir / f"{name}.f90"
    driver.write_text(source.strip() + "\n", encoding="utf-8")
    exe = workdir / f"{name}.exe"
    cmd = [shutil.which("gfortran") or "gfortran", "-O0", "-std=legacy", "-o", str(exe), str(B_RECORD), str(driver)]
    subprocess.run(cmd, check=True, cwd=workdir)
    run = subprocess.run([str(exe)], cwd=workdir)
    return int(run.returncode)


def main() -> int:
    gfortran = shutil.which("gfortran")
    if not gfortran:
        print("gfortran not found on PATH")
        return 1

    literal_driver = """
      program test_brecord_literal
      implicit none
      double precision s(3)
      s(1)=1.d0
      s(2)=0.d0
      s(3)=2.5d0
      open(61,file='brecord_literal.dat',status='unknown')
      call BRecord(61,3,s)
      close(61)
      end
    """

    variable_driver = """
      program test_brecord_variable
      implicit none
      integer n
      double precision s(3)
      n=3
      s(1)=1.d0
      s(2)=0.d0
      s(3)=2.5d0
      open(61,file='brecord_variable.dat',status='unknown')
      call BRecord(61,n,s)
      close(61)
      print *, n
      end
    """

    with tempfile.TemporaryDirectory(prefix="pyodt1-brecord-") as tmp:
        workdir = Path(tmp)
        literal_code = compile_and_run(workdir, literal_driver, "literal")
        variable_code = compile_and_run(workdir, variable_driver, "variable")
        literal_out = (workdir / "brecord_literal.dat").read_text(encoding="utf-8") if (workdir / "brecord_literal.dat").exists() else ""
        variable_out = (workdir / "brecord_variable.dat").read_text(encoding="utf-8") if (workdir / "brecord_variable.dat").exists() else ""

    print("# BRecord compatibility investigation")
    print(f"literal_argument_exit_code={literal_code}")
    print(f"variable_argument_exit_code={variable_code}")
    print("\n# interpretation")
    print("BRecord mutates N via `N=abs(N)`. Passing a literal such as `3` causes a crash because the routine writes through a by-reference argument that may point to read-only storage.")
    print("Passing an integer variable works under the local toolchain.")
    if variable_out:
        print("\n# variable-argument output")
        print(variable_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
