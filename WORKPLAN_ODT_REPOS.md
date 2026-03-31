# Work Plan: BYUignite/ODT and odt1

Date: 2026-03-31
Project directory: `/mnt/d/u_deepflame_agent/Projects/odt`
Reference repos inspected:
- `/tmp/ODT` → `https://github.com/BYUignite/ODT`
- `/tmp/odt1` → `https://github.com/rmcdermo/odt1`

## 1. Purpose

We want to work with both public ODT-related repositories in a complementary way:

- **`odt1`** as the minimal / foundational implementation for understanding the core ODT algorithm
- **`BYUignite/ODT`** as the modern, combustion-capable research code for actual runs, case modification, and possible extension

The combined goal is to:
1. understand the ODT method at algorithm level,
2. establish runnable local workflows for both repos,
3. identify combustion-relevant capabilities and limitations,
4. prepare a path toward future development, validation, and integration work.

## 2. Why use both repos

### `odt1`
Strengths:
- small and conceptually compact
- easier to trace triplet-map and eddy-sampling logic
- good for building algorithm understanding

Limitations:
- older Fortran structure
- sparse documentation
- no obvious modern chemistry stack
- likely limited as a production combustion workflow

### `BYUignite/ODT`
Strengths:
- modern C++ codebase
- Cantera-based reacting-flow support
- CVODE integration
- adaptive mesh support
- multiple example cases and postprocessing structure

Limitations:
- larger learning curve
- more dependencies
- case workflow needs setup and validation before productive use

## 3. Current environment snapshot

### Local machine
- GPU: NVIDIA GeForce RTX 3070 Ti
- Driver shown by `nvidia-smi`: Driver Version `591.74`
- CUDA shown by `nvidia-smi`: `13.1`
- VRAM: `8192 MiB`

### Current repo/workspace
- working directory: `/mnt/d/u_deepflame_agent/Projects/odt`
- reference clones currently available under `/tmp/ODT` and `/tmp/odt1`

## 4. Main technical questions to answer

### For `odt1`
1. What is the exact main execution flow in `Bodt.f`?
2. How are eddy size, location, and acceptance probability sampled?
3. What input files are required for the default run?
4. Can we compile and run a minimal case reproducibly?
5. What outputs/statistics does it produce?

### For `BYUignite/ODT`
1. Which example cases are nonreacting vs reacting?
2. What are the minimal dependencies needed to build it locally?
3. Which cases can be run first with least friction?
4. How do YAML inputs map to solver behavior?
5. Where are the main extension points for future combustion work?

## 5. Proposed phased plan

## Phase 0 — Workspace setup and reproducibility

### Objectives
- create a clean working structure for both repos
- avoid editing `/tmp` clones directly
- preserve provenance for all local changes

### Actions
- create local working copies under this project, e.g.:
  - `external/BYUignite-ODT/`
  - `external/odt1/`
- record exact upstream commit hashes
- add a small local notes directory:
  - `notes/`
  - `runs/`
  - `artifacts/`
- keep generated outputs out of Git unless curated

### Deliverables
- local clones in stable paths
- `notes/upstream-versions.md`
- `.gitignore` for run outputs and build artifacts

## Phase 1 — Read and map both codebases

### Objectives
- build a code navigation map for each repo
- identify the smallest useful execution path

### Actions for `odt1`
- inspect:
  - `Bodt.f`
  - `BSampleEddy.f`
  - `BProb.f`
  - `BLenProb.f`
  - `BTriplet.f`
  - `BEddy.f`
  - `BAdv.f`
- reconstruct the runtime loop and input/output flow
- document required input files:
  - `BConfig.dat`
  - `BOptions.dat`
  - `BPars.dat`
  - any restart / BC files

### Actions for `BYUignite/ODT`
- inspect:
  - `main.cc`
  - `solver.cc`
  - `domain.cc`
  - `eddy.cc`
  - `micromixer.cc`
  - `meshManager.cc`
  - `streams.cc`
- map how `input.yaml` fields drive execution
- classify input cases by physics

### Deliverables
- `notes/odt1-code-map.md`
- `notes/byu-odt-code-map.md`
- execution flow diagrams or bullet-form call chains

## Phase 2 — Minimal build and run for `odt1`

### Objectives
- get `odt1` compiling and running first
- use it as the algorithm-learning baseline

