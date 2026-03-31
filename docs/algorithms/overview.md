# Algorithm overview

This page is intended as a first technical orientation for new readers.

`pyodt1` is a Python reimplementation of the classic **Basic ODT** code (`odt1`), where **ODT** stands for **One-Dimensional Turbulence**. The original idea is to represent some of the essential effects of turbulent stirring on a one-dimensional line while still resolving transport and scalar structure in physical space along that line.

For readers coming from conventional CFD, ODT can feel unusual at first because it does **not** solve a full 3D turbulence field. Instead, it alternates between:

1. **deterministic evolution** of fields on a 1D mesh, and
2. **stochastic eddy events** that instantaneously rearrange the fields using a triplet map.

That combination is the core of the method.

## Why ODT exists

The practical motivation behind ODT is that fully resolved turbulent reacting-flow simulation is expensive. DNS resolves the full spatial field and the full cascade, but that cost quickly becomes prohibitive. ODT offers a compromise:

- keep a **real spatial line** on which sharp scalar and velocity structure can exist,
- model turbulent stirring with **discrete stochastic events**,
- preserve a mechanistic connection between eddy size, eddy rate, and transport.

This makes ODT much cheaper than DNS while still retaining nontrivial structure in the transported fields.

## High-level picture of one ODT step

At the most abstract level, the minimal path currently implemented and validated in `pyodt1` is:

1. initialize a legacy pseudo-random number generator,
2. build a cumulative distribution for allowed eddy sizes,
3. sample an eddy image size `L3`,
4. convert it to a full eddy size `L = 3 * L3`,
5. sample a left boundary `M` for that eddy,
6. compute eddy kernels `uK`, `vK`, `wK`,
7. compute the eddy acceptance probability `pp`,
8. if accepted, apply the triplet map and velocity-kernel correction.

This sequence is already validated against the original Fortran implementation for the current fixture cases.

## The main conceptual ingredients

## 1. A one-dimensional state

The current state is a 1D collection of velocity component arrays:

- `u`
- `v`
- `w`

stored in an `OdtState`.

In the original `odt1`, these are cell-centered arrays on a uniform or effectively index-based mesh. In the Python reimplementation, we currently focus on reproducing the discrete algorithmic path rather than extending the physical model.

## 2. Stochastic eddies

An eddy is characterized by:

- a size `L` measured in mesh cells,
- a location `M`, also expressed in mesh-cell indexing,
- a probability of being accepted.

Not every candidate eddy is accepted. The algorithm samples candidates from prescribed distributions and then filters them using a physically motivated acceptance probability.

## 3. Triplet map stirring

If an eddy is accepted, the state is rearranged by a **triplet map** over the selected interval. The triplet map compresses the interval into three copies, reverses the middle copy, and writes those mapped values back to the original interval.

This gives a compact, discrete representation of stirring and folding.

## 4. Kernel-based velocity correction

The triplet map alone is not the full story for the velocity field. After mapping the velocity components, the algorithm adds a correction of the form `c*K`, where the coefficients are computed from the kernel measures `uK`, `vK`, and `wK`.

This is implemented in the `BEddy` path and is one of the most important places where ODT goes beyond simple rearrangement.

## How `pyodt1` is organized

The current Python package is split into small modules that mirror the original Fortran structure while staying readable:

- `pyodt1.rng` — legacy RNG and seed handling
- `pyodt1.config` — legacy input parsing and lightweight config containers
- `pyodt1.eddy_sampling` — size distribution, size sampling, location sampling, `BsKd`
- `pyodt1.acceptance` — acceptance probability
- `pyodt1.triplet` — triplet map and `c*K` increment helper
- `pyodt1.state` — 1D state container
- `pyodt1.solver` — minimal sampling and one-step accepted-eddy application

## What is validated right now

At the moment, the project is intentionally modest in scope and precise in validation claims.

The following are currently validated against the original `odt1` Fortran code for the present fixtures:

- legacy RNG seeding and progression,
- eddy-size distribution setup,
- eddy-size sampling,
- eddy-location sampling,
- `BsKd`,
- acceptance probability,
- accepted eddy update through the `BEddy` path.

That means the currently implemented **minimal eddy sampling and accepted-eddy path** is no longer only a conceptual translation — it is numerically cross-checked against the original code.

## What is not yet complete

New learners should also understand the current limits of the package.

`pyodt1` is **not yet** a full end-to-end reproduction of `Bodt.f`. In particular, the broader runtime loop, deterministic advancement path, and full statistics/output machinery are not yet all ported.

So a good mental model is:

- `pyodt1` already has a validated core eddy mechanism,
- but it is still growing toward a fuller solver.

## How to read the rest of the docs

A useful reading order for new learners is:

1. this page
2. [Legacy Fortran to Python mapping](legacy-fortran-mapping.md)
3. [Legacy RNG](rng.md)
4. [Triplet map](triplet-map.md)
5. [Eddy sampling](eddy-sampling.md)
6. [Acceptance probability](acceptance-probability.md)
7. [Accepted eddy update](accepted-eddy-update.md)
8. [Validation harness](../implementation/validation-harness.md)

That path moves from concept to implementation to validation.
