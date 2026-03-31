# ODT in the literature

This page collects a few external references that are useful for understanding where **One-Dimensional Turbulence (ODT)** came from, what problems it was designed to address, and how the model family grew beyond the small legacy `odt1` code reimplemented in `pyodt1`.

The goal here is not to provide a full literature review. Instead, this page gives a practical reading map for new users.

## How to think about ODT in the wider turbulence-modeling landscape

A useful way to place ODT is:

- it is **not** DNS,
- it is **not** a conventional RANS closure,
- it is **not** a standard LES subgrid model,
- and it is **more structured than a purely statistical mixing model**.

The basic ODT idea is to evolve flow variables on a **1D physical domain** while representing turbulent advection by a stochastic sequence of **eddy events**, typically implemented using triplet maps. Deterministic diffusion, transport, and reaction processes are then solved directly on that 1D line.

This combination is why ODT is often attractive for:

- wall-bounded flows,
- turbulent mixing,
- scalar transport,
- turbulent combustion,
- and multiscale problems where small-scale structure matters but full 3D DNS is too expensive.

## A short reading path

If you want a compact progression, a good order is:

1. **Kerstein (1999)** for the classic ODT formulation.
2. **Kerstein et al. (2001)** for the vector-velocity extension that is especially relevant to `odt1`-style velocity evolution.
3. **Echekki et al. (2001)** for an early reacting-flow application.
4. **Schmidt et al. (2003)** and the **ODTLES** report for coupling ODT ideas to LES / 3D settings.
5. **Kerstein's later overview chapter** for the broader modeling philosophy.

## Core references

## 1. Classic formulation paper

**Alan R. Kerstein (1999)**  
*One-dimensional turbulence: model formulation and application to homogeneous turbulence, shear flows, and buoyant stratified flows*  
Journal of Fluid Mechanics, 392, 277-334.

- DOI: <https://doi.org/10.1017/S0022112099005376>
- Cambridge page: <https://www.cambridge.org/core/journals/journal-of-fluid-mechanics/article/onedimensional-turbulence-model-formulation-and-application-to-homogeneous-turbulence-shear-flows-and-buoyant-stratified-flows/8147DE294B666EBBE0938818B247E6BC>

Why it matters:

- This is the main foundational ODT paper.
- It explains the 1D stochastic-map view of turbulent advection.
- It shows that the model can reproduce meaningful turbulence behavior across several canonical flow classes.

For readers of `pyodt1`, this paper is the best first external source for understanding the overall method rather than just the details of one Fortran implementation.

## 2. Vector formulation / free-shear-flow extension

**Alan R. Kerstein, W. T. Ashurst, Scott Wunsch, and Vebjorn Nilsen (2001)**  
*One-dimensional turbulence: vector formulation and application to free shear flows*  
Journal of Fluid Mechanics, 447, 85-109.

- DOI: <https://doi.org/10.1017/S0022112001005778>
- Cambridge page: <https://www.cambridge.org/core/journals/journal-of-fluid-mechanics/article/onedimensional-turbulence-vector-formulation-and-application-to-free-shear-flows/69C33F9312AE4ACE961DCD94083D7D2F>

Why it matters:

- This is especially relevant to the legacy `odt1` code because it treats velocity as a **vector quantity**, not just a scalar profile.
- It discusses pressure scrambling ideas and intercomponent energy transfer.
- It is close in spirit to the kind of three-component velocity evolution implemented in `pyodt1`.

If you want to understand why the legacy code carries `u`, `v`, and `w` and why accepted eddies do more than a bare triplet map, this is a very useful paper.

## 3. Early reacting-flow ODT application

**Tarek Echekki, Alan R. Kerstein, Thomas D. Dreeben, and Jyh-Yuan Chen (2001)**  
*One-dimensional turbulence simulation of turbulent jet diffusion flames: model formulation and illustrative applications*  
Combustion and Flame, 125(3), 1083-1105.

- DOI: <https://doi.org/10.1016/S0010-2180(01)00214-6>

Why it matters:

