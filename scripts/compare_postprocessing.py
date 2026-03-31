#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from pyodt1.state import OdtState
from pyodt1.statistics import (
    accumulate_change,
    brecord_text,
    compute_snap_outputs,
    initialize_eddy_statistics,
    parse_brecord_text,
    parse_snap_intercomparison,
    parse_snap_xmgrace,
    parse_xrecord_text,
    save_old_values,
    write_snap_intercomparison,
    write_snap_xmgrace,
    xrecord_text,
)

ROOT = Path(__file__).resolve().parents[1]
ODT1_SRC = ROOT / "external" / "odt1" / "source1"


@dataclass(slots=True)
class SnapFixture:
    name: str
    nmesh: int
    istat: int
    mode: str
    dom: float
    visc: float
    cstat: np.ndarray
    edstat: np.ndarray


def max_abs_diff(a, b) -> float:
    arr_a = np.asarray(a, dtype=float)
    arr_b = np.asarray(b, dtype=float)
    return float(np.max(np.abs(arr_a - arr_b))) if arr_a.size else 0.0


def make_snap_fixture_a() -> SnapFixture:
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
    edstat[1, 1, 3, 0] = 1.0
    return SnapFixture("xmgrace_fixture", n, 1, "xmgrace", 1.0, 1.0e-5, cstat, edstat)


def make_snap_fixture_b() -> SnapFixture:
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
    return SnapFixture("xmgrace_fixture_2", n, 2, "xmgrace", 1.5, 2.5e-5, cstat, edstat)


