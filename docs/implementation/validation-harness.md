# Validation harness

The main comparison tools are:

- `scripts/compare_one_step.py`
- `scripts/compare_advance.py`
- `scripts/compare_multi_trial.py`
- `scripts/compare_iterations.py`
- `scripts/compare_postprocessing.py`
- `scripts/compare_bsnap_intercomparison.py`

This script is central to the project because it turns the reimplementation effort from a qualitative translation exercise into a quantitative validation workflow.

## Why a harness is necessary

When reimplementing a legacy scientific code, it is easy to produce something that looks structurally similar while still differing numerically because of:

- RNG differences,
- indexing shifts,
- array-copy semantics,
- cumulative-distribution interpretation,
- small formula or unit mismatches.

The validation harness exists to expose those differences explicitly.

## Current comparison layers

## 1. Fixed accepted-eddy path

The script compares Python and Fortran for a fixed small fixture covering:

- `BsKd`
- `BProb`
- `BEddy`

This path verifies not only individual scalar quantities like `uk` or `pp`, but also the actual post-event velocity arrays.

## 2. Sampled eddy path

`compare_one_step.py` also compares the sampling pipeline for a seeded case covering:

- `BSeeds`
- `BLenProb`
- `BLength`
- sampled `L3`, `L`, and `M`
- final RNG state

This is especially valuable because it shows that Python is not merely reproducing downstream formulas for a hand-selected eddy; it is reproducing the same sampled candidate path.

## 3. Deterministic advancement and initialization path

`compare_advance.py` compares Python and Fortran for:

- `BAdv`
- `BEqnStep`
- `BExp`
- `BInitRun`
- `BInitIter`

## 4. `BLowerdt` and scheduled multi-trial realization behavior

`compare_multi_trial.py` compares Python and Fortran for:

- `BLowerdt`
- adaptive trial-time bookkeeping across multiple candidate eddies
- `nstat` / `ntseg` sub-interval scheduling
- centerline series accumulation via the `BSeries`-style path
- final state and RNG state after a reduced multi-trial realization

## 5. Repeated realizations and simplified statistics/output paths

`compare_iterations.py` compares Python and Fortran for:

- repeated `niter`-level scheduled realizations
- `BStats`-style `cstat` accumulation
- `BSeries` aggregation across realizations
- `BWriteSeries` time/variance output for the centerline series
- final RNG state after multiple realizations

## 6. Eddy/change statistics and richer postprocessing

`compare_postprocessing.py` compares Python and Fortran for:

- `BSetOld`
- `BChange`
- direct `BRecord`
- direct `XRecord` formatting
- original `BSnap` xmgrace-style output products on multiple controlled fixtures, including a second `istat` case
- patched-legacy `BSnap` intercomparison products on a controlled fixture

`compare_bsnap_intercomparison.py` is a dedicated intercomparison-mode comparison for the patched legacy `BSnap` / `BRecord` path.

`investigate_brecord.py` documents the compatibility pitfall: `BRecord` mutates `N`, so calling it with a literal constant can segfault under pass-by-reference semantics. Calling it with an integer variable works and matches the Python implementation.

`investigate_bsnap_intercomparison.py` documents the distinction between the unmodified and patched legacy paths: the original `BSnap` intercomparison mode (`ioptions(1)=0`) still crashes here, while the patched legacy path runs. The crash occurs at the negative-`N` header-writing convention used around `BRecord` in the unmodified source.

For day-to-day Python-side regression of full case output production, `pyodt1.legacy.run_legacy_case()` now emits the usual legacy file bundle and `fort.11`, which makes it easier to check orchestration-level behavior without relying on the crashing unmodified legacy intercomparison path.

## Usage

```bash
python scripts/compare_one_step.py
python scripts/compare_advance.py
python scripts/compare_multi_trial.py
python scripts/compare_iterations.py
python scripts/compare_postprocessing.py
python scripts/compare_bsnap_intercomparison.py
```

## Behavior with and without Fortran

### If `gfortran` is available
The script will:

1. generate temporary drivers,
2. compile selected original `odt1` Fortran files,
3. execute them,
4. parse the results,
5. print Python-vs-Fortran differences.

### If `gfortran` is not available
The script still runs in Python-only mode and prints the Python reference values. This keeps the project usable on machines without a local Fortran compiler.

## Why this matters for new contributors

The validation harness acts as the bridge between:

- the mathematical method,
- the legacy implementation,
- the new Python implementation.

For new contributors, it provides a practical answer to the question:

> How do I know this Python port is still faithful after I modify something?

The intended workflow is:

1. make a change,
2. run tests,
3. run the comparison harness,
4. inspect differences.

That workflow is one of the main reasons this project can evolve safely.
