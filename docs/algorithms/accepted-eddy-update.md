# Accepted eddy update

This page describes what happens after a candidate eddy has already been sampled and accepted.

For new learners, this is the point where the algorithm becomes visibly dynamical: the state arrays are actually changed.

## Related Fortran file

Primary upstream reference:

- `BEddy.f`

Python implementation:

- `pyodt1.solver.OdtSolver.apply_eddy()`

## Overview

Once an eddy is accepted, the current validated path applies the following steps:

1. compute `uK`, `vK`, `wK`,
2. compute `cu`, `cv`, `cw`,
3. triplet-map `u`, `v`, `w`,
4. apply `c*K` increments to each mapped velocity component.

## Step 1 — Kernel values

The kernel values `uK`, `vK`, and `wK` come from `BsKd` and summarize the interaction between the mapped field and the triplet-map displacement geometry.

These quantities are central because they feed both:

- the acceptance probability, and
- the accepted-eddy velocity correction.

So the kernel is one of the main algorithmic bridges between “candidate eddy strength” and “state update.”

## Step 2 — Coefficient construction

The `BEddy.f` routine computes coefficients `cu`, `cv`, and `cw` from the kernels.

The expression includes:

- the discrete correction factor,
- the eddy size `L`,
- a root involving the combined kernel magnitude.

In the Python port, this logic is reproduced in:

- `OdtSolver._compute_c_coefficients()`

## Step 3 — Triplet map

After computing the coefficients, the velocity arrays are triplet-mapped over the accepted interval.

This rearrangement is performed first, before the `c*K` increment is added.

That order matters: the update is not “add then map,” but rather “map then add.”

## Step 4 — Add `c*K`

After mapping, the code applies the geometric correction field encoded by `K` and scaled by the component-specific coefficient.

This is what `BAddK.f` and `pyodt1.triplet.add_k()` implement.

## Why this update is interesting

For a new reader, the accepted-eddy update is where ODT becomes more than a passive rearrangement model.

If the code only triplet-mapped scalar values, one could think of it as a generic stirring operator. But the `BEddy` path shows that the velocity field receives a more structured update linked to the kernel measures and the eddy geometry.

That makes the update feel much closer to a compact model of turbulent event dynamics rather than a purely decorative reshuffling.

## Current validation status

For the present fixed fixture, Python and Fortran match exactly for:

- `cu`, `cv`, `cw`,
- `u_after`,
- `v_after`,
- `w_after`.

This is significant because it validates the complete currently implemented accepted-eddy state update for that path.

## Where this sits in the bigger algorithm

A useful mental sequence is:

1. sample candidate eddy,
2. compute kernels,
3. compute acceptance probability,
4. accept or reject,
5. if accepted, apply the `BEddy` path.

So the accepted-eddy update is not a separate detached routine. It is the final stage of the currently validated event mechanism.
