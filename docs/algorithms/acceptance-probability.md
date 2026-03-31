# Acceptance probability

Acceptance probability is the point where a sampled candidate eddy becomes either a real event or a discarded proposal.

This page is one of the most important places for new learners because it connects:

- the sampled eddy geometry,
- the velocity kernels,
- the size-distribution bookkeeping,
- the actual event rate used by the model.

## Related Fortran file

Primary upstream reference:

- `BProb.f`

Python implementation:

- `pyodt1.acceptance.acceptance_probability()`

## Conceptual role

The algorithm first proposes an eddy by sampling:

- an image size `L3`,
- a full size `L = 3 * L3`,
- a location `M`.

But not every proposed eddy should occur.

The acceptance probability `pp` decides whether this candidate eddy is dynamically plausible enough to be realized as an event at the current step.

In other words:

- sampling defines the candidate population,
- acceptance probability determines the actual occurrence rate.

## Inputs to the formula

The current implementation uses:

- `nmesh`
- `l3`
- `dt`
- `pl`
- `ratefac`
- `viscpen`
- `u_kernel`
- `v_kernel`
- `w_kernel`

The kernel quantities come from `BsKd` and summarize the eddy-relevant structure of the velocity fields over the candidate interval.

## Structure of the Fortran formula

At a high level, the Fortran expression computes something proportional to:

1. an event-rate factor,
2. a kernel-based measure of eddy strength,
3. the trial timestep `dt`,
4. the inverse probability of having sampled the chosen size and location.

That last point is subtle but important. The candidate eddies are sampled from a proposal distribution, not from the final event distribution itself. So the acceptance formula compensates for that proposal mechanism.

## Discrete correction factor

One detail in `BProb.f` that new learners should notice is the factor:

```text
disfac = 1 - 3 / L
```

This corrects for the fact that the discrete triplet map does not reproduce the continuum mean-square displacement exactly. The code therefore rescales the event-rate expression so that the discrete and continuum transport interpretations remain more consistent.

This is a good example of a scientific implementation detail that is easy to miss if one only reads the method description at a high level.

## The role of `PL`

The acceptance formula depends on the probability of sampling the chosen `L3`, which is extracted from the cumulative size distribution `PL`.

In Fortran this appears as:

```text
PL(L3) - PL(L3-1)
```

That quantity is the probability mass associated with the selected image-size bin.

## Important indexing note

A key bug during the Python port came from translating this line incorrectly.

Because Fortran uses one-based indexing and Python uses zero-based indexing, storing the same cumulative values in a Python array means that the correct translation is:

```python
pl[l3 - 1] - pl[l3 - 2]
```

not:

```python
pl[l3] - pl[l3 - 1]
```

This was not a cosmetic issue. It changed the size-bin probability used in the denominator and produced a measurable mismatch in `pp` until it was corrected.

That debugging episode is useful pedagogically because it shows how even a clean mathematical port can fail if array semantics are translated incorrectly.

## Python implementation notes

The current Python implementation is intentionally compact, but it follows the same logic as the validated Fortran path.

The implementation:

- reconstructs `L` from `L3`,
- computes the kernel norm term,
- applies the viscous penalty,
- applies the discrete correction factor,
- divides by the sampled size-bin probability,
- includes the location-sampling compensation,
- multiplies by `dt`.

## Validation status

For the current fixed comparison fixture, Python and Fortran now match exactly for `pp`.

That is an important milestone because `pp` is where several independently ported pieces meet:

- kernel computation,
- size-distribution construction,
- indexing conventions,
- discrete-event scaling.

Exact agreement here therefore increases confidence in the whole currently implemented path.

## What new learners should remember

The most useful summary is:

> Acceptance probability is not just a random filter. It is the mechanism that converts a sampled candidate eddy into the correct event-rate-weighted discrete ODT event.

Understanding that idea makes the rest of the ODT event pipeline much easier to interpret.
