import numpy as np

from pyodt1.state import OdtState
from pyodt1.statistics import accumulate_cstats, accumulate_series, finalize_series_variance, initialize_series, initialize_time_statistics, write_series_text


def test_accumulate_series_uses_centerline_value():
    series = initialize_series(10)
    u = np.linspace(0.0, 0.9, 10)
    accumulate_series(series, 1, u)
    ictr = int(0.5 * len(u)) - 1
    assert series.sums[0, 0] == u[ictr]
    assert series.sums[1, 0] == u[ictr] ** 2


def test_accumulate_cstats_matches_expected_terms():
    stats = initialize_time_statistics(4, 2)
    state = OdtState(
        u=np.array([1.0, 2.0, 3.0, 4.0]),
        v=np.array([0.5, 1.0, 1.5, 2.0]),
        w=np.array([0.0, 1.0, 0.0, 1.0]),
    )
    accumulate_cstats(stats, state, 0.2, 1)
    c = stats.cstat[:, :, 0]
    assert np.allclose(c[:, 0], 0.2)
    assert np.allclose(c[:, 1], state.u * 0.2)
    assert np.allclose(c[:, 4], state.u**2 * 0.2)
    assert np.allclose(c[:, 7], np.array([1.0, 1.0, 1.0, 1.0]) * 0.2)


def test_finalize_series_variance_and_write_text():
    umoms = np.zeros((2, 5))
    umoms[0, :3] = [2.0, 4.0, 6.0]
    umoms[1, :3] = [5.0, 10.0, 20.0]
    time, variance = finalize_series_variance(2, 3, 0.3, umoms)
    assert np.allclose(time, [0.1, 0.2, 0.3])
    assert np.allclose(variance, [1.5, 1.0, 1.0])

    ioptions = np.zeros(100, dtype=int)
    text = write_series_text(2, 3, 0.3, 1, umoms, ioptions)
    assert text.startswith("3\n")
    assert "1.0000000E-01" in text
