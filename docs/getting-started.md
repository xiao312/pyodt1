# Getting started

This page is for readers who want to understand, run, and extend `pyodt1`.

## What this project is

`pyodt1` is a Python reimplementation of the classic **Basic ODT** (`odt1`) code.

The current emphasis is not on immediately reproducing the entire legacy solver in one jump. Instead, the project is organized around a more reliable strategy:

1. port small but important algorithmic pieces,
2. validate them against the original Fortran,
3. document the mapping and the validation carefully,
4. then expand the implementation step by step.

This means the project is both a codebase and a teaching/validation effort.

## What you can do right now

At the current stage, you can:

- run the Python tests,
- inspect the package structure,
- run a direct Fortran-vs-Python comparison harness,
- read detailed algorithm notes in the documentation site.

## Environment setup with `uv`

Create and activate a virtual environment:

```bash
uv venv .venv
source .venv/bin/activate
```

Install the package in editable mode:

```bash
uv pip install -e .
```

Install development tools if needed:

```bash
uv pip install pytest jupyterlab ruff mypy
```

Install documentation dependencies:

```bash
uv pip install -r docs/requirements.txt
```

## Run tests

```bash
pytest -q
```

The test suite is currently used both for ordinary unit tests and for regression-style checks on algorithmic behavior.

## Run the comparison harness

The main validation entry point is:

```bash
python scripts/compare_one_step.py
```

If `gfortran` is available, the script will:

1. generate temporary Fortran drivers,
2. compile selected original `odt1` source files,
3. run them,
4. compare their outputs against the Python implementation.

If `gfortran` is not available, the script still prints the Python reference path, so it remains useful as a debugging tool.

## Build the docs locally

```bash
sphinx-build -b html docs docs/_build/html
```

Open:

```text
docs/_build/html/index.html
```

## Suggested reading order for new learners

If you are new to ODT or new to this package, a good sequence is:

1. [Algorithm overview](algorithms/overview.md)
2. [Legacy Fortran to Python mapping](algorithms/legacy-fortran-mapping.md)
3. [Legacy RNG](algorithms/rng.md)
4. [Triplet map](algorithms/triplet-map.md)
5. [Eddy sampling](algorithms/eddy-sampling.md)
6. [Acceptance probability](algorithms/acceptance-probability.md)
7. [Accepted eddy update](algorithms/accepted-eddy-update.md)
8. [Validation harness](implementation/validation-harness.md)

## Important current scope caveat

The current implementation validates a **minimal but important path**:

- legacy RNG,
- eddy-size distribution,
- eddy-size sampling,
- eddy-location sampling,
- `BsKd`,
- acceptance probability,
- accepted-eddy update.

This is already meaningful, but it is not yet the full `odt1` runtime loop.

That distinction matters. The project is already useful as a validated algorithmic reimplementation scaffold, but it is still under active expansion.
