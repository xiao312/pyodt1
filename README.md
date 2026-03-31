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
