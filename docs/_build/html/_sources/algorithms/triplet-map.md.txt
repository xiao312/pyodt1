# Triplet map

The triplet map is one of the central operations in ODT.

## Current Python implementation

- `pyodt1.triplet.triplet_map()`
- `pyodt1.triplet.add_k()`

## Related Fortran files

- `BTriplet.f`
- `BAddK.f`

## Validated behavior

For the current fixed fixture, Python and Fortran match exactly for:

- mapped velocity arrays after the accepted eddy update
- post-map `c*K` updates applied to `u`, `v`, and `w`
