"""Run cached-data QI/W7-X regressions with mandatory fixtures, never sync the environment."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from fusion_baselines.integration_audit import audit_integration_xml
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path, help="new immutable report directory")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    report, log = output / "tests.xml", output / "pytest.log"
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-rA",
        "tests/test_qi_data_integration.py",
        "tests/test_scientific_integration.py",
        f"--junitxml={report}",
    ]
    env = {**os.environ, "FUSION_REQUIRE_QI_DATA": "1", "FUSION_REQUIRE_W7X_DATA": "1"}
    completed = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True)
    log.write_text(completed.stdout + completed.stderr)
    audit = audit_integration_xml(report) if report.is_file() else {"all_pass": False}
    result = dict(
        schema_version=1,
        repository=git_state(root),
        command=command,
        required_data={k: env[k] for k in ("FUSION_REQUIRE_QI_DATA", "FUSION_REQUIRE_W7X_DATA")},
        returncode=completed.returncode,
        test_report_audit=audit,
        all_pass=completed.returncode == 0 and audit["all_pass"],
        scope="six cached-data regressions; no fresh solver/build or global QI qualification",
        log=reference(log),
        report=reference(report) if report.is_file() else None,
        code=[
            reference(root / p)
            for p in (
                "scripts/run_scientific_integration.py",
                "tests/conftest.py",
                "tests/test_qi_data_integration.py",
                "tests/test_scientific_integration.py",
                "src/fusion_baselines/integration_audit.py",
            )
        ],
    )
    write_json_atomic(output / "summary.json", result)
    print(json.dumps({"all_pass": result["all_pass"], "tests": audit}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
