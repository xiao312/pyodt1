#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from pyodt1.acceptance import acceptance_probability
from pyodt1.eddy_sampling import bs_kd, build_length_distribution, sample_length, sample_location
from pyodt1.rng import OdtRNG
from pyodt1.triplet import add_k, triplet_map


ROOT = Path(__file__).resolve().parents[1]
ODT1_SRC = ROOT / "external" / "odt1" / "source1"


def python_reference_case() -> dict:
    n = 12
    m = 3  # one-based
    l = 6
    l3 = l // 3
    dt = 0.01
    ratefac = 1.25
    viscpen = 0.02
    pl = np.ones(n, dtype=float)
    pl[0] = 0.0
    pl[1] = 0.25
    pl[2:] = 1.0

    u = np.linspace(0.0, 1.1, n)
    v = np.linspace(1.0, -0.1, n)
    w = np.zeros(n)

    uk = bs_kd(u, m, l)
    vk = bs_kd(v, m, l)
    wk = bs_kd(w, m, l)
    pp = acceptance_probability(
        nmesh=n,
        l3=l3,
        dt=dt,
        pl=pl,
        ratefac=ratefac,
        viscpen=viscpen,
        u_kernel=uk,
        v_kernel=vk,
        w_kernel=wk,
    )

    disfac = 1.0 - 3.0 / float(l)
    cfac = 6.75 / (disfac * float(l))
    root = np.sqrt((uk * uk + vk * vk + wk * wk) / 3.0)
    cu = float(cfac * (-uk + np.copysign(root, uk)))
    cv = float(cfac * (-vk + np.copysign(root, vk)))
    cw = float(cfac * (-wk + np.copysign(root, wk)))

    start = m - 1
    um = add_k(triplet_map(u, start, l), start, l, cu)
    vm = add_k(triplet_map(v, start, l), start, l, cv)
    wm = add_k(triplet_map(w, start, l), start, l, cw)

    return {
        "inputs": {
            "n": n,
            "m": m,
            "l": l,
            "l3": l3,
            "dt": dt,
            "ratefac": ratefac,
            "viscpen": viscpen,
            "pl": pl.tolist(),
            "u": u.tolist(),
            "v": v.tolist(),
            "w": w.tolist(),
        },
        "python": {
            "uk": uk,
            "vk": vk,
            "wk": wk,
            "pp": pp,
            "cu": cu,
            "cv": cv,
            "cw": cw,
            "u_after": um.tolist(),
            "v_after": vm.tolist(),
            "w_after": wm.tolist(),
        },
    }


def python_sample_reference() -> dict:
    n = 40
    ipars = np.zeros(100, dtype=int)
    ipars[2] = 2
    ipars[3] = 4
    ipars[4] = 8
    ipars[5] = 1
    dist = build_length_distribution(n, ipars, 5)
    rng = OdtRNG(seed_index=1)
    l3 = sample_length(n, dist, rng)
    l = 3 * l3
    m = sample_location(n, l, rng)
    i1, i2 = rng.get_state()
    return {
        "sampling_inputs": {
            "n": n,
            "io": dist.io,
            "ip": dist.ip,
            "co": dist.co,
            "cv": dist.cv,
            "pl": dist.pl.tolist(),
        },
        "sampling_python": {
            "l3": l3,
            "l": l,
            "m": m,
            "i1": i1,
            "i2": i2,
        },
    }


