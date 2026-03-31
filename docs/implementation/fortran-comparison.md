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

The repeated-realization statistics/output comparison shows agreement for:

- `niter`-level repeated scheduled realizations
- `BStats`-style `cstat` accumulation
- `BSeries` aggregation across realizations
- `BWriteSeries` time/variance output
- final RNG state after multiple realizations

The postprocessing/change-statistics comparison shows agreement for:

- `BSetOld`
- `BChange`
- direct `XRecord`
- `BSnap` xmgrace-style output products on a controlled fixture

## Scope caveat

This still does **not** yet imply full equivalence with the original `odt1` solver. However, the validated scope now includes:

- the minimal sampled/accepted eddy path,
- deterministic advancement and initialization,
- a reduced but faithful multi-trial realization schedule.

The remaining caveat is the standalone `BRecord` routine: it is implemented in Python, but the original Fortran routine segfaults under the local `gfortran` toolchain in this environment, so direct runtime validation of `BRecord` itself is still pending. Aside from that toolchain-specific issue, the broader `BChange` / `BSnap` / `XRecord` postprocessing path is now represented and cross-checked on controlled fixtures.
