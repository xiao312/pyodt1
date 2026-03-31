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

The deterministic advancement and initialization comparison shows exact or near-machine-precision agreement for:

- `BAdv`
- `BEqnStep`
- `BInitRun`
- `BInitIter`
- `BExp` RNG state and waiting-time behavior

The reduced multi-trial scheduling comparison shows agreement for:

- `BLowerdt`
- multi-trial `dt` / `td` adaptation
- `nstat` / `ntseg` sub-interval scheduling
- centerline series accumulation
- final state arrays and final RNG state

## Scope caveat

This still does **not** yet imply full equivalence with the original `odt1` solver. However, the validated scope now includes:

- the minimal sampled/accepted eddy path,
- deterministic advancement and initialization,
- a reduced but faithful multi-trial realization schedule.

Statistics/output routines such as the full `BSnap` / `BWriteSeries` production path are still only partially represented in Python.
