# Legacy RNG

The Python reimplementation includes a direct port of the legacy `Brng` random-number generator used by `odt1`.

## Why this matters

Matching the original RNG is important for:

- deterministic comparison of sampled eddy sizes and locations
- exact validation of one-step behavior
- later reproducibility for longer run sequences

## Related Fortran files

- `Brng.f`
- `BSeeds.f`
- `BrngGet.f`
- `BrngPut.f`

## Python implementation

- `pyodt1.rng.OdtRNG`

## Current validation status

For the tested fixture and seed setup, Python and Fortran match in:

- sampled `L3`
- sampled `L`
- sampled `M`
- final RNG state `(i1, i2)`