### Actions
- determine compiler assumptions from source
- write a minimal build command or Makefile wrapper
- identify or reconstruct the default input files needed for a baseline run
- execute one minimal case
- capture:
  - compile steps
  - runtime steps
  - output file meanings

### Risks
- old Fortran assumptions or compiler behavior
- missing sample input files in repo
- implicit legacy defaults not documented in README

### Deliverables
- `notes/odt1-build-run.md`
- `scripts/build_odt1.sh`
- `scripts/run_odt1_case.sh`
- one archived test run under `runs/odt1/`

## Phase 3 — Minimal build and run for `BYUignite/ODT`

### Objectives
- build the modern code locally
- run at least one nonreacting case first, then one reacting-capable case if dependencies permit

### Actions
- install/verify dependencies:
  - CMake
  - Cantera
  - SUNDIALS/CVODE as required by build
  - Python packages for postprocessing
- try easiest cases first:
  - `channelFlow`
  - `coldJet`
  - `laminar_mixing_layer`
- then identify the best first reacting case
- validate run directory generation and output structure

### Risks
- Cantera version mismatch
- build system drift relative to current compilers/libs
- undocumented expectations in run scripts

### Deliverables
- `notes/byu-odt-build-run.md`
- `scripts/build_byu_odt.sh`
- `scripts/run_byu_case.sh`
- one archived run under `runs/byu-odt/`

## Phase 4 — Capability comparison and validation plan

### Objectives
- compare what each repo can realistically support
- define which code to use for which class of task

### Comparison dimensions
- language / maintainability
- ease of building
- runtime workflow
- turbulence algorithm transparency
- combustion chemistry support
- adaptive mesh support
- case diversity
- extensibility
- output and postprocessing quality

### Deliverables
- `notes/repo-comparison.md`
- recommended usage matrix, e.g.:
  - algorithm study → `odt1`
  - reactive simulation and development → `BYUignite/ODT`

## Phase 5 — Development direction selection

### Objectives
- decide how future work should branch from the two-code strategy

### Possible paths

#### Path A — Learning + production split
- use `odt1` only as a reference model
- use `BYUignite/ODT` for all practical case work

#### Path B — Validation pair
- run analogous simple cases in both repos
- compare eddy statistics / scalar evolution / sensitivity to parameters

#### Path C — Feature transfer / modernization study
- use `odt1` as a compact algorithm reference for understanding pieces of BYUignite/ODT
- document where modern code behavior differs from the basic implementation

### Deliverable
- `notes/development-direction.md`

## 6. Recommended immediate execution order

### Week 1 priorities
1. create stable local clones under this project
2. write code maps for both repos
3. get `odt1` to compile or determine what is missing
4. inspect `BYUignite/ODT` build requirements in detail

### Week 2 priorities
1. run one `odt1` baseline case
2. build `BYUignite/ODT`
3. run one nonreacting BYU case
4. identify first reacting case and chemistry setup needs

### Week 3 priorities
1. write formal comparison note
2. choose primary code for forward work
3. define next technical target (e.g. hydrogen / ammonia / jet flame / benchmark replication)

## 7. Success criteria

This workplan is successful if we achieve all of the following:

- both repos are cloned into stable local working paths
- `odt1` execution flow is documented and at least one run is attempted reproducibly
- `BYUignite/ODT` is built and at least one case runs locally
- a clear comparison exists between the two repos
- we can state which repo is primary for future combustion work and why

## 8. Recommended file structure in this project

```text
odt/
  WORKPLAN_ODT_REPOS.md
  external/
    BYUignite-ODT/
    odt1/
  notes/
    upstream-versions.md
    odt1-code-map.md
    byu-odt-code-map.md
    odt1-build-run.md
    byu-odt-build-run.md
    repo-comparison.md
    development-direction.md
  scripts/
    build_odt1.sh
    run_odt1_case.sh
    build_byu_odt.sh
    run_byu_case.sh
  runs/
    odt1/
    byu-odt/
  artifacts/
```

## 9. Recommendation

Use the two repos with distinct roles:

- **`odt1`** = algorithm reference and minimal baseline
- **`BYUignite/ODT`** = primary practical code for combustion-oriented ODT work

This is the lowest-risk and most informative way to proceed.
