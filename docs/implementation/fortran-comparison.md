# Fortran comparison status

## Current status

The current fixed fixture comparison shows exact agreement between Python and Fortran for:

- `uk`
- `vk`
- `wk`
- `pp`
- `cu`
- `cv`
- `cw`
- `u_after`
- `v_after`
- `w_after`

The seeded sampling comparison also shows exact agreement for:

- `L3`
- `L`
- `M`
- final RNG state

## Scope caveat

This does **not** yet imply full equivalence with the original `odt1` solver. It validates the currently implemented minimal eddy sampling and accepted-eddy update path.
