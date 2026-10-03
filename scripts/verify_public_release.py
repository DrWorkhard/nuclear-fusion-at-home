"""Real starter qualification from an isolated path-free copy; retain every output.

No native solves/search or installation. Runs the preregistered public reference
and one explicitly non-optimized 1micrometre input-variation smoke check.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from fusion_public.data import canonical, load, save_new, sha  # noqa: E402


def verify(output):
    output.mkdir(parents=True, exist_ok=False)
    exported = output / "checkout with spaces"
    exported.mkdir()
    files = [ROOT / "fusion.py", ROOT / "scripts/test_public.py",
             ROOT / "scripts/verify_public_release.py"]
    for name in ("src/fusion_public", "public_tests", "examples"):
        files.extend(p for p in (ROOT / name).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts)
    records = {}
    for source in files:
        relative = source.relative_to(ROOT)
        target = exported / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        records[str(relative).replace(os.sep, "/")] = sha(target.read_bytes())
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("PYTHON", "VIRTUAL_ENV", "UV_"))}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    operations = []
    result = dict(schema_version=1, kind="public-release-local-qualification",
                  copied_files=records, operations=operations, complete=False,
                  hosted_ci_verified=False, physical_admission=False, step4_pass=False,
                  python_socket_audit_guard=True,
                  qualification_type="local copied tree, not an OS security sandbox")

    def run(label, arguments, expected=0):
        offline_runner = (
            "import runpy,sys\n"
            "def guard(event,args):\n"
            " if event.startswith('socket.'): raise RuntimeError('network disabled in replay')\n"
            "sys.addaudithook(guard)\n"
            "sys.argv=sys.argv[1:]\n"
            "runpy.run_path(sys.argv[0],run_name='__main__')\n"
        )
        command = [sys.executable, "-I", "-S", "-c", offline_runner, *arguments]
        started = time.monotonic()
        try:
            completed = subprocess.run(command, cwd=exported, env=env, text=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
        except subprocess.TimeoutExpired as error:
            # Timeout output can be bytes even with text=True, including a partial character.
            partial = error.stdout or ""
            if isinstance(partial, bytes):
                partial = partial.decode("utf-8", errors="replace")
            record = dict(label=label, argv=arguments, returncode=None,
                          expected_returncode=expected, elapsed_seconds=time.monotonic()-started,
                          output=partial, passed=False, timed_out=True,
                          timeout_seconds=error.timeout)
            save_new(output / f"{len(operations):02d}-{label}.json", record)
            operations.append(record)
            raise
        record = dict(label=label, argv=arguments, returncode=completed.returncode,
                      expected_returncode=expected, elapsed_seconds=time.monotonic()-started,
                      output=completed.stdout, passed=completed.returncode == expected)
        save_new(output / f"{len(operations):02d}-{label}.json", record)
        operations.append(record)
        if not record["passed"]:
            raise ValueError(f"Failed release check: {label}: {completed.stdout}")

    def cli(label, *args, expected=0):
        run(label, ["fusion.py", "public", *args], expected)

    try:
        run("public-unit-tests", ["scripts/test_public.py"])
        cli("discovery", "cases")
        cli("reference-demo", "demo", "--output", "results/reference")
        seed_report = load(exported / "results/reference/report.json")
        result["reference"] = dict(
            report_sha256=sha(canonical(seed_report)),
            reference_check=seed_report["seed_native_reference"],
            resolution_differences=seed_report["resolution_differences"],
            sampled_metrics_512=seed_report["levels"][1]["metrics"],
        )
        candidate = load(exported / "results/reference/candidate.json")
        candidate["base_coefficients"][0][0][0] += 1e-6
        save_new(exported / "results/changed-candidate.json", candidate)
        cli("changed-candidate", "evaluate", "--candidate", "results/changed-candidate.json",
            "--output", "results/changed-report.json")
        cli("changed-replay", "audit", "--report", "results/changed-report.json",
            "--output", "results/changed-audit.json")
        changed = load(exported / "results/changed-report.json")
        if changed["candidate_sha256"] == seed_report["candidate_sha256"]:
            raise ValueError("Candidate change did not affect identity")
        if changed["levels"][0]["fields"] == seed_report["levels"][0]["fields"]:
            raise ValueError("Candidate change did not affect computed fields")
        changed["scope"]["physical_admission"] = True
        save_new(exported / "results/tampered-report.json", changed)
        cli("reject-false-admission", "audit", "--report", "results/tampered-report.json",
            "--output", "results/should-not-exist.json", expected=2)
        if (exported / "results/should-not-exist.json").exists():
            raise ValueError("Rejected report produced a success artifact")
        cli("optional-cost", "check-submission", "--file", "examples/contribution.json")
        cli("reject-overwrite", "demo", "--output", "results/reference", expected=2)
        result["complete"] = True
    except Exception as error:
        result.update(error_type=type(error).__name__, error=str(error))
        raise
    finally:
        save_new(output / "qualification.json", result)
    print(json.dumps(dict(complete=True, output=str(output),
                          checks=len(operations), physical_admission=False), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    verify(parser.parse_args().output.resolve())
