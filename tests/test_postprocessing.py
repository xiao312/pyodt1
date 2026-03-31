import numpy as np

from pyodt1.state import OdtState
from pyodt1.statistics import (
    brecord_text,
    compute_snap_outputs,
    initialize_eddy_statistics,
    save_old_values,
    accumulate_change,
    write_snap_intercomparison,
    write_snap_xmgrace,
    xrecord_text,
)


def test_set_old_and_change_accumulate_expected_deltas(tmp_path):
    eddy = initialize_eddy_statistics(8, 1)
    before = OdtState(np.arange(8.0), np.arange(8.0) + 1.0, np.zeros(8))
    after = OdtState(before.u.copy(), before.v.copy(), before.w.copy())
    save_old_values(eddy, before, 2, 3)
    after.u[1:4] += 1.0
    after.v[1:4] += 2.0
    accumulate_change(eddy, after, 2, 3, 1, 0)
    assert np.allclose(eddy.edstat[1:4, 0, 0, 0], 1.0)
    assert np.allclose(eddy.edstat[1:4, 0, 1, 0], 2.0)
    assert eddy.edstat[0, 0, 3, 0] == 1.0


def test_brecord_and_xrecord_format():
    arr = np.array([1.0, 0.0, 2.5])
    btext = brecord_text(-3, arr)
    assert btext.startswith("    -3\n")
    assert "  1.0000000E+00" in btext
    xtext = xrecord_text(3, np.array([0.1, 0.2, 0.3]), arr)
    assert "  1.0000000E-01  1.0000000E+00" in xtext


def test_compute_snap_outputs_and_write_files(tmp_path):
    n = 6
    cstat = np.ones((n, 10, 1))
    cstat[:, 1, 0] = np.linspace(0.0, 0.5, n)
    cstat[:, 2, 0] = np.linspace(0.1, 0.6, n)
    cstat[:, 3, 0] = np.linspace(0.2, 0.7, n)
    cstat[:, 4, 0] = cstat[:, 1, 0] ** 2 + 0.01
    cstat[:, 5, 0] = cstat[:, 2, 0] ** 2 + 0.02
    cstat[:, 6, 0] = cstat[:, 3, 0] ** 2 + 0.03
    cstat[:, 7, 0] = 0.04
    cstat[:, 8, 0] = 0.05
    cstat[:, 9, 0] = 0.06
    edstat = np.zeros((n, 4, 4, 1))
    edstat[:, 0, 0, 0] = 0.01
    edstat[:, 1, 0, 0] = 0.02
    edstat[:, 2, 0, 0] = 0.03
    edstat[:, 3, 0, 0] = 0.04
    edstat[0, 0, 3, 0] = 2.0
    snap = compute_snap_outputs(n, np.zeros(n), np.zeros(n), np.zeros(n), 1.0, 1.0e-5, 1, edstat, cstat)
    assert snap.mean_u.shape == (n,)
    assert snap.variances.shape == (3, n)
    write_snap_intercomparison(tmp_path, 1, snap)
    write_snap_xmgrace(tmp_path, 1, snap)
    assert (tmp_path / "A1.dat").exists()
    assert (tmp_path / "D1.dat").exists()
    assert (tmp_path / "H1.dat").exists()
    assert (tmp_path / "I1.dat").exists()
