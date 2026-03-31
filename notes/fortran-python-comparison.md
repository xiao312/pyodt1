# Minimal Fortran-vs-Python comparison harness

## Purpose

Compare the Python `pyodt1` reimplementation against selected original `odt1` Fortran subroutines for a single fixed eddy sample / accepted eddy step.

## Current scope

The harness compares:
- `BsKd`
- `BProb`
- `BEddy`

for a small hard-coded fixture.

## Script

Run:

```bash
source .venv/bin/activate
python scripts/compare_one_step.py
```

## Behavior when no Fortran compiler is installed

The script **does not fail** if `gfortran` is missing.
Instead it:
- computes and prints the Python reference result
- reports that Fortran comparison was skipped

This is intentional so the project remains usable on machines without local Fortran tooling.

## When a Fortran compiler is available

If `gfortran` is on `PATH`, the script will:
1. generate a temporary fixed-form Fortran driver,
2. compile the required `odt1` source files,
3. run the executable,
4. parse the generated JSON-like output,
5. report scalar and array differences vs Python.

## Requirement

A local Fortran compiler is helpful for direct validation, but **not required** for continued Python implementation.

Without Fortran installed, we can still:
- continue the port,
- build tests,
- prepare the harness,
- later run validation on another machine/container/CI environment that has `gfortran`.
