from __future__ import annotations

import numpy as np

from pyodt1.legacy import b_add_term, b_init_stats, b_read_options, brng_get, brng_put, run_legacy_case
from pyodt1.rng import OdtRNG


def test_b_read_options_and_rng_state_helpers(tmp_path):
    options_path = tmp_path / "BOptions.dat"
    options_path.write_text("2\n1\n7\n", encoding="utf-8")
    arr, nopt = b_read_options(options_path)
    assert nopt == 2
    assert arr[0] == 1
    assert arr[1] == 7

    rng = OdtRNG(seed_index=1)
    state = brng_get(rng)
    rng.uniform()
    brng_put(rng, *state)
    assert brng_get(rng) == state


def test_b_init_stats_and_b_add_term():
    bundle = b_init_stats(nmesh=4, nstat=2, mval=10, max_points=8)
    assert bundle.series.sums.shape == (2, 8)
    assert bundle.time_statistics.cstat.shape == (4, 10, 2)
    assert bundle.eddy_statistics.edstat.shape == (4, 4, 4, 2)

    term = np.array([1.0, 2.0, 3.0, 4.0])
    b_add_term(3, 4, bundle.time_statistics.cstat, term, 2)
    assert np.allclose(bundle.time_statistics.cstat[:, 2, 1], term)


def test_run_legacy_case_writes_legacy_output_bundle(tmp_path):
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    (case_dir / "BOptions.dat").write_text("1\n1\n", encoding="utf-8")
    (case_dir / "BPars.dat").write_text(
        "6\n18\n2\n2\n4\n8\n1\n6\n0.4\n0.2\n1.5\n0.5\n2.0e-4\n-1.0\n",
        encoding="utf-8",
    )
    (case_dir / "BConfig.dat").write_text(
        "2\n2\n3\n6.0e-4\n1.0\n1.0e-5\n0.0\n1.0\n0.0\n",
        encoding="utf-8",
    )

    out_dir = tmp_path / "out"
    result = run_legacy_case(case_dir, seed_index=1, output_dir=out_dir, max_trials=5)
    assert result.output_dir == out_dir
    assert (out_dir / "T.dat").exists()
    for name in ["A1.dat", "B1.dat", "C1.dat", "D1.dat", "E1.dat", "F1.dat", "G1.dat", "H1.dat", "I1.dat", "A2.dat", "H2.dat", "I2.dat"]:
        assert (out_dir / name).exists()
