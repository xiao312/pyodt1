#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from pyodt1.state import OdtState
from pyodt1.statistics import (
    accumulate_change,
    brecord_text,
    compute_snap_outputs,
    initialize_eddy_statistics,
    save_old_values,
    write_snap_intercomparison,
    write_snap_xmgrace,
    xrecord_text,
)

ROOT = Path(__file__).resolve().parents[1]
ODT1_SRC = ROOT / "external" / "odt1" / "source1"


def python_reference(tmp: Path) -> dict:
    eddy = initialize_eddy_statistics(8, 1)
    before = OdtState(np.arange(8.0), np.arange(8.0) + 1.0, np.zeros(8))
    after = OdtState(before.u.copy(), before.v.copy(), before.w.copy())
    save_old_values(eddy, before, 2, 3)
    after.u[1:4] += 1.0
    after.v[1:4] += 2.0
    accumulate_change(eddy, after, 2, 3, 1, 0)

    btext = brecord_text(3, np.array([1.0, 0.0, 2.5]))
    xtext = xrecord_text(3, np.array([0.1, 0.2, 0.3]), np.array([1.0, 0.0, 2.5]))

    n = 6
    cstat = np.ones((n, 10, 1), dtype=float)
    cstat[:, 1, 0] = np.linspace(0.0, 0.5, n)
    cstat[:, 2, 0] = np.linspace(0.1, 0.6, n)
    cstat[:, 3, 0] = np.linspace(0.2, 0.7, n)
    cstat[:, 4, 0] = cstat[:, 1, 0] ** 2 + 0.01
    cstat[:, 5, 0] = cstat[:, 2, 0] ** 2 + 0.02
    cstat[:, 6, 0] = cstat[:, 3, 0] ** 2 + 0.03
    cstat[:, 7, 0] = 0.04
    cstat[:, 8, 0] = 0.05
    cstat[:, 9, 0] = 0.06
    edstat = np.zeros((n, 4, 4, 1), dtype=float)
    edstat[:, 0, 0, 0] = 0.01
    edstat[:, 1, 0, 0] = 0.02
    edstat[:, 2, 0, 0] = 0.03
    edstat[:, 3, 0, 0] = 0.04
    edstat[0, 0, 3, 0] = 2.0
    snap = compute_snap_outputs(n, np.zeros(n), np.zeros(n), np.zeros(n), 1.0, 1.0e-5, 1, edstat, cstat)
    py_snap_dir = tmp / "py_snap"
    py_snap_dir.mkdir()
    write_snap_intercomparison(py_snap_dir, 1, snap)
    write_snap_xmgrace(py_snap_dir, 1, snap)

    return {
        "python": {
            "old": eddy.old.tolist(),
            "edstat": eddy.edstat.tolist(),
            "brecord": btext,
            "xrecord": xtext,
            "snap_files": {
                name: (py_snap_dir / name).read_text(encoding="utf-8")
                for name in ["A1.dat", "B1.dat", "C1.dat", "D1.dat", "E1.dat", "F1.dat", "G1.dat", "H1.dat", "I1.dat"]
            },
        },
        "fixtures": {
            "cstat": cstat.tolist(),
            "edstat": edstat.tolist(),
        },
    }


def write_direct_driver(workdir: Path) -> None:
    (workdir / "driver_direct.f90").write_text(
        """
      program driver_direct
      implicit none
      integer, parameter :: N=8, NVAL=8
      integer j,k,m,n3
      double precision u(N),v(N),w(N),old(NVAL,3),ed1(NVAL,4,4,1)
      double precision s3(3), x3(3)
      open(10,file='fixture_direct.dat',status='old')
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
      call BSetOld(N,2,3,u,v,w,old,NVAL)
      do j=2,4
         u(j)=u(j)+1.d0
         v(j)=v(j)+2.d0
      enddo
      ed1 = 0.d0
      call BChange(N,2,3,u,v,w,old,ed1,NVAL,1,1,0)
      open(20,file='old.dat',status='unknown')
      do j=1,N
         write(20,*) old(j,1), old(j,2), old(j,3)
      enddo
      close(20)
      open(21,file='edstat.dat',status='unknown')
      do j=1,N
         do k=1,4
            write(21,*) (ed1(j,k,m,1),m=1,4)
         enddo
      enddo
      close(21)
      s3(1)=1.d0
      s3(2)=0.d0
      s3(3)=2.5d0
      x3(1)=0.1d0
      x3(2)=0.2d0
      x3(3)=0.3d0
      n3=3
      open(61,file='brecord.dat',status='unknown')
      call BRecord(61,n3,s3)
      close(61)
      open(62,file='xrecord.dat',status='unknown')
      call XRecord(62,3,x3,s3)
      close(62)
      end
        """.strip()
        + "\n",
        encoding="utf-8",
    )
    lines: list[str] = []
    lines.extend(str(x) for x in np.arange(8.0))
    lines.extend(str(x) for x in (np.arange(8.0) + 1.0))
    lines.extend(str(x) for x in np.zeros(8))
    (workdir / "fixture_direct.dat").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_snap_driver(workdir: Path, ref: dict) -> None:
    (workdir / "driver_snap.f90").write_text(
        """
      program driver_snap
      implicit none
      integer, parameter :: N2=6, MVAL=10
      integer j,k,m,io(100)
      double precision cstat(N2,10,1), ed2(N2,4,4,1), u2(N2), v2(N2), w2(N2)
      open(10,file='fixture_snap.dat',status='old')
      do j=1,N2
         do k=1,10
            read(10,*) cstat(j,k,1)
         enddo
      enddo
      do j=1,N2
         do k=1,4
            do m=1,4
               read(10,*) ed2(j,k,m,1)
            enddo
         enddo
      enddo
      close(10)
      io = 0
      io(1) = 1
      open(41,file='A1.dat',status='unknown')
      open(42,file='B1.dat',status='unknown')
      open(43,file='C1.dat',status='unknown')
      open(44,file='D1.dat',status='unknown')
      open(45,file='E1.dat',status='unknown')
      open(46,file='F1.dat',status='unknown')
      open(47,file='G1.dat',status='unknown')
      open(81,file='H1.dat',status='unknown')
      open(91,file='I1.dat',status='unknown')
      u2 = 0.d0
      v2 = 0.d0
      w2 = 0.d0
      call BSnap(N2,u2,v2,w2,1.d0,1.d-5,1,ed2,cstat,io,N2,MVAL,1)
      close(41)
      close(42)
      close(43)
      close(44)
      close(45)
      close(46)
      close(47)
      close(81)
      close(91)
      end
        """.strip()
        + "\n",
        encoding="utf-8",
    )
    cstat = np.asarray(ref["fixtures"]["cstat"], dtype=float)
    edstat = np.asarray(ref["fixtures"]["edstat"], dtype=float)
    lines = [str(float(cstat[j, k, 0])) for j in range(6) for k in range(10)]
    lines.extend(str(float(edstat[j, k, m, 0])) for j in range(6) for k in range(4) for m in range(4))
    (workdir / "fixture_snap.dat").write_text("\n".join(lines) + "\n", encoding="utf-8")


