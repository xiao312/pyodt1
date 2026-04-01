# Fortran routine status matrix

This page gives a concise routine-by-routine status summary for the legacy `odt1` Fortran source set under `external/odt1/source1/`.

## Status labels

- **Implemented**: a Python equivalent exists
- **Validated**: compared directly against actual Fortran execution
- **Tested**: covered by Python tests or structural compatibility checks, but not a dedicated major harness
- **Caveated**: validated with an important caveat (for example, only for the patched legacy path)
- **Remaining**: not yet fully mirrored in exact procedural detail

## Matrix

| Fortran routine | Python equivalent | Status |
|---|---|---|
| `Brng.f` | `pyodt1.rng.OdtRNG.uniform()` | Implemented, validated |
| `BSeeds.f` | `pyodt1.rng.OdtRNG(seed_index=...)` | Implemented, validated |
| `BrngGet.f` | `pyodt1.rng.OdtRNG.get_state()`, `pyodt1.legacy.brng_get()` | Implemented, validated |
| `BrngPut.f` | `pyodt1.rng.OdtRNG.put_state()`, `pyodt1.legacy.brng_put()` | Implemented, validated |
| `BLenProb.f` | `pyodt1.eddy_sampling.build_length_distribution()` | Implemented, validated |
| `BLength.f` | `pyodt1.eddy_sampling.sample_length()` | Implemented, validated |
| `BSampleEddy.f` | `pyodt1.eddy_sampling.sample_eddy()` and helpers | Implemented, validated |
| `BsKd.f` | `pyodt1.eddy_sampling.bs_kd()` | Implemented, validated |
| `BProb.f` | `pyodt1.acceptance.acceptance_probability()` | Implemented, validated |
| `BTriplet.f` | `pyodt1.triplet.triplet_map()` | Implemented, validated |
| `BAddK.f` | `pyodt1.triplet.add_k()` | Implemented, validated |
| `BEddy.f` | `pyodt1.solver.OdtSolver.apply_eddy()` | Implemented, validated |
| `BAdv.f` | `pyodt1.advance.advance_diffusion()` | Implemented, validated |
| `BEqnStep.f` | `pyodt1.advance.equation_step()` | Implemented, validated |
| `BExp.f` | `pyodt1.advance.sample_exponential_wait()` | Implemented, validated |
| `BInitRun.f` | `pyodt1.advance.generate_initial_state()` | Implemented, validated |
| `BInitIter.f` | `pyodt1.advance.compute_initial_dt()`, `pyodt1.advance.compute_td()`, solver setup logic | Implemented, validated, caveated |
| `BLowerdt.f` | `pyodt1.solver.OdtSolver.lower_dt()` | Implemented, validated |
| `BRaisedt.f` | `pyodt1.solver.OdtSolver.raise_dt()` | Implemented, validated |
| `BSetOld.f` | `pyodt1.statistics.save_old_values()` | Implemented, validated |
| `BChange.f` | `pyodt1.statistics.accumulate_change()` | Implemented, validated |
| `BStats.f` | `pyodt1.statistics.accumulate_cstats()` | Implemented, validated |
| `BSeries.f` | `pyodt1.statistics.accumulate_series()` | Implemented, validated |
| `BWriteSeries.f` | `pyodt1.statistics.finalize_series_variance()`, `pyodt1.statistics.write_series_text()` | Implemented, validated |
| `BRecord.f` | `pyodt1.statistics.brecord_text()` | Implemented, validated |
| `XRecord.f` | `pyodt1.statistics.xrecord_text()` | Implemented, validated |
| `BSnap.f` | `pyodt1.statistics.compute_snap_outputs()`, `write_snap_intercomparison()`, `write_snap_xmgrace()` | Implemented, validated, caveated |
| `BReadOptions.f` | `pyodt1.config.read_options()`, `pyodt1.legacy.b_read_options()` | Implemented, validated |
| `BReadPars.f` | `pyodt1.config.read_pars()` | Implemented, validated |
| `BReadConfig.f` | `pyodt1.config.read_config()` | Implemented, validated |
| `BInitStats.f` | `pyodt1.legacy.b_init_stats()` and underlying initializers | Implemented, validated |
| `BAddTerm.f` | `pyodt1.legacy.b_add_term()` | Implemented, validated |
| top-level execution in `Bodt.f` | `run_realization()`, `run_scheduled_realization()`, `run_iterations()`, `pyodt1.legacy.run_legacy_case()` | Implemented, caveated, remaining |

## Important caveats

## `BInitIter.f`

The important numerical behavior is represented and validated, but the Python implementation is split across helper functions and solver setup rather than mirrored as a single one-to-one routine.

## `BSnap.f`

- the **patched legacy intercomparison path** is validated
- the **original unmodified xmgrace path** is validated
- the **original unmodified intercomparison path** is documented as compiler-fragile legacy behavior

See:

- [Fortran comparison status](fortran-comparison.md)
- [Legacy source patches](legacy-patches.md)

## `Bodt.f`

The main numerical runtime structure is in place, but exact line-by-line procedural parity is still not complete.

What remains is mostly:

- exact monolithic driver structure
- exact open/write/close sequencing everywhere
- exact historical procedural parity rather than missing turbulence-model content

## Recommended interpretation

The most accurate summary is:

- the repository now covers **almost the full routine set** in implementation terms
- the **numerically important majority** is directly validated against Fortran
- the remaining work is primarily about **top-level procedural parity**, not missing core ODT physics
