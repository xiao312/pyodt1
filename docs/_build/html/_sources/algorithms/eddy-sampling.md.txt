# Eddy sampling

## Components

The sampled eddy path currently includes:

1. eddy-size distribution construction
2. eddy-size sampling
3. eddy-location sampling

## Python implementation

- `pyodt1.eddy_sampling.build_length_distribution()`
- `pyodt1.eddy_sampling.sample_length()`
- `pyodt1.eddy_sampling.sample_location()`

## Related Fortran files

- `BLenProb.f`
- `BLength.f`
- `BSampleEddy.f`

## Validation status

For the tested seeded case, Python and Fortran match exactly in:

- `L3`
- `L`
- `M`
- final RNG state after the sampling path
