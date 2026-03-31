# Package structure

```text
src/pyodt1/
  __init__.py
  acceptance.py
  advance.py
  config.py
  eddy_sampling.py
  rng.py
  solver.py
  state.py
  triplet.py
```

## Roles

- `config.py` — legacy input parsing and small config dataclasses
- `rng.py` — Fortran-compatible RNG path
- `advance.py` — deterministic advancement (`BAdv`, `BEqnStep`), initial-state generation, exponential waiting times
- `eddy_sampling.py` — eddy-size distribution, eddy-size sampling, location sampling, `BsKd`
- `acceptance.py` — acceptance probability
- `triplet.py` — triplet map and `c*K` increment
- `state.py` — state container
- `solver.py` — one-step sampling, accepted-eddy application, and an initial realization runner
