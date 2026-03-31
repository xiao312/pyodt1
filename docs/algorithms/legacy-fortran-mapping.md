# Legacy Fortran to Python mapping

## Upstream Fortran source

Primary upstream reference:
- `external/odt1/source1/`

## Current mapping

| Fortran | Python |
|---|---|
| `Brng.f` | `pyodt1.rng.OdtRNG` |
| `BSeeds.f` | `pyodt1.rng.OdtRNG(seed_index=...)` |
| `BExp.f` | `pyodt1.advance.sample_exponential_wait()` |
| `BInitRun.f` | `pyodt1.advance.generate_initial_state()` |
| `BInitIter.f` | `pyodt1.advance.compute_initial_dt()`, `pyodt1.advance.compute_td()` |
| `BAdv.f` | `pyodt1.advance.advance_diffusion()` |
| `BEqnStep.f` | `pyodt1.advance.equation_step()` |
| `BLenProb.f` | `pyodt1.eddy_sampling.build_length_distribution()` |
| `BLength.f` | `pyodt1.eddy_sampling.sample_length()` |
| location sampling in `BSampleEddy.f` | `pyodt1.eddy_sampling.sample_location()` |
| `BsKd.f` | `pyodt1.eddy_sampling.bs_kd()` |
| `BProb.f` | `pyodt1.acceptance.acceptance_probability()` |
| `BTriplet.f` | `pyodt1.triplet.triplet_map()` |
| `BAddK.f` | `pyodt1.triplet.add_k()` |
| `BEddy.f` | `pyodt1.solver.OdtSolver.apply_eddy()` |
| `BLowerdt.f` | `pyodt1.solver.OdtSolver.sample_only()` |
| `BRaisedt.f` | `pyodt1.solver.OdtSolver.raise_dt()` |
| inner realization scheduling in `Bodt.f` | `pyodt1.solver.OdtSolver.run_realization()` |

## Notes

This mapping is still partial. The current code validates the minimal eddy-sampling and accepted-eddy update path, not yet the full `Bodt.f` execution loop.
