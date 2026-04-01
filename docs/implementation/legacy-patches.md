# Legacy source patches

This page records the **small source-level robustness patches** applied to the vendored legacy `odt1` Fortran sources in this repository.

The purpose of this page is to make one distinction very clear:

- these patches are **not algorithm redesigns**, and
- they are **not intended to change ODT model physics**,
- but they do remove compiler-fragile legacy coding patterns that prevented reliable runtime validation in the current environment.

## Why patches were needed

During direct Fortran-vs-Python validation, the major remaining runtime problem was the original `BSnap` intercomparison path (`ioptions(1)=0`).

The unmodified legacy code used a header-writing convention based on **negative `N`**:

- `BSnap.f` temporarily negated `N`
- then called `BRecord`
- `BRecord.f` declared local arrays using `N`
- and only later normalized with `N = abs(N)`

Under the local `gfortran 9.4.0` toolchain, this led to crashes in the unmodified path.

A dedicated reproducer remains available:

- `scripts/investigate_bsnap_intercomparison.py`

That reproducer shows:

- the **original unmodified** intercomparison path crashes,
- the **patched legacy** intercomparison path runs,
- and the patched output matches the Python implementation numerically.

## Files patched

The following vendored legacy sources were patched:

- `external/odt1/source1/BRecord.f`
- `external/odt1/source1/BSnap.f`

## What was patched

## 1. `BRecord.f`

### Original issue

The original routine used the signed incoming `N` directly in array declarations and only later normalized it:

- header mode was indicated by `N < 0`
- local storage depended on `N`
- normalization happened afterward via `N = abs(N)`

That pattern is compiler-fragile because it allows negative extents to participate in runtime storage logic before the value is sanitized.

### Patch applied

The patched version now:

- treats the incoming array as assumed-size (`s(*)`)
- computes `nabs = abs(N)` immediately
- uses `nabs` for loop extents and output count
- uses a fixed local buffer rather than negative-extent local storage

### Effect of the patch

This preserves the intended record semantics:

- negative `N` still means “write header first”
- the same record values are written
- formatting remains the same

But it removes the fragile dependency on negative extents in local array sizing.

## 2. `BSnap.f`

### Original issue

The original intercomparison path used in-place mutation of `N`:

- `N = -N`
- `call BRecord(ifile, N, ht)`

This was intended only as a signaling trick for header writing, but it meant the signed argument passed into `BRecord` could trigger the unsafe behavior described above.

### Patch applied

The patched version introduces a separate variable:

- `NWRITE = -N`
- `call BRecord(ifile, NWRITE, ht)`

The physical mesh size `N` itself is no longer negated in-place.

### Effect of the patch

This preserves the intended file-format semantics while avoiding mutation of the principal loop/index variable.

## What behavior changed

The following behavior changed:

- the patched legacy intercomparison path now runs successfully under the local toolchain
- `BSnap` intercomparison-mode output can now be directly compared numerically against Python
- the repository no longer needs temporary generated patched stand-ins for routine-level validation of this path

In practical terms, this means:

- patched `BSnap` intercomparison mode is now part of the normal comparison workflow
- see `scripts/compare_bsnap_intercomparison.py`

## What behavior did **not** change

The patches are not intended to change:

- ODT sampling logic
- eddy acceptance logic
- triplet-map behavior
- deterministic advancement formulas
- statistics formulas
- output-file semantics for the legacy intercomparison format
- output-file semantics for xmgrace mode

The model equations and the intended file contents remain the same.

The patch only changes **how the legacy code expresses header signaling and temporary storage**, so that the intended behavior runs reliably.

## Validation status after patching

After patching:

- patched `BSnap` intercomparison mode runs
- patched `BSnap` xmgrace mode runs
- direct comparison against Python shows small floating-point / formatting-level differences only

See:

- `scripts/compare_bsnap_intercomparison.py`
- `scripts/compare_postprocessing.py`
- `scripts/investigate_bsnap_intercomparison.py`

## How to describe this in project status

The most accurate wording is:

- the **original unmodified historical** intercomparison path is compiler-fragile,
- the repository now includes a **minimal robustness patch** for that path,
- and the **patched legacy path is directly runtime-validated**.

That is more precise than either of the following oversimplifications:

- “the original intercomparison path works everywhere”
- “intercomparison mode is unsupported”

Neither of those is true anymore.

## Related pages

- [Fortran comparison status](fortran-comparison.md)
- [Validation harness](validation-harness.md)
- [Legacy Fortran to Python mapping](../algorithms/legacy-fortran-mapping.md)
