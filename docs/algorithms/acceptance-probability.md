# Acceptance probability

Acceptance probability is computed from the sampled eddy size, sampled location, kernel measures, and eddy-size probability distribution.

## Python implementation

- `pyodt1.acceptance.acceptance_probability()`

## Related Fortran file

- `BProb.f`

## Important indexing note

A key bug during porting came from translating Fortran 1-based indexing of `PL` into Python 0-based indexing.

In Fortran:

```text
PL(L3) - PL(L3-1)
```

In Python, with the same values stored in zero-based form, the correct mapping is:

```python
pl[l3 - 1] - pl[l3 - 2]
```

This indexing fix was required to obtain exact agreement with the original Fortran `pp` value.
