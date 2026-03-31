from __future__ import annotations

import numpy as np

from pyodt1.acceptance import acceptance_probability
from pyodt1.config import EddySample, EddySizeDistribution
from pyodt1.rng import OdtRNG


def build_length_distribution(nmesh: int, ipars: np.ndarray, nipars: int) -> EddySizeDistribution:
    io = 2
    ip = 4
    iv = (nmesh - 1) // 3
    if nipars >= 3:
        io = int(ipars[2])
    if nipars >= 4:
        ip = int(ipars[3])
    if nipars >= 5:
        iv = min(iv, int(ipars[4]))

    pl = np.ones(nmesh, dtype=float)
    pl[: io - 1] = 0.0

    co = float(np.exp(-2.0 * ip / float(io)))
    cv = float(np.exp(-2.0 * ip / float(iv)))

    norm = 0.0
    for i in range(io, iv + 1):
        z = np.exp(-2.0 * ip / float(i)) * (np.exp(2.0 * ip / (i * (i + 1.0))) - 1.0)
        norm += z
    c_norm = 1.0 / norm

    for i in range(io, iv):
        z = np.exp(-2.0 * ip / float(i)) * (np.exp(2.0 * ip / (i * (i + 1.0))) - 1.0)
        prev = pl[i - 2] if i - 2 >= 0 else 0.0
        pl[i - 1] = prev + c_norm * z
    pl[iv - 1 :] = 1.0

    return EddySizeDistribution(io=io, ip=ip, iv=iv, co=co, cv=cv, pl=pl)


def sample_length(nmesh: int, dist: EddySizeDistribution, rng: OdtRNG) -> int:
    rannum = rng.uniform()
    x = -2.0 * dist.ip / np.log((dist.cv * rannum) + (dist.co * (1.0 - rannum)))
    nn = int(x) - 1
    nn = max(1, min(nn, nmesh - 1))

    while nn < nmesh and rannum > dist.pl[nn - 1]:
        nn += 1
    while nn > 1 and rannum < dist.pl[nn - 2]:
        nn -= 1
    return max(dist.io, nn)


def sample_location(nmesh: int, l: int, rng: OdtRNG) -> int:
    rannum = rng.uniform()
    return 1 + min(nmesh - l - 1, int(rannum * (nmesh - l)))


def bs_kd(values: np.ndarray, m: int, l: int) -> float:
    """Exact port of `BsKd.f` using one-based `m` and integer `l`."""
    n = values.size
    start = m - 1
    stop = start + l
    if start < 0 or stop > n:
        raise ValueError("eddy interval out of bounds")

    s = np.zeros_like(values, dtype=float)
    s[start:stop] = values[start:stop]

    # Apply triplet map only to the mapped portion, consistent with Fortran routine.
    from pyodt1.triplet import triplet_map

    s = triplet_map(s, start, l)
    lo = l // 3
    total = 0.0
    for j in range(1, lo + 1):
        y1 = -2.0 * (j - 1)
        y2 = 4.0 * (j + lo - 1) - 2.0 * (l - 1)
        y3 = 2.0 * (l - 1) - 2.0 * (j + lo + lo - 1)
        j1 = start + j - 1
        j2 = start + j + lo - 1
        j3 = start + j + lo + lo - 1
        total += s[j1] * y1
        total += s[j2] * y2
        total += s[j3] * y3
    return total / float(l * l)


def sample_eddy(
    *,
    nmesh: int,
    u: np.ndarray,
    v: np.ndarray,
    w: np.ndarray,
    dt: float,
    dist: EddySizeDistribution,
    ratefac: float,
    viscpen: float,
    rng: OdtRNG,
) -> EddySample:
    l3 = sample_length(nmesh, dist, rng)
    l = 3 * l3
    m = sample_location(nmesh, l, rng)
    u_kernel = bs_kd(u, m, l)
    v_kernel = bs_kd(v, m, l)
    w_kernel = bs_kd(w, m, l)
    pp = acceptance_probability(
        nmesh=nmesh,
        l3=l3,
        dt=dt,
        pl=dist.pl,
        ratefac=ratefac,
        viscpen=viscpen,
        u_kernel=u_kernel,
        v_kernel=v_kernel,
        w_kernel=w_kernel,
    )
    return EddySample(
        m=m,
        l=l,
        l3=l3,
        acceptance_probability=pp,
        u_kernel=u_kernel,
        v_kernel=v_kernel,
        w_kernel=w_kernel,
    )
