"""Rebuild the acceptance-v2 leaderboard from completed coil runs.

Needs NumPy and the native environment for checks. Entries live in
`submissions/leaderboard-v2.json`; an entry with `input` is first checked with
`scripts/check_coils.py` into its `run` directory when that run is missing. The
verdict summaries are written back to the entries file and the tables to
`docs/validation/LEADERBOARD.md` between the leaderboard markers.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fusion_baselines.acceptance_v2 import V2, evaluate  # noqa: E402

START, END = "<!-- leaderboard:start -->", "<!-- leaderboard:end -->"
WOUT = ROOT / "artifacts/plasma-design-v2/reference-fine/wout.nc"
LABELS = {"reference401": "Original Goodman target (reference401)",
          "selected401": "Improved Step 3 target (selected401)"}


def summary(verdict):
    boundary = verdict["boundary"]
    mean = max(b["mean"] for b in boundary)
    peak = max(b["max"] for b in boundary)
    interior = max(verdict["interior_vector_rms"])
    return dict(boundary_mean=mean, boundary_max=peak, interior_vector_rms=interior,
                checks_pass=all(verdict["shared_checks"].values()),
                v1=verdict["v1"]["passed"], v2=verdict["v2"]["passed"],
                worst_v2_ratio=max(mean / V2["boundary_mean_max"], peak / V2["boundary_max_max"],
                                   interior / V2["interior_vector_rms_max"]))


def check(entry):
    run = ROOT / entry["run"]
    if (run / "result.json").is_file():
        return
    if entry["target"] != "reference401":
        raise ValueError(f"no stored run for {entry['name']}; checks support reference401 only")
    (kind, path), = entry["input"].items()
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
               VECLIB_MAXIMUM_THREADS="1", MKL_NUM_THREADS="1")
    subprocess.run([sys.executable, str(ROOT / "scripts/check_coils.py"), f"--{kind}",
                    str(ROOT / path), "--wout", str(WOUT), "--output", str(run)],
                   check=True, env=env)


def table(entries):
    rows = ["| Rank | Coil set | Original contributor | Record | v2 | v1 | Boundary mean | "
            "Boundary max | Interior RMS | Other checks | Worst v2 ratio |",
            "| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: |"]
    ranked = sorted(entries, key=lambda e: (not e["result"]["v2"], not e["result"]["checks_pass"],
                                            e["result"]["worst_v2_ratio"]))
    for rank, entry in enumerate(ranked, 1):
        r = entry["result"]
        rows.append(f"| {rank} | [{entry['name']}](../../{entry['link']}) | "
                    f"{entry['contributor']} | {entry['record']} | "
                    f"{'**pass**' if r['v2'] else 'fail'} | "
                    f"{'pass' if r['v1'] else 'fail'} | {r['boundary_mean']:.5f} | "
                    f"{r['boundary_max']:.4f} | {r['interior_vector_rms']:.5f} | "
                    f"{'pass' if r['checks_pass'] else 'fail'} | {r['worst_v2_ratio']:.3f} |")
    return "\n".join(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entries", type=Path, default=ROOT / "submissions/leaderboard-v2.json")
    parser.add_argument("--page", type=Path, default=ROOT / "docs/validation/LEADERBOARD.md")
    args = parser.parse_args()
    data = json.loads(args.entries.read_text(encoding="utf-8"))
    for entry in data["entries"]:
        if "input" in entry:
            check(entry)
        entry["result"] = summary(evaluate(ROOT / entry["run"]))
    targets = dict.fromkeys(entry["target"] for entry in data["entries"])
    tables = "\n\n".join(f"### {LABELS[target]}\n\n" + table(
        [e for e in data["entries"] if e["target"] == target]) for target in targets)
    page = args.page.read_text(encoding="utf-8")
    before, rest = page.split(START, 1)
    args.page.write_text(f"{before}{START}\n{tables}\n{END}{rest.split(END, 1)[1]}",
                         encoding="utf-8")
    args.entries.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(tables)
