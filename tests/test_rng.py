from pyodt1.rng import OdtRNG


def test_legacy_rng_uniform_range():
    rng = OdtRNG(seed_index=1)
    x = rng.uniform()
    assert 0.0 < x < 1.0


def test_legacy_rng_state_roundtrip():
    rng = OdtRNG(seed_index=2)
    s1 = rng.get_state()
    _ = rng.uniform()
    rng.put_state(*s1)
    x1 = rng.uniform()
    rng.put_state(*s1)
    x2 = rng.uniform()
    assert x1 == x2
