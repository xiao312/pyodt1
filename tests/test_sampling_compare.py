import numpy as np

from pyodt1.config import EddySizeDistribution
from pyodt1.eddy_sampling import build_length_distribution, sample_length, sample_location
from pyodt1.rng import OdtRNG


def test_sample_length_reproducible_with_legacy_rng():
    ipars = np.zeros(100, dtype=int)
    ipars[2] = 2
    ipars[3] = 4
    ipars[4] = 8
    dist = build_length_distribution(40, ipars, 5)
    rng1 = OdtRNG(seed_index=1)
    rng2 = OdtRNG(seed_index=1)
    assert sample_length(40, dist, rng1) == sample_length(40, dist, rng2)


def test_sample_location_reproducible_with_legacy_rng():
    rng1 = OdtRNG(seed_index=2)
    rng2 = OdtRNG(seed_index=2)
    assert sample_location(40, 6, rng1) == sample_location(40, 6, rng2)
