# ODT for CFD readers

This tutorial is written for readers who already know conventional CFD ideas—grids, transport equations, turbulence closures, DNS/LES/RANS tradeoffs—but are new to **ODT**, or **One-Dimensional Turbulence**.

The goal is not to present the most formal derivation first. Instead, the goal is to build a working mental model from first principles and connect that model to what `pyodt1` is implementing.

## Why a CFD reader might find ODT strange at first

If your background is in CFD, you are probably used to one of these pictures:

- **DNS**: solve the full unsteady equations on a fine multidimensional mesh,
- **LES**: resolve large scales and model subgrid scales,
- **RANS**: solve averaged equations and model turbulence statistically.

ODT does not fit neatly into any of those boxes.

ODT keeps a **real one-dimensional spatial line** and evolves fields on that line, but it does **not** treat turbulence as only a diffusion coefficient or only a closure term. Instead, it represents turbulent stirring using **stochastic eddy events** that instantaneously remap part of the 1D domain.

That sounds odd at first, but it is the key idea.

## First principle: turbulent mixing is not only diffusion

A useful place to start is the observation that turbulent transport is not well described by molecular diffusion alone.

Molecular diffusion smooths gradients through a local second-derivative process. In a scalar transport equation, that looks like the familiar Laplacian term.

But turbulent mixing also contains:

- advection-like rearrangement,
- stretching and folding,
- generation of fine scales,
- intermittent bursts over a range of eddy sizes.

So if we only add more diffusion, we miss an important part of how turbulence reorganizes scalar and velocity structure.

ODT addresses that by separating two roles:

1. **deterministic transport** such as diffusion and imposed forcing,
2. **stochastic stirring events** representing turbulent eddies.

That decomposition is one of the central conceptual moves of the method.

## Second principle: keep a real spatial line

ODT is not a zero-dimensional mixing model. It keeps a one-dimensional line with spatial resolution.

That means the model still has:

- resolved profiles,
- gradients,
- interfaces,
- boundary effects along the line,
- evolving fine structure on the line.

This matters because many interesting combustion and transport problems depend on sharp scalar layers and local structure.

So even though the model is one-dimensional, it still retains much more spatial information than a fully lumped model.

## Third principle: model stirring as discrete eddies

The signature idea of ODT is that turbulence is represented by **discrete eddy events**.

Instead of trying to explicitly compute a full 3D velocity field, the model says:

- occasionally an eddy of some size occurs,
- it affects some interval of the 1D line,
- that interval is instantaneously remapped,
- between eddies, deterministic processes continue to evolve the fields.

This creates an event-driven picture of turbulent stirring.

For CFD readers, one helpful analogy is:

- deterministic advancement is the “continuous PDE part,”
- eddy events are a “stochastic rearrangement operator” layered on top.

## The triplet map: the heart of the stirring model

The specific remapping operation used in basic ODT is the **triplet map**.

Imagine selecting an interval of the 1D domain and compressing it into three equal images placed back into the same interval:

1. a left copy,
2. a reversed middle copy,
3. a right copy.

This operation does several things that are qualitatively similar to turbulent stirring:

- it creates sharper gradients,
- it folds structure,
- it transfers larger-scale variation into smaller-scale structure,
- it stays local to one interval.

That is why the triplet map is such a compact and powerful operator in ODT.

## Why the middle copy is reversed

The reversed middle copy is not an arbitrary flourish. It gives the map a folding character.

Without that reversal, the operation would look too much like simple repeated compression. With reversal, the map better mimics the idea that fluid elements are stretched and folded into one another.

This is one of the clearest places where the method encodes a physical intuition in a very compact discrete rule.

## What an ODT realization looks like

At a high level, one ODT realization evolves like this:

1. start from a 1D initial condition,
2. advance deterministic processes for some time,
3. sample a candidate eddy,
4. decide whether to accept it,
5. if accepted, apply a triplet-map-based update,
6. continue alternating between deterministic evolution and stochastic eddies.

So an ODT history is not a smooth time integration alone. It is a hybrid process:

- continuous deterministic segments,
- punctuated by discrete stochastic events.

## Where randomness enters—and why

A CFD reader may naturally ask: why is the model stochastic at all?

The answer is that a reduced one-dimensional model cannot explicitly resolve the full multidimensional turbulent cascade. So the unresolved turbulent stirring must be represented statistically.