- It shows how ODT was adapted to turbulent combustion problems.
- It is a good bridge between the general turbulence-model idea and the combustion-oriented use cases many readers care about.
- It helps explain why ODT has remained interesting in combustion even when many other turbulence closures exist.

## 4. Broader conceptual overview

**Alan R. Kerstein**  
*ODT: Stochastic Simulation of Multi-Scale Dynamics*

- OSTI full text: <https://www.osti.gov/servlets/purl/1728518>

Why it matters:

- This is a broader conceptual discussion rather than just a narrow algorithm paper.
- It places ODT in a wider modeling framework for multiscale flow simulation.
- It is useful if you want to understand the modeling philosophy behind ODT, not only the mechanics of triplet maps and event rates.

This source is especially helpful for readers asking: *Why invent a model like this at all, instead of just refining LES or RANS?*

## ODT beyond stand-alone 1D runs

## 5. Near-wall LES closure based on ODT

**Rodney C. Schmidt, Alan R. Kerstein, Scott Wunsch, and Vebjorn Nilsen (2003)**  
*Near-wall LES closure based on one-dimensional turbulence modeling*  
Journal of Computational Physics, 186(1), 317-355.

- DOI: <https://doi.org/10.1016/S0021-9991(03)00071-8>
- ScienceDirect page: <https://www.sciencedirect.com/science/article/abs/pii/S0021999103000718>

Why it matters:

- It shows one major direction the ODT community took: embedding ODT-like resolution where LES is weak, especially near walls.
- It helps readers understand that ODT is not only a stand-alone 1D model; it can also act as part of a larger hybrid formulation.

## 6. ODTLES report

**Rodney C. Schmidt, Randy McDermott, and Alan R. Kerstein (2005)**  
*ODTLES: A Model for 3D Turbulent Flow Based on One-Dimensional Turbulence Modeling Concepts*

- OSTI full text: <https://www.osti.gov/servlets/purl/921740>

Why it matters:

- This is one of the key references for extending ODT concepts to 3D domains.
- It explains the idea of embedding multiple ODT lines in a coarser LES mesh.
- It is a natural next read if you are interested in hybrid LES / ODT approaches.

## More recent examples and practical reminders

## 7. Modern stand-alone ODT for turbulent mixing

**Marten Klein, Christian Zenker, and Heiko Schmidt (2019)**  
*Small-scale resolving simulations of the turbulent mixing in confined planar jets using one-dimensional turbulence*  
Chemical Engineering Science, 204, 186-202.

- DOI: <https://doi.org/10.1016/j.ces.2019.04.024>
- ScienceDirect page: <https://www.sciencedirect.com/science/article/abs/pii/S0009250919303896>

Why it matters:

- It illustrates that ODT is still actively used for turbulent mixing problems.
- It highlights one recurring theme in ODT work: the model is appealing when scalar microstructure matters and coarse closures become limiting.
- It also reinforces an important practical point: **ODT model parameters are not generally universal** and often need calibration for a class of flows.

## What these papers mean for `pyodt1`

The legacy `odt1` code reimplemented here is not the whole ODT literature. It is a specific historical code path within a larger model family.

A practical summary is:

- `pyodt1` is closest to the **classical stand-alone ODT** tradition,
- the three-component velocity handling connects naturally to the **vector ODT** literature,
- the postprocessing/output path in the legacy code reflects a specific older implementation style,
- and the wider ODT ecosystem includes **reacting-flow**, **boundary-layer**, and **ODTLES / LES-coupled** developments that go beyond the present repository.

## Suggested use of this page

Use this page when you want to answer questions like:

- What is ODT trying to model physically?
- Why is there a triplet map at all?
- Why is a 1D model taken seriously for turbulent flow?
- Why does the code carry several velocity components?
- How does stand-alone ODT relate to ODTLES?

For the implementation details of this repository, return to:

- [Algorithm overview](../algorithms/overview.md)
- [Legacy Fortran to Python mapping](../algorithms/legacy-fortran-mapping.md)
- [Validation harness](../implementation/validation-harness.md)
