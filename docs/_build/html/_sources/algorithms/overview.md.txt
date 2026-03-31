# Algorithm overview

`pyodt1` currently focuses on the minimal ODT path needed to validate the Python reimplementation against the original Fortran `odt1` code.

## Current validated path

1. initialize legacy RNG state
2. build eddy-size cumulative distribution
3. sample eddy image size `L3`
4. compute eddy size `L = 3 * L3`
5. sample eddy location `M`
6. compute kernels `uK`, `vK`, `wK`
7. compute acceptance probability `pp`
8. if accepted, apply triplet map and `c*K` update to velocity fields

## Main modules

- `pyodt1.rng`
- `pyodt1.config`
- `pyodt1.eddy_sampling`
- `pyodt1.acceptance`
- `pyodt1.triplet`
- `pyodt1.solver`
