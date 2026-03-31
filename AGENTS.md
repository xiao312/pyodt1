# AGENTS.md

Project instructions for coding agents working in this repository.

## Validation policy

When implementing or modifying any Python functionality intended to reproduce legacy `odt1` Fortran behavior:

1. **Run direct Fortran-vs-Python comparisons for the new piece whenever practical.**
2. Do **not** describe a feature as validated against the original code unless the Fortran path was actually compiled and executed.
3. If a new piece is only ported-from-source but not yet cross-checked, state that explicitly.
4. Prefer adding or extending reproducible comparison harnesses under `scripts/`.

## Current comparison harnesses

- `scripts/compare_one_step.py` — validated core eddy path
- `scripts/compare_advance.py` — deterministic advancement / initialization path

## Workflow expectation

For new algorithmic ports:

- implement the Python version,
- add/update tests,
- run the matching Fortran comparison harness,
- only then claim parity for that feature.
