# sample_channel_case

Small legacy-style sample case for `pyodt1`.

Files:

- `BOptions.dat` — xmgrace-style snapshot output mode (`ioptions(1)=1`)
- `BPars.dat` — mesh and algorithm parameters
- `BConfig.dat` — run-control and physical parameters

This case is intentionally chosen to produce visible stochastic activity in a short run:

- `N = 30`
- `niter = 3`
- `nstat = 3`
- `ntseg = 5`
- `tend = 5.0e-2`
- `pgrad = 100.0`
- `C = 1.0e11`

The pressure gradient creates a clear mean-velocity buildup, while the elevated event-rate parameter makes accepted eddies visible within a short demonstration run. This is a compact demo case, not a tuned physical benchmark.

Run from the repository root:

```bash
source .venv/bin/activate
python - <<'PY'
from pyodt1 import run_legacy_case
out = run_legacy_case(
    'cases/sample_channel_case',
    seed_index=1,
    output_dir='runs/sample_channel_case_py',
    max_trials=500,
)
print(out.output_dir)
print(out.log_path)
print(out.result.final_rng_state)
PY
```
