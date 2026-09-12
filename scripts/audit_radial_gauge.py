"""Audit all four gauge cases, raw c=0 identity and independent well/stencil arithmetic."""

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np

from fusion_baselines.gauge_audit import audit_cell_binding, audit_family
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic


def reference(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path))


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError(f"input hash mismatch: {path}")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable audit output required")
    root = Path(__file__).resolve().parents[1]
    result = dict(
        schema_version=1,
        repository=git_state(root),
        cases=[],
        additional_physics_calls=0,
        global_maximum_J_certified=False,
        code=[
            reference(root / p)
            for p in ("scripts/audit_radial_gauge.py", "src/fusion_baselines/gauge_audit.py")
        ],
    )
    for nfp in (2, 3):
        for state in ("vacuum", "beta2"):
            path = args.study / f"nfp{nfp}-{state}.json"
            measured = json.loads(path.read_text())
            old = json.loads(checked(measured["source"]).read_text())
            checked(measured["wout"])
            checks = dict(
                completed=measured["status"] == "completed",
                raw_hashes=True,
                old_traces_exact=True,
                fixed_trace_set=True,
            )
            trace_keys = set()
            for ref in measured["traces"]:
                with np.load(checked(ref), allow_pickle=False) as data:
                    if "historical" in ref:
                        with np.load(checked(ref["historical"]), allow_pickle=False) as previous:
                            checks["old_traces_exact"] &= set(data.files) == set(
                                previous.files
                            ) and all(np.array_equal(data[k], previous[k]) for k in data.files)
                key = (
                    ref["kind"],
                    ref.get("slope"),
                    ref.get("level"),
                    ref.get("s"),
                    ref.get("alpha_offset"),
                )
                checks["fixed_trace_set"] &= key not in trace_keys
                trace_keys.add(key)
            expected = {
                ("radial", 0, level, s, None)
                for level in range(3)
                for s in (0.46, 0.48, 0.49, 0.5, 0.51, 0.52, 0.54)
            }
            expected |= {
                ("radial", c, level, s, c * (s - 0.5))
                for c in (-1, 1)
                for level in range(3)
                for s in (0.46, 0.48, 0.49, 0.51, 0.52, 0.54)
            }
            expected |= {("alpha", None, 2, 0.5, a) for a in (-0.01, 0.01, -0.005, 0.005)}
            checks["fixed_trace_set"] &= trace_keys == expected and len(measured["traces"]) == 61
            rows, family_checks = [], []
            old_by_cell = {(c["alpha_index"], c["Bstar"]): c for c in old["cells"]}
            seen = []
            for cell in measured["cells"]:
                key = cell["alpha_index"], cell["Bstar"]
                seen.append(key)
                source = old_by_cell[key]
                rows.append(audit_cell_binding(cell, source, nfp))
                if len(cell["families"]) != len(source["families"]):
                    family_checks.append({"all_expected_families": False})
                    continue
                family_checks.extend(
                    audit_family(a, b)
                    for a, b in zip(cell["families"], source["families"], strict=True)
                )
            checks["fixed_cells"] = len(seen) == len(set(seen)) == 40 and set(seen) == set(
                old_by_cell
            )
            checks["all_well_bindings"] = all(all(r.values()) for r in rows)
            checks["all_family_arithmetic"] = all(all(r.values()) for r in family_checks)
            families = [f for c in measured["cells"] for f in c["families"]]
            summary = dict(
                matched_families=len(families),
                failed_cells=sum(not c["matching_pass"] for c in measured["cells"]),
                changed_sign_families=sum(not f["gauge_signs_equal"] for f in families),
                sign_counts={
                    str(c): dict(Counter(f["gauges"][str(c)]["sign"] for f in families))
                    for c in (-1, 0, 1)
                },
            )
            checks["summary_arithmetic"] = summary == measured["summary"]
            record = dict(
                input=reference(path),
                checks={k: bool(v) for k, v in checks.items()},
                cell_checks=rows,
                family_checks=family_checks,
                summary=summary,
                all_pass=bool(all(checks.values())),
            )
            result["cases"].append(record)
    result["all_pass"] = all(c["all_pass"] for c in result["cases"])
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
