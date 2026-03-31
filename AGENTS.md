# AGENTS.md

Project instructions for coding agents working in this repository.

## Validation policy

When implementing or modifying any Python functionality intended to reproduce legacy `odt1` Fortran behavior:

1. **Run direct Fortran-vs-Python comparisons for the new piece whenever practical.**
2. Do **not** describe a feature as validated against the original code unless the Fortran path was actually compiled and executed.
3. If a new piece is only ported-from-source but not yet cross-checked, state that explicitly.
4. Prefer adding or extending reproducible comparison harnesses under `scripts/`.
5. If the original Fortran routine crashes under the available toolchain, document that explicitly, add a minimal reproducer when possible, and do not over-claim validation.
6. Check whether a crash is due to an invalid call pattern before concluding the routine itself is incompatible (for example, passing a literal to a routine that mutates a by-reference argument).

## Current comparison harnesses

- `scripts/compare_one_step.py` — validated core eddy path
- `scripts/compare_advance.py` — deterministic advancement / initialization path
- `scripts/compare_multi_trial.py` — `BLowerdt` and reduced multi-trial scheduling path
- `scripts/compare_iterations.py` — repeated realizations and simplified statistics/output path
- `scripts/compare_postprocessing.py` — `BSetOld`, `BChange`, `XRecord`, and `BSnap` xmgrace-style postprocessing path

## Workflow expectation

For new algorithmic ports:

- implement the Python version,
- add/update tests,
- run the matching Fortran comparison harness,
- only then claim parity for that feature.
