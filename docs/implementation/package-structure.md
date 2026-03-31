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
  statistics.py
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
- `statistics.py` — `BStats`-style accumulation, `BSeries`-style centerline moments, `BChange` / `BSetOld` helpers, `BSnap`-style postprocessing, and `BWriteSeries`-style output helpers
- `solver.py` — one-step sampling, accepted-eddy application, `BLowerdt` / `BRaisedt` logic, realization runners including `nstat` / `ntseg` scheduling, and repeated-iteration aggregation
