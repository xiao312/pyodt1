# Legacy RNG

A surprising amount of validation effort in numerical reimplementation work comes down to random numbers.

In `pyodt1`, the random-number generator is not an incidental utility. It is part of the algorithmic definition of the original code path. If the Python reimplementation uses a different RNG, even a high-quality modern one, then sampled eddy sizes, eddy locations, and later event sequences will differ from the original Fortran execution. That makes debugging and validation much harder.

For this reason, `pyodt1` includes a direct port of the legacy `odt1` random-number generator.

## Why match the original RNG?

When reimplementing an algorithmic code, there are usually two phases:

1. **algorithm validation** — make sure the Python code follows the original implementation exactly enough to reproduce its behavior,
2. **possible modernization** — later decide whether to keep or replace parts of the implementation.

For phase 1, using the same RNG is extremely valuable because it lets us ask precise questions such as:

- Did Python sample the same eddy image size `L3` as Fortran?
- Did Python sample the same eddy location `M`?
- After those draws, is the internal RNG state the same?

If the answer is yes, then discrepancies later in the algorithm can be localized much more quickly.

## Related Fortran files

The relevant upstream files are:

- `Brng.f`
- `BSeeds.f`
- `BrngGet.f`
- `BrngPut.f`

These define:

- the core uniform RNG recurrence,
- the seed-table-based initialization path,
- functions for reading and restoring RNG state.

## Python implementation

The Python implementation is:

- `pyodt1.rng.OdtRNG`

It supports two initialization modes:

### 1. Seed-table mode

```python
from pyodt1.rng import OdtRNG

rng = OdtRNG(seed_index=1)
```

This reproduces the behavior of the Fortran `BSeeds.f` logic:

- choose a seed pair from the legacy table,
- warm up the generator by drawing 100 values.

### 2. Explicit state mode

```python
rng = OdtRNG(i1=123456789, i2=362436069)
```

This is useful for tests and debugging where we want exact control over the internal state.

## The generator itself

The Fortran code uses a specific integer recurrence and combines two internal seed values `i1` and `i2` into one returned uniform random value.

The Python port intentionally preserves:

- the integer arithmetic structure,
- the state updates,
- the final scaling constant,
- the exclusive `(0, 1)`-style behavior of the returned values.

This is not primarily about claiming the legacy RNG is the ideal RNG for future scientific production work. It is about preserving comparability with the original implementation during the reimplementation phase.

## State access

The Python wrapper provides:

```python
state = rng.get_state()
rng.put_state(*state)
```

These mirror the spirit of the original `BrngGet.f` and `BrngPut.f` routines.

This functionality is especially useful in debugging because it lets us freeze the RNG state before a step, replay the same step, and compare Python and Fortran more precisely.

## Validation status

For the current seeded sampling comparison, Python and Fortran match exactly in:

- sampled `L3`,
- sampled `L`,
- sampled `M`,
- final RNG state `(i1, i2)`.

That is a strong indicator that the RNG path is correctly ported for the currently tested workflow.

## Why this matters pedagogically

For new learners, the RNG page is important because it shows a general lesson that applies far beyond ODT:

> Reimplementing a stochastic scientific code is not only about the formulas. It is also about reproducing the stochastic control path closely enough that later differences are interpretable.

In many scientific codes, matching the RNG behavior early is one of the fastest ways to make the entire validation process tractable.
