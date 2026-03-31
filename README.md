# pyodt1

Python reimplementation workspace for `odt1` (Basic ODT by Alan R. Kerstein).

## Environment

Create and activate the environment:

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e .
uv pip install pytest jupyterlab ruff mypy
```

Or, if using the already prepared environment in this workspace:

```bash
source .venv/bin/activate
```

## Upstream references

- `external/odt1/` — <https://github.com/rmcdermo/odt1>
- `external/BYUignite-ODT/` — <https://github.com/BYUignite/ODT>

## Goal

Reimplement the core `odt1` package in Python with emphasis on:

1. clarity of the core ODT algorithm,
2. testability,
3. reproducibility,
4. later comparison against `odt1` and `BYUignite/ODT`.

## Documentation

Project documentation is published at:

- <https://xiao312.github.io/pyodt1/>

This repo includes a Sphinx + MyST + Furo documentation scaffold under `docs/`.

Build locally with:

```bash
source .venv/bin/activate
pip install -r docs/requirements.txt
sphinx-build -b html docs docs/_build/html
```

The site is set up for deployment to GitHub Pages with GitHub Actions.

## Fortran comparison harnesses

Use these to validate Python ports against the original `odt1` Fortran:

```bash
source .venv/bin/activate
python scripts/compare_one_step.py
python scripts/compare_advance.py
python scripts/compare_multi_trial.py
python scripts/compare_iterations.py
python scripts/compare_postprocessing.py
```

- `compare_one_step.py` covers the core sampled/accepted eddy path.
- `compare_advance.py` covers deterministic advancement, initialization, and exponential waiting-time sampling.
- `compare_multi_trial.py` covers `BLowerdt` and a reduced multi-trial `Bodt`-style scheduled realization.
- `compare_iterations.py` covers repeated realizations plus simplified `BStats` / `BSeries` / `BWriteSeries`-style behavior.
- `compare_postprocessing.py` covers `BSetOld`, `BChange`, direct `BRecord`, direct `XRecord`, and `BSnap` xmgrace-style outputs on multiple fixtures.

BRecord note: the original Fortran routine mutates `N` (`N=abs(N)`), so calling it with a literal such as `call BRecord(61,3,s)` segfaults under the local toolchain because the routine writes through a by-reference constant argument. Calling it with an integer variable works, and `BRecord` is now direct-runtime validated that way. See `scripts/investigate_brecord.py`.

BSnap note: the original xmgrace path (`ioptions(1)=1`) is direct-runtime validated here. The original intercomparison path (`ioptions(1)=0`) currently segfaults under the local toolchain; see `scripts/investigate_bsnap_intercomparison.py`.