But the randomness is not uncontrolled. The model does **not** just pick arbitrary events. It uses structured rules for:

- eddy-size distribution,
- eddy location,
- eddy acceptance probability,
- waiting time between candidate trials.

So the stochastic part is disciplined by algorithmic and physical constraints.

## Candidate eddies versus accepted eddies

This distinction is important.

ODT does not directly say “an eddy happens here.” Instead it says:

1. propose a candidate eddy,
2. evaluate whether it should occur,
3. accept or reject it.

This is similar in spirit to other stochastic sampling frameworks where proposals and actual realized events are not the same thing.

For `odt1`, the current Python implementation already covers this path:

- build the eddy-size distribution,
- sample the size,
- sample the location,
- compute the acceptance probability,
- apply the accepted-eddy update if the event is accepted.

## Why eddy size matters so much

An eddy in ODT is not only “where” but also “how large.”

Large eddies and small eddies do different things:

- large eddies reorganize a broad region,
- small eddies create fine structure more locally,
- the model must control how likely different sizes are.

In `odt1`, the triplet map requires the full eddy size `L` to be divisible by 3, so the code often works with the image size `L3 = L/3` first and then reconstructs `L = 3*L3`.

This is a nice example of the model’s mathematical structure shaping the implementation details.

## Why acceptance probability matters

If the algorithm only sampled candidate eddies and always applied them, the resulting event sequence would generally be wrong.

The acceptance probability is what turns the proposal mechanism into the intended event process.

In practice, it depends on things like:

- eddy size,
- kernel measures derived from the current velocity fields,
- event-rate parameters,
- the probability with which that eddy was proposed.

This is one of the deeper ideas in `odt1`: the event process is not only random; it is **rate controlled**.

## Deterministic advancement is still there

ODT is not purely a sequence of maps. Between eddy events, the model still advances deterministic equations.

In the basic code path, this includes diffusion and streamwise forcing effects on the velocity components.

For CFD readers, this is reassuring because it means ODT does not abandon PDE-based physics. It reorganizes the full problem into:

- a deterministic transport component,
- a stochastic stirring component.

## Why ODT can be powerful

The appeal of ODT is that it can capture nontrivial small-scale structure and intermittent stirring behavior at much lower cost than multidimensional DNS.

That does not mean it replaces DNS or LES in every role. Rather, it occupies a useful modeling niche where:

- a 1D resolved line is still meaningful,
- strong scalar structure matters,
- stochastic event modeling is acceptable,
- the cost of full 3D resolution would be too high.

This is one reason ODT has remained interesting in turbulent combustion and related transport problems.

## What `pyodt1` is doing specifically

The purpose of `pyodt1` is not just to create “an ODT-like Python toy.” It is a careful reimplementation of the legacy **Basic ODT** Fortran package `odt1`.

That means the project cares about three things simultaneously:

1. preserving the algorithmic meaning of the original code,
2. validating the Python implementation quantitatively against the Fortran,
3. making the method easier to read and learn.

At the current stage, `pyodt1` already validates a minimal but important algorithmic path against the original Fortran:

- legacy RNG,
- eddy-size distribution,
- eddy-size sampling,
- eddy-location sampling,
- `BsKd`,
- acceptance probability,
- accepted-eddy update.

## How to connect the concepts to the package

A practical reading map is:

- start with [Algorithm overview](../algorithms/overview.md),
- then read [Triplet map](../algorithms/triplet-map.md),
- then [Eddy sampling](../algorithms/eddy-sampling.md),
- then [Acceptance probability](../algorithms/acceptance-probability.md),
- and finally [Validation harness](../implementation/validation-harness.md).

If you are interested in the mechanics of reproducibility, also read [Legacy RNG](../algorithms/rng.md).

## A simple summary for CFD readers

If you want one compact mental model, use this:

> ODT keeps a real 1D domain, advances deterministic transport on that domain, and represents turbulent stirring by stochastic eddy events implemented through the triplet map.

That sentence is not the full method, but it is the right starting intuition.

## What to keep in mind while learning ODT

A few mindset shifts help a lot:

- do not judge ODT by whether it looks like a discretized Navier–Stokes solver,
- think of it as a reduced stochastic transport model with resolved 1D structure,
- pay attention to how eddy proposals, acceptance, and updates fit together,
- remember that exact implementation details matter when reproducing a legacy scientific code.

With those ideas in place, the rest of the package documentation becomes much easier to navigate.
