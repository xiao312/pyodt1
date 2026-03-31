import numpy as np

from pyodt1.triplet import triplet_map


def test_triplet_map_basic_segment():
    arr = np.arange(9)
    out = triplet_map(arr, 0, 9)
    expected = np.array([0, 3, 6, 7, 4, 1, 2, 5, 8])
    assert np.array_equal(out, expected)


def test_triplet_map_subsegment_only_changes_range():
    arr = np.arange(12)
    out = triplet_map(arr, 3, 6)
    expected = np.array([0, 1, 2, 3, 6, 7, 4, 5, 8, 9, 10, 11])
    assert np.array_equal(out, expected)
