from __future__ import annotations

from pyodt1 import run_legacy_case
from pyodt1.statistics import parse_snap_xmgrace


def main() -> None:
    out = run_legacy_case(
        "cases/sample_channel_case",
        seed_index=1,
        output_dir="runs/sample_channel_case_py",
        max_trials=500,
    )

    print(f"outputs: {out.output_dir}")
    print(f"log: {out.log_path}")
    print(f"iterations: {out.result.niter}")
    print(f"final rng: {out.result.final_rng_state}")
    for i, result in enumerate(out.result.iteration_results, start=1):
        print(
            f"iteration {i}: trials={result.trial_count}, accepted={result.accepted_count}, "
            f"rejected={result.rejected_count}, physical_time={result.physical_time:.6f}"
        )

    snap1 = parse_snap_xmgrace(out.output_dir, 1)
    mean_u = snap1.records["A"][1:, 1]
    balance = snap1.records["H"][1:, 1]
    eddy_counts = snap1.records["eddy_counts"]
    nonzero = eddy_counts[(eddy_counts[:, 1] != 0) | (eddy_counts[:, 2] != 0)]

    print(f"snapshot-1 mean_u near wall: {mean_u[:5]}")
    print(f"snapshot-1 balance near wall: {balance[:5]}")
    print(f"snapshot-1 nonzero eddy-count rows: {nonzero[:10]}")


if __name__ == "__main__":
    main()
