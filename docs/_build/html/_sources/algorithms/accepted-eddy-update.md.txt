# Accepted eddy update

The accepted-eddy update currently covers the `BEddy` path.

## Steps

1. compute `uK`, `vK`, `wK`
2. compute `cu`, `cv`, `cw`
3. apply triplet map to `u`, `v`, `w`
4. apply `c*K` increments

## Python implementation

- `pyodt1.solver.OdtSolver.apply_eddy()`

## Related Fortran file

- `BEddy.f`

## Validation status

For the current fixture, Python and Fortran match exactly for:

- `cu`, `cv`, `cw`
- `u_after`
- `v_after`
- `w_after`
