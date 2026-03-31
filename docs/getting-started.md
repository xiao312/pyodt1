# Getting started

## Environment

Create and activate a virtual environment with `uv`:

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e .
uv pip install sphinx myst-parser furo
```

## Run tests

```bash
pytest -q
```

## Run the Fortran-vs-Python comparison harness

```bash
python scripts/compare_one_step.py
```

If `gfortran` is available, the script will compile a temporary driver and compare Python and Fortran outputs directly.

## Build docs locally

```bash
sphinx-build -b html docs docs/_build/html
```

Then open:

```text
docs/_build/html/index.html
```