def compile_and_run(workdir: Path, exe_name: str, sources: list[Path]) -> None:
    gfortran = shutil.which("gfortran")
    if not gfortran:
        raise RuntimeError("gfortran not found on PATH")
    exe = workdir / exe_name
    cmd = [gfortran, "-O0", "-std=legacy", "-o", str(exe)] + [str(s) for s in sources]
    subprocess.run(cmd, check=True, cwd=workdir)
    subprocess.run([str(exe)], check=True, cwd=workdir)


def max_abs_diff(a, b) -> float:
    return float(np.max(np.abs(np.asarray(a, dtype=float) - np.asarray(b, dtype=float))))


def parse_numeric_text(text: str) -> np.ndarray:
    vals = [float(tok) for tok in text.split()]
    return np.asarray(vals, dtype=float)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="pyodt1-post-") as tmpdir:
        tmp = Path(tmpdir)
        ref = python_reference(tmp)
        direct_dir = tmp / "direct"
        snap_dir = tmp / "snap"
        direct_dir.mkdir()
        snap_dir.mkdir()
        write_direct_driver(direct_dir)
        write_snap_driver(snap_dir, ref)
        compile_and_run(
            direct_dir,
            "direct.exe",
            [ODT1_SRC / "BSetOld.f", ODT1_SRC / "BChange.f", ODT1_SRC / "BRecord.f", ODT1_SRC / "XRecord.f", direct_dir / "driver_direct.f90"],
        )
        compile_and_run(
            snap_dir,
            "snap.exe",
            [ODT1_SRC / "BRecord.f", ODT1_SRC / "XRecord.f", ODT1_SRC / "BSnap.f", snap_dir / "driver_snap.f90"],
        )
        ft = {
            "old": np.loadtxt(direct_dir / "old.dat").tolist(),
            "edstat": np.loadtxt(direct_dir / "edstat.dat").reshape(8, 4, 4).tolist(),
            "brecord": (direct_dir / "brecord.dat").read_text(encoding="utf-8"),
            "xrecord": (direct_dir / "xrecord.dat").read_text(encoding="utf-8"),
            "snap_files": {name: (snap_dir / name).read_text(encoding="utf-8") for name in ["A1.dat", "B1.dat", "C1.dat", "D1.dat", "E1.dat", "F1.dat", "G1.dat", "H1.dat", "I1.dat"]},
        }

    py = ref["python"]
    print("# Differences")
    py_old = np.asarray(py['old'], dtype=float)[1:4, :]
    ft_old = np.asarray(ft['old'], dtype=float)[1:4, :]
    py_ed = np.asarray(py['edstat'], dtype=float)[:, :, :, 0]
    ft_ed = np.asarray(ft['edstat'], dtype=float)
    print(f"old(active_range): max_abs_diff={max_abs_diff(py_old, ft_old):.6e}")
    print(f"edstat: max_abs_diff={max_abs_diff(py_ed, ft_ed):.6e}")
    print(f"brecord: max_abs_diff={max_abs_diff(parse_numeric_text(py['brecord']), parse_numeric_text(ft['brecord'])):.6e}")
    print(f"xrecord: max_abs_diff={max_abs_diff(parse_numeric_text(py['xrecord']), parse_numeric_text(ft['xrecord'])):.6e}")
    for name in ["A1.dat", "B1.dat", "C1.dat", "D1.dat", "E1.dat", "F1.dat", "G1.dat", "H1.dat", "I1.dat"]:
        print(f"{name}: max_abs_diff={max_abs_diff(parse_numeric_text(py['snap_files'][name]), parse_numeric_text(ft['snap_files'][name])):.6e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
