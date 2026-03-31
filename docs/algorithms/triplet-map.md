# Triplet map

The triplet map is one of the signature ideas in ODT.

If a new reader wants to understand *what makes ODT look like ODT*, the triplet map is a good place to start.

## Intuition

Imagine taking a contiguous interval of the solution field and compressing it into three copies placed back into the same interval:

1. a left image,
2. a middle image that is reversed,
3. a right image.

That operation creates local folding and sharpening while staying entirely one-dimensional. The reversed middle image is important because it introduces a notion of inversion/folding rather than mere copying.

In ODT, this serves as a stylized representation of turbulent stirring.

## Discrete version in `odt1`

The original `odt1` code uses a **discrete triplet map** on cell-indexed arrays.

Relevant Fortran files:

- `BTriplet.f`
- `BAddK.f`

The map is applied over an interval:

- left index `M`
- length `L`

with the constraint that `L` is divisible by 3.

The interval is decomposed into three images of length:

```text
Lo = L / 3
```

The Fortran implementation explicitly gathers the values for the three images and writes them back in mapped order.

## Python implementation

The Python implementation lives in:

- `pyodt1.triplet.triplet_map()`

Its job is to preserve the indexing logic of the Fortran routine while expressing it in clearer Python/Numpy code.

The function accepts:

- a 1D array,
- a zero-based start index,
- a segment length divisible by 3.

## The `add_k` companion operation

The triplet map is only half of the accepted-eddy velocity update.

After mapping the velocity fields, the algorithm applies a correction term of the form:

```text
c * K
```

where `K` depends on the displacement geometry of the triplet-map images.

This is implemented in Python as:

- `pyodt1.triplet.add_k()`

and corresponds to the Fortran routine:

- `BAddK.f`

So, operationally, the accepted velocity update is:

1. triplet-map the field,
2. apply the `c*K` increment.

## Why the triplet map is useful in a reduced model

The triplet map is attractive because it is:

- local,
- discrete,
- conservative in a structured sense,
- easy to apply repeatedly,
- capable of generating steep local gradients and folded structure.

This gives ODT a compact way to represent stirring events without solving a full multidimensional flow field.

## Implementation caution: indexing matters

The triplet map is simple conceptually but very sensitive to indexing.

During reimplementation, one of the main hazards is accidentally changing:

- one-based vs zero-based indexing,
- which element enters the reversed middle image,
- whether the operation reads from the original array or partially updated output.

For faithful reproduction, the Python implementation must mirror the Fortran data movement exactly.

## Validation status

For the currently tested fixture, Python and Fortran match exactly for:

- mapped arrays after accepted eddy update,
- the post-map `c*K` adjustment path.

That means the current discrete triplet-map and `add_k` logic are validated for the tested case.

## What new learners should take away

The most important takeaway is this:

> In ODT, the triplet map is the discrete stirring operator.

Once you internalize that idea, much of the rest of the algorithm becomes easier to parse:

- eddy sampling decides **where** and **how large** the stirring event is,
- acceptance probability decides **whether it occurs**,
- the triplet map and `c*K` logic determine **how the state changes if it does occur**.
