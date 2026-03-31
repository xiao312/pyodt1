import numpy as np

from pyodt1.acceptance import acceptance_probability
from pyodt1.config import read_config, read_options, read_pars
from pyodt1.eddy_sampling import build_length_distribution, sample_eddy, sample_length, sample_location
from pyodt1.rng import OdtRNG


def test_read_options_and_pars(tmp_path):
    (tmp_path / "BOptions.dat").write_text("2\n1\n3\n", encoding="utf-8")
    (tmp_path / "BPars.dat").write_text("3\n90\n100\n2\n2\n0.4\n0.02\n", encoding="utf-8")
    options, nopt = read_options(tmp_path / "BOptions.dat")
    ipars, rpars, nipars, nrpars = read_pars(tmp_path / "BPars.dat")
    assert nopt == 2
    assert options[0] == 1 and options[1] == 3
    assert nipars == 3
    assert nrpars == 2
    assert ipars[0] == 90
    assert ipars[2] == 2
    assert rpars[0] == 0.4


def test_read_config(tmp_path):
    (tmp_path / "BConfig.dat").write_text("1\n2\n3\n4.0\n5.0\n0.1\n0.2\n0.3\n0.4\n", encoding="utf-8")
    vals = read_config(tmp_path / "BConfig.dat", nmesh=90)
    assert vals[0:4] == (1, 2, 3, 4.0)
    assert np.isclose(vals[7], 3.0 * 0.3 * 90 / 5.0)
    assert np.isclose(vals[8], 0.4 * (0.1 * 90 / 5.0) ** 2)


def test_build_length_distribution_monotone():
    ipars = np.zeros(100, dtype=int)
    ipars[2] = 2
    ipars[3] = 4
    ipars[4] = 10
    dist = build_length_distribution(40, ipars, 5)
    assert dist.io == 2
    assert dist.iv == 10
    assert np.all(np.diff(dist.pl) >= 0.0)
    assert np.isclose(dist.pl[dist.iv - 1], 1.0)


def test_sample_length_and_location_bounds():
    ipars = np.zeros(100, dtype=int)
    ipars[2] = 2
    ipars[3] = 4
    ipars[4] = 8
    dist = build_length_distribution(40, ipars, 5)
    rng = OdtRNG(i1=123456789, i2=362436069)
    l3 = sample_length(40, dist, rng)
    l = 3 * l3
    m = sample_location(40, l, rng)
    assert dist.io <= l3 <= dist.iv
    assert 1 <= m <= 40 - l


def test_acceptance_probability_nonnegative():
    pl = np.zeros(20)
    pl[0] = 0.0
    pl[1] = 0.3
    pl[2:] = 1.0
    pp = acceptance_probability(
        nmesh=20,
        l3=2,
        dt=0.01,
        pl=pl,
        ratefac=1.0,
        viscpen=0.0,
        u_kernel=1.0,
        v_kernel=0.0,
        w_kernel=0.0,
    )
    assert pp > 0.0


def test_acceptance_probability_uses_fortran_pl_indexing():
    pl = np.ones(12)
    pl[0] = 0.0   # Fortran PL(1)
    pl[1] = 0.25  # Fortran PL(2)
    pl[2:] = 1.0  # Fortran PL(3:)
    pp = acceptance_probability(
        nmesh=12,
        l3=2,
        dt=0.01,
        pl=pl,
        ratefac=1.25,
        viscpen=0.02,
        u_kernel=-0.022222222222222223,
        v_kernel=0.022222222222222223,
        w_kernel=0.0,
    )
    assert np.isclose(pp, 5.7741626339104024e-05)


def test_sample_eddy_returns_structured_result():
    ipars = np.zeros(100, dtype=int)
    ipars[2] = 2
    ipars[3] = 4
    ipars[4] = 8
    dist = build_length_distribution(40, ipars, 5)
    u = np.linspace(0.0, 1.0, 40)
    v = np.zeros(40)
    w = np.zeros(40)
    rng = OdtRNG(i1=987654321, i2=123456789)
    sample = sample_eddy(
        nmesh=40,
        u=u,
        v=v,
        w=w,
        dt=0.01,
        dist=dist,
        ratefac=1.0,
        viscpen=0.0,
        rng=rng,
    )
    assert sample.l == 3 * sample.l3
    assert 1 <= sample.m <= 40 - sample.l
    assert sample.acceptance_probability >= 0.0
