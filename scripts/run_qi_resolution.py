"""Sixteen frozen QI cold starts with independent input checks and retained failures."""

import argparse
import json
import os
import subprocess
from pathlib import Path

import f90nml
from inventory_qi_producers import reference
from run_jac_scaled_study import require_committed

from fusion_baselines.provenance import git_state, host_state, sha256_file, write_json_atomic
from fusion_baselines.qi_resolution import MATRIX, author_input_checks, check_effective
from fusion_baselines.resource_guard import GIB, space_check


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError(f"changed bound source: {path}")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new immutable study paths required")
    root = Path(__file__).resolve().parents[1]
    space_check(root, 3 * GIB)
    inventory = root / "evidence/qi-producer-inventory-v1.json"
    old = json.loads(inventory.read_text())
    code = [root / p for p in (
        "scripts/run_qi_resolution.py", "scripts/qi_equilibrium_worker.py",
        "src/fusion_baselines/qi_resolution.py")]
    protocol = root / "docs/qi/QI_FRESH_RESOLUTION_PROTOCOL.md"
    for p in [inventory, protocol, *code]:
        require_committed(root, p)
    for ref in old["vmecpp"]["sources"]:
        checked(ref)
    interpreter = root / "environments/vmecpp/.venv/bin/python"
    worker = root / "scripts/qi_equilibrium_worker.py"
    args.raw.mkdir(parents=True)
    report = dict(repository=git_state(root), host=host_state(), status="running", cells=[],
                  inventory=reference(inventory), protocol=reference(protocol),
                  code=[reference(p) for p in code], solver=old["vmecpp"],
                  lock=reference(root / "environments/vmecpp/uv.lock"),
                  all_numerically_converged=False, absolute_drift_certified=False,
                  exact_historical_reproduction=False,
                  threads={k: os.environ.get(k) for k in (
                      "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")})
    try:
        for case in old["cases"]:
            source = checked(case["input"])
            nml = f90nml.read(source)["indata"]
            for ns, angular in MATRIX:
                space_check(root, 2 * GIB)
                folder = args.raw / f"{case['case']}-s{ns}-a{angular}"
                row = dict(case=case["case"], ns=ns, angular=angular, input=case["input"],
                           historical_wout=case["wout"], directory=str(folder.resolve()),
                           status="preparing")
                report["cells"].append(row)
                write_json_atomic(args.output, report)
                prepare = [str(interpreter), str(worker), "prepare", str(folder),
                           "--input", str(source), "--ns", str(ns), "--angular", str(angular)]
                process = subprocess.run(prepare, capture_output=True, text=True, check=False,
                                         cwd=root, timeout=60)
                row["prepare"] = dict(command=prepare, returncode=process.returncode,
                                      stdout=process.stdout, stderr=process.stderr)
                if process.returncode != 0:
                    raise ValueError("input preparation failed; no unchecked solve allowed")
                original = json.loads((folder / "original_input.json").read_text())
                effective = json.loads((folder / "effective_input.json").read_text())
                row["author_checks"] = author_input_checks(nml, original)
                row["effective_controls_match"] = check_effective(original, effective, ns, angular)
                row["original"] = reference(folder / "original_input.json")
                row["effective"] = reference(folder / "effective_input.json")
                if not all(row["author_checks"].values()) or not row["effective_controls_match"]:
                    raise ValueError("independent input qualification failed")
                command = [str(interpreter), str(worker), "solve", str(folder)]
                row.update(status="running", command=command)
                write_json_atomic(args.output, report)
                log = folder / "solver.log"
                with log.open("xb") as stream:
                    try:
                        process = subprocess.run(command, cwd=root, stdout=stream,
                                                 stderr=subprocess.STDOUT, timeout=1800,
                                                 check=False)
                        row.update(status="completed" if process.returncode in (0, 2) else "failed",
                                   returncode=process.returncode, timeout=False)
                    except subprocess.TimeoutExpired:
                        row.update(status="timeout", returncode=None, timeout=True)
                row["log"] = reference(log)
                if (folder / "solver.json").exists():
                    row["solver"] = reference(folder / "solver.json")
                    row["numerically_converged"] = json.loads(
                        (folder / "solver.json").read_text())["numerically_converged"]
                else:
                    row["numerically_converged"] = False
                if (folder / "wout.nc").exists():
                    row["wout"] = reference(folder / "wout.nc")
                write_json_atomic(args.output, report)
                print(row["case"], ns, angular, row["status"], row["numerically_converged"],
                      flush=True)
        report.update(status="completed", all_numerically_converged=all(
            r["status"] == "completed" and r["numerically_converged"] for r in report["cells"]))
    except Exception as error:
        report.update(status="error", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.output, report)
    return 0 if report["all_numerically_converged"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
