# Eddy sampling

Eddy sampling is the stage where the algorithm decides what candidate eddy to test.

In the current `pyodt1` implementation, this includes:

1. building the eddy-size cumulative distribution,
2. sampling an eddy image size `L3`,
3. converting to the full eddy size `L = 3 * L3`,
4. sampling the leftmost eddy location `M`.

This page is important for new learners because it shows how ODT combines randomness with strong structural constraints.

## Why sample `L3` instead of `L` directly?

In the original code, the triplet map always splits the eddy interval into three equal images. Therefore the total eddy size `L` must be divisible by 3.

To make that natural, the code samples the image size:

```text
L3 = L / 3
```

and then reconstructs:

```text
L = 3 * L3
```

This makes the later triplet-map logic convenient and avoids invalid eddy lengths.

## Related Fortran files

The main Fortran references are:

- `BLenProb.f`
- `BLength.f`
- `BSampleEddy.f`

## Step 1 — Build the length distribution

The size distribution used in `odt1` is not arbitrary. It is constructed by `BLenProb.f`, which defines the allowed range of `I` values (where `I` corresponds to `L3`) and builds a cumulative distribution `PL(I)`.

In the current Python implementation, this corresponds to:

- `pyodt1.eddy_sampling.build_length_distribution()`

The result is stored as an `EddySizeDistribution` containing:

- `io` — lower allowed image size,
- `ip` — parameter shaping the distribution,
- `iv` — upper allowed image size,
- `co`, `cv` — helper quantities used for sampling,
- `pl` — the cumulative distribution array.

## Step 2 — Sample `L3`

Sampling is done by drawing a random number and using it to locate the smallest `L3` whose cumulative probability exceeds the draw.

The original `BLength.f` does this carefully:

- it uses a closed-form initial guess,
- then corrects that guess upward or downward until the cumulative distribution condition is satisfied.

This is implemented in Python as:

- `pyodt1.eddy_sampling.sample_length()`

The combination of closed-form guess + local correction is a nice example of a scientific code balancing mathematical structure and cheap discrete search.

## Step 3 — Compute `L`

Once `L3` is sampled, the eddy size is simply:

```text
L = 3 * L3
```

This is then used by the map and kernel routines.

## Step 4 — Sample `M`

The left boundary `M` is sampled uniformly over the allowed placements of the eddy interval.

In `BSampleEddy.f`, this is expressed so that the right boundary remains strictly inside the admissible indexed range. The details matter because the original code is written in a one-based index convention with specific assumptions about the physical interpretation of the end cells.

The Python port mirrors the same logic in:

- `pyodt1.eddy_sampling.sample_location()`

## Why this stage matters physically

The eddy-sampling stage encodes two important ideas:

1. **large and small eddies should not be equally likely**, and
2. **an eddy must fit into the current domain discretization**.

So this is not just “draw random indices.” It is structured random sampling constrained by the eddy model.

## Why this stage matters computationally

From a reimplementation perspective, this stage is also where subtle differences can appear quickly:

- RNG mismatch,
- one-based vs zero-based indexing,
- cumulative distribution indexing,
- off-by-one placement bounds.

These are exactly the kinds of differences that lead two implementations to drift apart even when the formulas look similar.

## Validation status

For the current seeded comparison fixture, Python and Fortran match exactly in:

- `L3`,
- `L`,
- `M`,
- final RNG state after the sampling path.

That is a strong validation result because it means the Python sampling path is following the original code closely enough to reproduce the same candidate eddy.

## Recommended mental model for new learners

A good way to think about eddy sampling is:

- `BLenProb` defines the admissible *population* of eddy sizes,
- `BLength` chooses one size from that population,
- location sampling chooses where that candidate lives,
- later steps determine whether that candidate is actually accepted.

So sampling defines the **proposal**, while the acceptance calculation defines the **filter**.
