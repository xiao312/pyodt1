# Validation harness

The main comparison tool is:

- `scripts/compare_one_step.py`

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

The script also compares the sampling pipeline for a seeded case covering:

- `BSeeds`
- `BLenProb`
- `BLength`
- sampled `L3`, `L`, and `M`
- final RNG state

This is especially valuable because it shows that Python is not merely reproducing downstream formulas for a hand-selected eddy; it is reproducing the same sampled candidate path.

## Usage

```bash
python scripts/compare_one_step.py
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