def write_driver(workdir: Path) -> Path:
    driver = workdir / "driver.f90"
    driver.write_text(
        """
      program pycompare
      implicit none
      integer N,M,L,L3,j
      double precision dt,ratefac,viscpen,pp,uK,vK,wK,root,disfac,cfac
       double precision BsKd
      double precision cu,cv,cw
      parameter (N=12)
      double precision u(N),v(N),w(N),pl(N)
      open(10,file='fixture.dat',status='old')
      read(10,*) M,L,dt,ratefac,viscpen
      L3=L/3
      do j=1,N
         read(10,*) pl(j)
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
      uK=BsKd(N,M,L,u)
      vK=BsKd(N,M,L,v)
      wK=BsKd(N,M,L,w)
      call BProb(N,M,L3,u,v,w,dt,pl,ratefac,viscpen,uK,vK,wK,pp)
      disfac=(1.d0-3.d0/dfloat(L))
      cfac=6.75d0/(disfac*dfloat(L))
      root=dsqrt((uK*uK+vK*vK+wK*wK)/3.d0)
      cu=cfac*(-uK+sign(1.d0,uK)*root)
      cv=cfac*(-vK+sign(1.d0,vK)*root)
      cw=cfac*(-wK+sign(1.d0,wK)*root)
      call BEddy(N,M,L,u,v,w,uK,vK,wK)
      open(20,file='fortran_out.json',status='unknown')
      write(20,'(A)') '{'
      write(20,'(A,ES24.16,A)') '  "uk": ',uK,','
      write(20,'(A,ES24.16,A)') '  "vk": ',vK,','
      write(20,'(A,ES24.16,A)') '  "wk": ',wK,','
      write(20,'(A,ES24.16,A)') '  "pp": ',pp,','
      write(20,'(A,ES24.16,A)') '  "cu": ',cu,','
      write(20,'(A,ES24.16,A)') '  "cv": ',cv,','
      write(20,'(A,ES24.16,A)') '  "cw": ',cw,','
      write(20,'(A)') '  "u_after": ['
      do j=1,N
         if (j.lt.N) then
            write(20,'(ES24.16,A)') u(j),','
         else
            write(20,'(ES24.16)') u(j)
         endif
      enddo
      write(20,'(A)') '  ],'
      write(20,'(A)') '  "v_after": ['
      do j=1,N
         if (j.lt.N) then
            write(20,'(ES24.16,A)') v(j),','
         else
            write(20,'(ES24.16)') v(j)
         endif
      enddo
      write(20,'(A)') '  ],'
      write(20,'(A)') '  "w_after": ['
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
    return driver


def write_fixture(workdir: Path, case: dict) -> None:
    inp = case["inputs"]
    lines = [f"{inp['m']} {inp['l']} {inp['dt']} {inp['ratefac']} {inp['viscpen']}"]
    for key in ["pl", "u", "v", "w"]:
        lines.extend(str(x) for x in inp[key])
    (workdir / "fixture.dat").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_sampling_driver(workdir: Path) -> Path:
    driver = workdir / "sampling_driver.f90"
    driver.write_text(
        """
      program pysampling
      implicit none
      integer N,Io,Ip,L3,L,M,j,nipars,i1,i2
      double precision Co,Cv,rannum
      parameter (N=40)
      integer ipars(100)
      double precision PL(N)
      double precision BsKd
      open(10,file='sampling_fixture.dat',status='old')
      read(10,*) nipars
      do j=1,100
         read(10,*) ipars(j)
      enddo
      close(10)
      call BSeeds(ipars,i1,i2)
      call BLenProb(N,Io,Ip,PL,Co,Cv,ipars,nipars)
      call BLength(N,PL,L3,Io,Ip,Cv,Co,i1,i2)
      L=3*L3
      call Brng(rannum,i1,i2)
      M=1+min(N-L-1,int(rannum*(N-L)))
      open(20,file='sampling_out.json',status='unknown')
      write(20,'(A)') '{'
      write(20,'(A,I0,A)') '  "l3": ',L3,','
      write(20,'(A,I0,A)') '  "l": ',L,','
      write(20,'(A,I0,A)') '  "m": ',M,','
      write(20,'(A,I0,A)') '  "i1": ',i1,','
      write(20,'(A,I0)') '  "i2": ',i2
      write(20,'(A)') '}'
      close(20)
      end
        """.strip()
        + "\n",
        encoding="utf-8",
    )
    return driver


def write_sampling_fixture(workdir: Path) -> None:
    ipars = [0] * 100
    ipars[2] = 2
    ipars[3] = 4
    ipars[4] = 8
    ipars[5] = 1
    lines = ["5"] + [str(x) for x in ipars]
    (workdir / "sampling_fixture.dat").write_text("\n".join(lines) + "\n", encoding="utf-8")


def compile_and_run_fortran(workdir: Path) -> dict | None:
    gfortran = shutil.which("gfortran")
    if not gfortran:
        return None
    sources = [
        ODT1_SRC / "BTriplet.f",
        ODT1_SRC / "BAddK.f",
        ODT1_SRC / "BsKd.f",
        ODT1_SRC / "BProb.f",
        ODT1_SRC / "BEddy.f",
        workdir / "driver.f90",
    ]
    exe = workdir / "compare.exe"
    cmd = [gfortran, "-O0", "-std=legacy", "-o", str(exe)] + [str(s) for s in sources]
    subprocess.run(cmd, check=True, cwd=workdir)
    subprocess.run([str(exe)], check=True, cwd=workdir)
    return json.loads((workdir / "fortran_out.json").read_text(encoding="utf-8"))


def compile_and_run_sampling_fortran(workdir: Path) -> dict | None:
    gfortran = shutil.which("gfortran")
    if not gfortran:
        return None
    sources = [
        ODT1_SRC / "Brng.f",
        ODT1_SRC / "BSeeds.f",
        ODT1_SRC / "BLenProb.f",
        ODT1_SRC / "BLength.f",
        workdir / "sampling_driver.f90",
    ]
    exe = workdir / "sampling_compare.exe"
    cmd = [gfortran, "-O0", "-std=legacy", "-o", str(exe)] + [str(s) for s in sources]
    subprocess.run(cmd, check=True, cwd=workdir)
    subprocess.run([str(exe)], check=True, cwd=workdir)
    return json.loads((workdir / "sampling_out.json").read_text(encoding="utf-8"))


def main() -> int:
    case = python_reference_case()
    sampling_case = python_sample_reference()
    with tempfile.TemporaryDirectory(prefix="pyodt1-compare-") as tmp:
        workdir = Path(tmp)
        write_driver(workdir)
        write_fixture(workdir, case)
        write_sampling_driver(workdir)
        write_sampling_fixture(workdir)
        fortran = compile_and_run_fortran(workdir)
        sampling_fortran = compile_and_run_sampling_fortran(workdir)

    print("# Python reference")
    print(json.dumps(case, indent=2))
    print("\n# Python sampling reference")
    print(json.dumps(sampling_case, indent=2))
    if fortran is None or sampling_fortran is None:
        print("\n# Fortran comparison skipped")
        print("gfortran not found on PATH. This harness is ready, but compilation requires a local Fortran compiler.")
        return 0

    print("\n# Fortran result")
    print(json.dumps(fortran, indent=2))
    print("\n# Fortran sampling result")
    print(json.dumps(sampling_fortran, indent=2))

    py = case["python"]
    checks = ["uk", "vk", "wk", "pp", "cu", "cv", "cw"]
    print("\n# Differences")
    for k in checks:
        diff = abs(py[k] - fortran[k])
        print(f"{k}: abs_diff={diff:.6e}")
    for k in ["u_after", "v_after", "w_after"]:
        diff = np.max(np.abs(np.asarray(py[k]) - np.asarray(fortran[k])))
        print(f"{k}: max_abs_diff={diff:.6e}")

    print("\n# Sampling differences")
    pys = sampling_case["sampling_python"]
    for k in ["l3", "l", "m", "i1", "i2"]:
        print(f"{k}: py={pys[k]} ft={sampling_fortran[k]} diff={pys[k]-sampling_fortran[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