def python_reference(tmp: Path) -> dict:
    eddy = initialize_eddy_statistics(8, 1)
    before = OdtState(np.arange(8.0), np.arange(8.0) + 1.0, np.zeros(8))
    after = OdtState(before.u.copy(), before.v.copy(), before.w.copy())
    save_old_values(eddy, before, 2, 3)
    after.u[1:4] += 1.0
    after.v[1:4] += 2.0
    accumulate_change(eddy, after, 2, 3, 1, 0)

    fixtures = [make_snap_fixture_a(), make_snap_fixture_b()]
    snap_refs: dict[str, dict[str, dict[str, np.ndarray]]] = {}
    for fixture in fixtures:
        snap = compute_snap_outputs(
            fixture.nmesh,
            np.zeros(fixture.nmesh),
            np.zeros(fixture.nmesh),
            np.zeros(fixture.nmesh),
            fixture.dom,
            fixture.visc,
            fixture.istat,
            fixture.edstat,
            fixture.cstat,
        )
        inter_dir = tmp / f"{fixture.name}_inter"
        xmgr_dir = tmp / f"{fixture.name}_xmgr"
        inter_dir.mkdir()
        xmgr_dir.mkdir()
        write_snap_intercomparison(inter_dir, fixture.istat, snap)
        write_snap_xmgrace(xmgr_dir, fixture.istat, snap)
        snap_refs[fixture.name] = {
            "intercomparison": parse_snap_intercomparison(inter_dir, fixture.istat).records,
            "xmgrace": parse_snap_xmgrace(xmgr_dir, fixture.istat).records,
        }

    return {
        "old": eddy.old.copy(),
        "edstat": eddy.edstat.copy(),
        "brecord": parse_brecord_text(brecord_text(3, np.array([1.0, 0.0, 2.5]))),
        "xrecord": parse_xrecord_text(xrecord_text(3, np.array([0.1, 0.2, 0.3]), np.array([1.0, 0.0, 2.5]))),
        "fixtures": fixtures,
        "snaps": snap_refs,
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


def fortran_double_literal(value: float) -> str:
    return f"{value:.17e}".replace("e", "d")


def write_snap_driver(workdir: Path, fixture: SnapFixture) -> None:
    suffix = fixture.name.replace("-", "_")
    nstatval = fixture.cstat.shape[2]
    call_block = (
        f"      dom = {fortran_double_literal(fixture.dom)}\n"
        f"      visc = {fortran_double_literal(fixture.visc)}\n"
        f"      call BSnap(N2,u2,v2,w2,dom,visc,{fixture.istat},ed2,cstat,io,N2,MVAL,NSTATVAL)"
    )
    if fixture.mode == "xmgrace":
        open_block = f"""
      io = 0
      io(1) = 1
      open({31+10*fixture.istat},file='A{fixture.istat}.dat',status='unknown')
      open({32+10*fixture.istat},file='B{fixture.istat}.dat',status='unknown')
      open({33+10*fixture.istat},file='C{fixture.istat}.dat',status='unknown')
      open({34+10*fixture.istat},file='D{fixture.istat}.dat',status='unknown')
      open({35+10*fixture.istat},file='E{fixture.istat}.dat',status='unknown')
      open({36+10*fixture.istat},file='F{fixture.istat}.dat',status='unknown')
      open({37+10*fixture.istat},file='G{fixture.istat}.dat',status='unknown')
      open({80+fixture.istat},file='H{fixture.istat}.dat',status='unknown')
      open({90+fixture.istat},file='I{fixture.istat}.dat',status='unknown')
        """.strip()
    else:
        open_block = f"""
      io = 0
      io(1) = 0
      open({37+4*fixture.istat},file='A{fixture.istat}.dat',status='unknown')
      open({38+4*fixture.istat},file='B{fixture.istat}.dat',status='unknown')
      open({39+4*fixture.istat},file='C{fixture.istat}.dat',status='unknown')
      open({40+4*fixture.istat},file='D{fixture.istat}.dat',status='unknown')
      open({80+fixture.istat},file='H{fixture.istat}.dat',status='unknown')
      open({90+fixture.istat},file='I{fixture.istat}.dat',status='unknown')
        """.strip()
    driver = f"""
      program driver_{suffix}
      implicit none
      integer, parameter :: N2={fixture.nmesh}, MVAL=10, NSTATVAL={nstatval}
      integer j,k,m,is,io(100)
      double precision cstat(N2,10,NSTATVAL), ed2(N2,4,4,NSTATVAL), u2(N2), v2(N2), w2(N2), dom, visc
      open(10,file='fixture_snap.dat',status='old')
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
{open_block}
      u2 = 0.d0
      v2 = 0.d0
      w2 = 0.d0
{call_block}
      end
    """
    (workdir / "driver_snap.f90").write_text(driver.strip() + "\n", encoding="utf-8")
    lines = [
        str(float(fixture.cstat[j, k, is_]))
        for is_ in range(fixture.cstat.shape[2])
        for j in range(fixture.nmesh)
        for k in range(10)
    ]
    lines.extend(
        str(float(fixture.edstat[j, k, m, is_]))
        for is_ in range(fixture.edstat.shape[3])
        for j in range(fixture.nmesh)
        for k in range(4)
        for m in range(4)
    )
    (workdir / "fixture_snap.dat").write_text("\n".join(lines) + "\n", encoding="utf-8")


def compile_and_run(workdir: Path, exe_name: str, sources: list[Path]) -> None:
    gfortran = shutil.which("gfortran")
    if not gfortran:
        raise RuntimeError("gfortran not found on PATH")
    exe = workdir / exe_name
    cmd = [gfortran, "-O0", "-std=legacy", "-o", str(exe)] + [str(s) for s in sources]
    subprocess.run(cmd, check=True, cwd=workdir)
    subprocess.run([str(exe)], check=True, cwd=workdir)


def compare_snap_records(py_records: dict[str, np.ndarray], ft_records: dict[str, np.ndarray]) -> list[tuple[str, float]]:
    names = sorted(set(py_records) & set(ft_records))
    return [(name, max_abs_diff(py_records[name], ft_records[name])) for name in names]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="pyodt1-post-") as tmpdir:
        tmp = Path(tmpdir)
        ref = python_reference(tmp)

        direct_dir = tmp / "direct"
        direct_dir.mkdir()
        write_direct_driver(direct_dir)
        compile_and_run(
            direct_dir,
            "direct.exe",
            [ODT1_SRC / "BSetOld.f", ODT1_SRC / "BChange.f", ODT1_SRC / "BRecord.f", ODT1_SRC / "XRecord.f", direct_dir / "driver_direct.f90"],
        )

        ft_direct = {
            "old": np.loadtxt(direct_dir / "old.dat"),
            "edstat": np.loadtxt(direct_dir / "edstat.dat").reshape(8, 4, 4),
            "brecord": parse_brecord_text((direct_dir / "brecord.dat").read_text(encoding="utf-8")),
            "xrecord": parse_xrecord_text((direct_dir / "xrecord.dat").read_text(encoding="utf-8")),
        }

        print("# Differences")
        print(f"old(active_range): max_abs_diff={max_abs_diff(ref['old'][1:4, :], ft_direct['old'][1:4, :]):.6e}")
        print(f"edstat: max_abs_diff={max_abs_diff(ref['edstat'][:, :, :, 0], ft_direct['edstat']):.6e}")
        print(f"brecord: max_abs_diff={max_abs_diff(ref['brecord'].records, ft_direct['brecord'].records):.6e}")
        print(f"xrecord: max_abs_diff={max_abs_diff(ref['xrecord'], ft_direct['xrecord']):.6e}")

        for fixture in ref["fixtures"]:
            workdir = tmp / fixture.name
            workdir.mkdir(exist_ok=True)
            write_snap_driver(workdir, fixture)
            compile_and_run(
                workdir,
                "snap.exe",
                [ODT1_SRC / "BRecord.f", ODT1_SRC / "XRecord.f", ODT1_SRC / "BSnap.f", workdir / "driver_snap.f90"],
            )
            if fixture.mode == "xmgrace":
                ft_records = parse_snap_xmgrace(workdir, fixture.istat).records
            else:
                ft_records = parse_snap_intercomparison(workdir, fixture.istat).records
            py_records = ref["snaps"][fixture.name][fixture.mode]
            for name, diff in compare_snap_records(py_records, ft_records):
                print(f"{fixture.name}.{fixture.mode}.{name}: max_abs_diff={diff:.6e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
