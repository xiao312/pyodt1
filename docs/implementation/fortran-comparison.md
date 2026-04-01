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
- direct `BRecord`
- direct `XRecord`
- original `BSnap` xmgrace-style output products on multiple controlled fixtures, including a second `istat` case
- patched-legacy `BSnap` intercomparison products on a controlled fixture
- dedicated patched-legacy `BSnap` intercomparison comparison via `scripts/compare_bsnap_intercomparison.py`

The smaller helper/config compatibility comparison shows agreement for:

- `BReadOptions`
- `BReadPars`
- `BReadConfig`
- `BInitStats`
- `BAddTerm`
- `BrngGet` / `BrngPut`

## Scope caveat

This still does **not** yet imply full equivalence with the original `odt1` solver. However, the validated scope now includes:

- the minimal sampled/accepted eddy path,
- deterministic advancement and initialization,
- a reduced but faithful multi-trial realization schedule.

`BRecord` compatibility has now been investigated: the crash was caused by passing a literal argument to a routine that mutates `N` via `N=abs(N)`. Under Fortran pass-by-reference semantics, writing through a constant argument can segfault. A minimal reproducer is provided in `scripts/investigate_brecord.py`. When called correctly with an integer variable, `BRecord` runs and matches the Python implementation.

A separate caveat remains for the **original unmodified** `BSnap` intercomparison mode (`ioptions(1)=0`): a minimal reproducer in `scripts/investigate_bsnap_intercomparison.py` shows that this path segfaults under the local toolchain, while the patched legacy intercomparison path and the original xmgrace mode (`ioptions(1)=1`) run and match the Python implementation. The failure is tied to the negative-`N` header-writing convention around `BRecord` in the original intercomparison path. The external legacy sources in this repository have therefore been minimally patched to preserve the intended output semantics while avoiding the in-place negative-`N` mutation.

At the program-orchestration level, `pyodt1.legacy.run_legacy_case()` now reproduces the usual legacy output bundle more closely by writing `T.dat`, the selected mode's `A*`–`I*` files (including empty placeholders for unused legacy file slots), and a `fort.11` progress log. This narrows the remaining gap to exact line-for-line `Bodt.f` procedural parity rather than missing output products.

For a precise record of the vendored Fortran source changes, see [Legacy source patches](legacy-patches.md).
