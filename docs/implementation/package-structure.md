# Package structure

```text
src/pyodt1/
  __init__.py
  acceptance.py
  advance.py
  config.py
  eddy_sampling.py
  legacy.py
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
- `statistics.py` — `BStats`-style accumulation, `BSeries`-style centerline moments, `BChange` / `BSetOld` helpers, `BSnap`-style postprocessing, legacy text writers, and parser/regression helpers for generated output files
- `legacy.py` — compatibility wrappers for small legacy helpers (`BReadOptions`, `BInitStats`, `BAddTerm`, `BrngGet`, `BrngPut`) plus a legacy-style end-to-end case runner that writes `T.dat`, the expected `A*`–`I*` file bundle, and `fort.11`
- `solver.py` — one-step sampling, accepted-eddy application, `BLowerdt` / `BRaisedt` logic, realization runners including `nstat` / `ntseg` scheduling, and repeated-iteration aggregation
