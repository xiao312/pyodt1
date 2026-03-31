# Python reimplementation plan for odt1

## Immediate objective

Build a readable Python version of the core `odt1` algorithm before attempting feature parity.

## Scope for first implementation

### Phase 1
- input model for core scalar/integer parameters
- fixed-grid state container
- RNG wrapper
- triplet map
- eddy size sampling
- eddy location sampling
- acceptance probability calculation
- one realization loop skeleton

### Phase 2
- advection / advancement logic matching `odt1`
- statistics recording
- file-compatible input parsing for `BConfig.dat`, `BOptions.dat`, `BPars.dat`
- comparison tests against simple hand-worked cases

### Phase 3
- numerical comparison against original Fortran outputs
- improved API
- optional plotting and notebook demos

## Suggested Python package modules

```text
src/pyodt1/
  __init__.py
  config.py
  state.py
  rng.py
  triplet.py
  eddy_sampling.py
  acceptance.py
  solver.py
  io_legacy.py
  stats.py
```

## First milestone

Achieve a tested Python implementation of:
- triplet mapping,
- eddy size/location sampling,
- a minimal one-step candidate eddy evaluation.
