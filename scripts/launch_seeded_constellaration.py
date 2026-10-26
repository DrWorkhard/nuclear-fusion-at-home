"""One hash-bound #112 seeded task. Default invocation checks readiness only.

Adapted from the recorded-plasma v2 launcher. Reuses its published dual-clock
supervisor and radial resource guard read-only, with the stricter current grant
and <=60-second inventory rule. No scientific imports before child-side checks.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path

PROTOCOL_SHA256 = "df71882af62631557cc4bad55472e7a0a1f0bdb665a7f9c51fb1c602bea7303b"


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def resolve(root, relative):
    need(not Path(relative).is_absolute() and ".." not in Path(relative).parts,
         "manifest path leaves alignment root")
    # Preserve the virtualenv executable path; resolving its symlink loses pyvenv.cfg.
    return root / relative


def timestamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    need(result.tzinfo is not None, "timezone required")
    return result


def check_live(manifest, digest, root, *, now=None, require_full_window=False,
               owned_native_pid=None):
    now = datetime.now(UTC) if now is None else now
    coordination = root / "coordination"
    need(not (coordination / "automation/STOP").exists(), "STOP present")
    peer = coordination / "notes/claude.md"
    grant = manifest["peer_grant"]
    need(peer.read_text(encoding="utf-8").splitlines().count(grant["line"]) == 1,
         "current explicit task-specific peer grant missing")
    start, end = timestamp(grant["start"]), timestamp(grant["end"])
    remaining = 1800 if require_full_window else 0
    need(start <= now < end and (end-now).total_seconds() >= remaining,
         "peer window expired or too short")
    own = coordination / "notes/codex.md"
    pattern = rf"^C18-SEEDED-V1 CLAIM manifest={digest} start=(\S+) end=(\S+)$"
    matches = re.findall(pattern, own.read_text(encoding="utf-8"), re.MULTILINE)
    need(len(matches) == 1, "current owned manifest-specific claim missing")
    claim_start, claim_end = map(timestamp, matches[0])
    need(start <= claim_start <= now < claim_end <= end
         and (claim_end-now).total_seconds() >= remaining, "owned claim expired or too short")
    inventory = coordination / "automation/process-check.json"
    record = load(inventory)
    age = (now-timestamp(record["checked_at"])).total_seconds()
    need(0 <= age <= 60, "controller inventory must be <=60 seconds old")
    allowed = [] if owned_native_pid is None else [owned_native_pid]
    need(set(record["native_compute_pids"]) <= set(allowed), "native inventory occupied")
    need(record["controller_lock_held"] is True
         and record["other_codex_exec_worker"] is False, "controller ownership mismatch")
    return dict(peer_sha256=sha(peer), own_sha256=sha(own), controller_sha256=sha(inventory),
                controller=record, inventory_age_seconds=age, claim_end=claim_end.isoformat())


def verify_files(manifest, root):
    for relative, expected in manifest["files_sha256"].items():
        need(sha(resolve(root, relative)) == expected, f"frozen file mismatch: {relative}")
    need(sha(resolve(root, manifest["protocol"])) == PROTOCOL_SHA256, "comparison freeze changed")
    need(sha(Path(__file__)) == manifest["files_sha256"][manifest["launcher"]],
         "launcher identity mismatch")
    source = resolve(root, manifest["scorer_source"])
    head = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"],
                                   text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"],
                                    text=True).strip()
    need(head == manifest["scorer_commit"] and not dirty, "scorer source revision/dirty mismatch")
    limits = load(resolve(root, manifest["protocol"]))["limits"]
    need(manifest["limits"] == limits, "resource limits differ from public comparison freeze")


def module_from(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_resources(output, limits, *, initial=False):
    reserve = limits["start_disk_reserve_bytes" if initial else "runtime_disk_reserve_bytes"]
    need(shutil.disk_usage(output.parent if initial else output).free >= reserve,
         "disk reserve exhausted")
    if not initial:
        size = sum(path.stat().st_size for path in output.rglob("*") if path.is_file())
        need(size < limits["output_bytes"], "output size limit")


def child(manifest, digest, root, output, timer, guard):
    verify_files(manifest, root)
    guard.verify_runtime(manifest)
    check_live(manifest, digest, root, owned_native_pid=os.getpid())
    need((output / "preflight.json").is_file(), "parent preflight missing")
    write(output / "child-started.json", dict(manifest_sha256=digest, pid=os.getpid(),
                                             started_at=datetime.now(UTC).isoformat()))
    write(output / "environment.json", manifest["environment"])
    timing = load(output / "task-start.json")
    end = timestamp(check_live(manifest, digest, root,
                               owned_native_pid=os.getpid())["claim_end"]).timestamp()

    def check_ready():
        need(timer.deadline(timing["monotonic"], timing["utc"], 1800, end) is None,
             "global task deadline expired")
        verify_files(manifest, root)
        check_live(manifest, digest, root, owned_native_pid=os.getpid())
        check_resources(output, manifest["limits"])
        need(timer.deadline(timing["monotonic"], timing["utc"], 1800, end) is None,
             "global task deadline expired during readiness checks")

    # No solver/module import above this line.
    check_ready()
    from constellaration.mhd import vmec_settings
    sys.path.insert(0, str(resolve(root, manifest["launcher"]).parent))
    from run_seeded_constellaration import run_rows
    scorer = module_from("frozen_seeded_scorer", resolve(root, manifest["scorer"]))
    result = run_rows(scorer, vmec_settings, resolve(root, manifest["protocol"]),
                      {number: resolve(root, path) for number, path in manifest["inputs"].items()},
                      output / "rows", check_ready=check_ready)
    return 0 if result["completed"] else 1


def main():
    start_m, start_w = time.monotonic(), time.time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--alignment-root", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--child", action="store_true")
    args = parser.parse_args()
    need(sha(args.manifest) == args.manifest_sha256, "manifest hash mismatch")
    manifest, root = load(args.manifest), args.alignment_root.resolve()
    verify_files(manifest, root)
    timer = module_from("seeded_timer", resolve(root, manifest["supervisor"]))
    guard = module_from("seeded_guard", resolve(root, manifest["resource_guard"]))
    output = resolve(root, manifest["output"])
    if args.child:
        return child(manifest, args.manifest_sha256, root, output, timer, guard)
    need(not output.exists(), "output already exists; no repeat permitted")
    preflight = check_live(manifest, args.manifest_sha256, root, require_full_window=True)
    check_resources(output, manifest["limits"], initial=True)
    if not args.execute:
        print(json.dumps(dict(preflight=preflight, native_started=False)))
        return 0
    output.mkdir(exist_ok=False)
    for name in ("cache", "tmp"):
        (output / name).mkdir()
    write(output / "preflight.json", preflight)
    write(output / "task-start.json", dict(monotonic=start_m, utc=start_w))
    command = [str(resolve(root, manifest["native_python"])), "-B", str(Path(__file__).resolve()),
               "--manifest", str(args.manifest.resolve()),
               "--manifest-sha256", args.manifest_sha256,
               "--alignment-root", str(root), "--child"]
    end = timestamp(preflight["claim_end"]).timestamp()
    outcome = dict(completed=False, physical_admission=False, manifest_sha256=args.manifest_sha256)
    try:
        budget = min(1740, 1770-max(time.monotonic()-start_m, time.time()-start_w))
        need(budget > 0, "preflight exhausted task budget")
        execution = timer.supervise(command, output, guard.clean_environment(output),
                                    root / "coordination/automation/STOP",
                                    limits={**guard.LIMITS, "wall_seconds": budget},
                                    reservation_end=end)
        outcome["execution"] = execution
        need(execution["exit_code"] == 0 and execution["stop_reason"] is None,
             "native child incomplete; preserve failure without retry")
        verify_files(manifest, root)
        marker = load(output / "child-started.json")
        need(marker["manifest_sha256"] == args.manifest_sha256, "child identity mismatch")
        check_live(manifest, args.manifest_sha256, root, owned_native_pid=marker["pid"])
        check_resources(output, manifest["limits"])
        comparison = load(output / "rows/comparison.json")
        need(comparison["completed"] is True, "seeded workflow incomplete")
        outcome.update(comparison_sha256=sha(output / "rows/comparison.json"),
                       all_agree=comparison["all_agree"])
        need(timer.deadline(start_m, start_w, 1800, end) is None, "global task deadline expired")
        outcome["completed"] = True
    except (Exception, SystemExit):
        outcome["error"] = traceback.format_exc()
    finally:
        outcome.update(monotonic_seconds=time.monotonic()-start_m,
                       utc_elapsed_seconds=time.time()-start_w)
        write(output / "launch-result.json", outcome)
    return 0 if outcome["completed"] else 1


if __name__ == "__main__":
    sys.exit(main())
