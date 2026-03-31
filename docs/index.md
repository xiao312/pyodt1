# pyodt1

Python reimplementation of the Basic ODT (`odt1`) package.

```{toctree}
:maxdepth: 2
:caption: Contents

getting-started
algorithms/overview
algorithms/legacy-fortran-mapping
algorithms/rng
algorithms/triplet-map
algorithms/eddy-sampling
algorithms/acceptance-probability
algorithms/accepted-eddy-update
implementation/package-structure
implementation/validation-harness
implementation/fortran-comparison
api/index
```

## Project status

This project is an in-progress Python reimplementation of the Basic ODT (`odt1`) Fortran code.

Currently validated against the original Fortran implementation for a minimal path including:

- legacy RNG seeding and state progression
- eddy-size distribution setup
- eddy-size sampling
- eddy-location sampling
- `BsKd`
- acceptance probability
- accepted-eddy update (`BEddy` path)

## Scope

The current focus is on:

1. making the core ODT algorithm readable in Python,
2. validating against the original Fortran code,
3. documenting algorithm and implementation details carefully.
