"""Fixed-state, field-free local-curvature study; execution requires qualification.

The intake path only reads identities. Scientific imports and old-certificate
reconstruction occur inside separately supervised producer/auditor phases.
"""

import argparse
import hashlib
import json
import math
import os
import selectors
import shutil
import signal
import struct
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRATION = "evidence/local-curvature-registration-v1.json"
MANIFEST_SHA = "ca9c3bac130080cb261660abf18d6de29872c58f7d305114b06ee061969beca5"
CAPS = dict(t_depth=14, lambda_depth=10, evaluations=16383)
CURVE_BYTES, STATE_BYTES, INDEX_BYTES = 8 * 1024**2, 64 * 1024**2, 64 * 1024
RESERVE_BYTES = 3 * 1024**3
PHASE_SECONDS, HARD_SECONDS = 120.0, 125.0
GATES = {
    "regularity",
    "projection",
    "length",
    "curvature",
    "direct_plasma",
    "analytic_plasma",
    "direct_coil",
    "analytic_coil",
}
SCOPE = dict(
    interval_arithmetic=False,
    field_pass=False,
    physical_admission=False,
    step4_pass=False,
    ms1_reached=False,
)
SOURCE_PATHS = (
    REGISTRATION,
    "docs/geometry/LOCAL_CURVATURE_PROTOCOL.md",
    "evidence/local-curvature-inputs-v1.json",
    "scripts/run_local_curvature.py",
    "src/fusion_baselines/local_curvature.py",
    "src/fusion_baselines/local_curvature_audit.py",
    "src/fusion_baselines/coil_perturbation.py",
    "src/fusion_baselines/coil_perturbation_audit.py",
    "src/fusion_baselines/clear_coil_geometry_audit.py",
    "tests/test_local_curvature.py",
    "tests/test_local_curvature_audit.py",
    "tests/test_local_curvature_runner.py",
)


def need(condition, message):
    if not condition:
        raise ValueError(message)


def encode(value):
    return (
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        )
        + "\n"
    ).encode("utf-8")


def _unique(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def decode(raw):
    value = json.loads(raw, object_pairs_hook=_unique)
    encode(value)
    return value


def reference(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def read(ref, *, limit=STATE_BYTES):
    need(
        type(ref) is dict and set(ref) in ({"path", "sha256"}, {"path", "sha256", "bytes"}),
        "reference schema",
    )
    path = Path(ref["path"])
    need(path.is_absolute() and not path.is_symlink() and path.is_file(), "regular reference")
    need(type(ref["sha256"]) is str and len(ref["sha256"]) == 64, "reference digest")
    if "bytes" in ref:
        need(type(ref["bytes"]) is int and 0 < ref["bytes"] <= limit, "reference size")
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    need(
        0 < len(raw) <= limit and hashlib.sha256(raw).hexdigest() == ref["sha256"],
        "reference bytes/hash changed",
    )
    need("bytes" not in ref or len(raw) == ref["bytes"], "reference byte count changed")
    return decode(raw)


def same(first, second, label):
    need(encode(first) == encode(second), "exact identity: " + label)


def bits(values):
    need(
        type(values) is list and all(type(v) is float and math.isfinite(v) for v in values),
        "finite binary64 coordinates",
    )
    return struct.pack("<" + "d" * len(values), *values)


def flatten(coefficients):
    return [v for coil in coefficients for axis in coil for v in axis]


def names(nbase, order):
    modes = ["c(0)"] + [f"{part}({m})" for m in range(1, order + 1) for part in ("s", "c")]
    return [f"coil[{i}]/{axis}{mode}" for i in range(nbase) for axis in "xyz" for mode in modes]


def state_labels():
    return (
        ["seed-n6", "seed-n8"]
        + [
            f"{target}-n{n}-{method}"
            for target in ("reference", "selected")
            for n in (6, 8)
            for method in ("N", "V")
        ]
        + ["rejected-n6", "rejected-n8"]
    )


def intake(root=ROOT, *, guard=lambda: None):
    """Read only frozen metadata; deliberately does not import bound APIs."""
    guard()
    registration_ref = reference(Path(root) / REGISTRATION)
    registration = read(registration_ref)
    need(
        registration["kind"] == "local-homotopy-curvature-registration"
        and registration["registered_only"] is True,
        "registered protocol required",
    )
    for key in ("protocol", "inputs", "review"):
        guard()
        ref = registration[key]
        if key == "protocol":
            raw = Path(ref["path"]).read_bytes()
            need(
                len(raw) == ref["bytes"] and hashlib.sha256(raw).hexdigest() == ref["sha256"],
                "registered protocol changed",
            )
        else:
            read(ref)
    need(registration["inputs"]["sha256"] == MANIFEST_SHA, "fixed manifest identity")
    manifest = read(registration["inputs"])
    need([s["label"] for s in manifest["states"]] == state_labels(), "fixed twelve-state order")
    for ref in manifest["checked_references"]:
        guard()
        read(ref)
    guard()
    return registration_ref, manifest


def load_state(manifest, index, *, guard=lambda: None):
    """Bind original coefficients, proof and actual physical copies without evaluation."""
    need(type(index) is int and 0 <= index < 12, "fixed state index")
    row = manifest["states"][index]
    guard()
    seed, context, proof, geometry = (
        read(row[k]) for k in ("seed", "context", "old_certificate", "geometry_report")
    )
    original = context["original_context"]
    n, order = seed["nbase"], seed["order"]
    need(type(n) is type(order) is int and (n, order) in ((6, 5), (8, 7)), "registered shape")
    expected_names = names(n, order)
    same(seed["names"], expected_names, "original names")
    same(seed, original["seed"], "original seed")
    need(seed["nfp"] == 2 and seed["parameter_orientation"] == "alpha=-2*pi*t", "orientation")
    coefficients = seed["base_coefficients"]
    need(
        len(coefficients) == n
        and all(len(c) == 3 and all(len(a) == 2 * order + 1 for a in c) for c in coefficients),
        "complete coefficient shape",
    )
    seed_bits = bits(flatten(coefficients))
    need(row["named_parameter_count"] == len(expected_names) == len(proof["x"]), "named count")
    bits(proof["x"])
    for key, expected in dict(
        case=row["case"],
        original_seed=row["seed"],
        geometry_report=row["geometry_report"],
        geometry_report_index=row["geometry_report_index"],
    ).items():
        same(proof[key], expected, "old certificate " + key)
    same(context["case"], row["case"], "context case")
    same(original["case"], row["case"], "original case")
    same(original["seed_reference"], row["seed"], "seed reference")
    same(original["geometry_audit_reference"], row["geometry_report"], "geometry reference")
    need(
        row["geometry_report_index"] == original["geometry_report_index"] == (3 if n == 6 else 9),
        "original geometry index",
    )
    report = geometry["sets"][row["geometry_report_index"]]
    same(report, original["geometry_report"], "complete old geometry report")
    same(report["case"], seed["case"], "original geometry case")
    need(report["geometry_pass"] is True, "admitted original seed")
    digest = hashlib.sha256(
        encode(dict(schema_version=1, names=expected_names, x=proof["x"]))
    ).hexdigest()
    need(digest == row["state_sha256"] == proof["state_sha256"], "named coordinate digest")
    gates = proof["result"]["gates"]
    need(set(gates) == GATES and all(type(v) is bool for v in gates.values()), "eight old gates")
    same(gates, row["old_gates"], "old gates")
    need(all(v for k, v in gates.items() if k != "curvature"), "seven unchanged gates")
    need(len(seed["physical"]) == row["physical_copies"] == 4 * n, "all physical copies")
    for i, physical in enumerate(seed["physical"]):
        need(set(physical) == {"base_index", "matrix", "period", "flip"}, "physical schema")
        need(
            type(physical["base_index"]) is int
            and physical["base_index"] == i % n
            and type(physical["period"]) is int
            and physical["period"] == i // (2 * n)
            and type(physical["flip"]) is bool
            and physical["flip"] == bool(i // n % 2),
            "ordered physical-copy mapping",
        )
        matrix = physical["matrix"]
        need(
            type(matrix) is list and len(matrix) == 3 and all(len(r) == 3 for r in matrix),
            "physical matrix shape",
        )
        bits([v for r in matrix for v in r])
    width = 2 * order + 1
    candidate = [
        [proof["x"][(i * 3 + a) * width : (i * 3 + a + 1) * width] for a in range(3)]
        for i in range(n)
    ]
    for i, value in enumerate(proof["x"]):
        if i % width >= 5:
            need(bits([value]) == seed_bits[8 * i : 8 * (i + 1)], "inactive coordinate bits")
    if row["role"] == "original-seed":
        need(bits(proof["x"]) == seed_bits and all(gates.values()), "seed coordinate bits")
    elif row["role"] == "coarse-selection":
        snapshot = read(row["snapshot"])
        same(snapshot["names"], expected_names, "snapshot names")
        need(bits(flatten(snapshot["base_coefficients"])) == bits(proof["x"]), "snapshot bits")
        same(
            [{k: v for k, v in p.items() if k != "current"} for p in snapshot["physical"]],
            seed["physical"],
            "snapshot actual physical matrices",
        )
        same(row["snapshot"], context["coarse"]["selected_snapshot"], "selected snapshot")
        same(row["old_certificate"], context["coarse"]["selected_certificate"], "selected proof")
        same(proof, context["selected"]["certificate"], "embedded selected proof")
        need(all(gates.values()), "old selected gates")
    else:
        need(
            row["role"] == "curvature-only-rejection" and gates["curvature"] is False,
            "curvature-only rejected state",
        )
        search = read(row["search_report"])
        terminal = [
            t
            for t in search["trials"]
            if t["iteration"] == max(t["iteration"] for t in search["trials"])
        ]
        need(
            search["reason"] == "certificate-limited"
            and all(t["accepted"] is False for t in terminal),
            "final failed iteration",
        )
        chosen = None
        for trial in terminal:
            guard()
            old = read(trial["certificate"]["certificate_reference"])
            if trial["reason"] == "geometry-rejected" and {
                k for k, v in old["result"]["gates"].items() if not v
            } == {"curvature"}:
                chosen = trial
                break
        need(chosen is not None, "first curvature-only trial")
        same(chosen["certificate"]["certificate_reference"], row["old_certificate"], "chosen proof")
        need(
            bits(chosen["x"]) == bits(proof["x"])
            and chosen["evaluation"] is None
            and row["evaluated_field_bundle"] is False,
            "rejection without field evaluation",
        )
        for key in ("iteration", "backtrack"):
            same(chosen[key], row[key], "rejected " + key)
        same(chosen["index"], row["trial_index"], "rejected index")
    guard()
    return dict(row=row, seed=seed, candidate=candidate, old_proof=proof, geometry=report)


def _git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL)


def source_snapshot(root):
    return dict(
        commit=_git(root, "rev-parse", "HEAD").decode().strip(),
        sources=[reference(Path(root) / p) for p in SOURCE_PATHS],
    )


def execution_gate(checkpoint_ref, root=ROOT, *, guard=lambda: None):
    """Require committed actual qualification evidence and unchanged implementation."""
    guard()
    need(
        not _git(root, "status", "--porcelain", "--untracked-files=all").strip(),
        "clean source required",
    )
    checkpoint = read(checkpoint_ref)
    need(
        checkpoint.get("kind") == "local-curvature-execution-checkpoint"
        and type(checkpoint.get("schema_version")) is int
        and checkpoint.get("schema_version") == 1
        and checkpoint.get("execution_allowed") is True,
        "separate execution checkpoint required",
    )
    qualification = read(checkpoint["qualification"])
    need(
        qualification.get("kind") == "local-curvature-implementation-qualification"
        and qualification.get("status") == "completed",
        "completed implementation qualification",
    )
    for item in (checkpoint, qualification):
        need(
            item.get("field_pass") is False and item.get("step4_pass") is False, "nonphysical scope"
        )
    same(
        qualification.get("checks"),
        dict.fromkeys(("focused", "public", "docs", "full_regression", "independent_review"), True),
        "complete required qualification checks",
    )
    artifacts = qualification.get("artifacts")
    need(type(artifacts) is list and len(artifacts) >= 5, "retained qualification artifacts")
    for artifact in artifacts:
        guard()
        path = Path(artifact["path"])
        raw = path.read_bytes()
        need(
            len(raw) == artifact["bytes"] and hashlib.sha256(raw).hexdigest() == artifact["sha256"],
            "qualification artifact changed",
        )
    before = source_snapshot(root)
    for key in ("registration", "sources", "implementation_commit"):
        same(checkpoint[key], qualification[key], "qualified " + key)
    same(checkpoint["sources"], before["sources"], "complete required source list")
    same(checkpoint["registration"], reference(Path(root) / REGISTRATION), "registration")
    commit = checkpoint["implementation_commit"]
    need(type(commit) is str and len(commit) == 40, "implementation commit")
    _git(root, "merge-base", "--is-ancestor", commit, "HEAD")
    for ref in (checkpoint_ref, checkpoint["qualification"]):
        relative = Path(ref["path"]).relative_to(Path(root).resolve()).as_posix()
        need(
            hashlib.sha256(_git(root, "show", "HEAD:" + relative)).hexdigest() == ref["sha256"],
            "checkpoint/qualification must be committed",
        )
    for relative, ref in zip(SOURCE_PATHS, before["sources"], strict=True):
        guard()
        need(
            hashlib.sha256(_git(root, "show", commit + ":" + relative)).hexdigest()
            == ref["sha256"],
            "implementation source changed since qualified commit",
        )
    guard()
    return before


def publish(directory, name, payload, *, limit, clock, deadline, failure=False):
    """Exclusive, atomic publication; failed temporary files remain as evidence."""
    raw = encode(payload)
    need(len(raw) <= limit, "publication byte limit")
    cutoff = deadline + (HARD_SECONDS - PHASE_SECONDS if failure else 0)
    if clock() >= cutoff:
        raise TimeoutError("publication deadline")
    path = Path(directory) / name
    temporary = path.with_suffix(path.suffix + ".partial")
    with temporary.open("xb") as stream:
        need(stream.write(raw) == len(raw), "short report write")
        stream.flush()
        os.fsync(stream.fileno())
    if clock() >= cutoff:
        raise TimeoutError("publication deadline after serialization/write")
    os.link(temporary, path)  # Atomic no-overwrite publication in the owned directory.
    published = dict(
        path=str(path.resolve()), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()
    )
    try:
        descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        temporary.unlink()
        if clock() >= cutoff:
            raise TimeoutError("publication deadline after persistence")
    except Exception as error:
        # Linking happened even though persistence/timing did not complete.
        # Callers retain these exact bytes under failure, without republishing.
        error.published_reference = published
        raise
    return published


def _guard(clock, deadline):
    now = clock()
    need(type(now) in (int, float) and math.isfinite(now), "finite monotonic clock")
    if now >= deadline:
        raise TimeoutError("phase deadline")


def reconstruct_old(data, phase):
    from fusion_baselines.coil_perturbation_audit import (
        audit_certificate,
        compare_certificate,
    )

    if phase == "producer":
        from fusion_baselines.coil_perturbation import candidate_certificate

        result = candidate_certificate(data["seed"], data["geometry"], data["candidate"])
        compare_certificate(result, data["old_proof"]["result"])
    else:
        result = audit_certificate(
            data["seed"], data["geometry"], data["candidate"], data["old_proof"]["result"]
        )
    return result


def _curve(data, physical, phase, recorded, deadline, clock):
    base = physical["base_index"]
    args = (data["seed"]["base_coefficients"][base], data["candidate"][base], physical["matrix"])
    if phase == "producer":
        from fusion_baselines.local_curvature import certify_curve

        return certify_curve(*args, deadline=deadline, clock=clock, caps=dict(CAPS))
    from fusion_baselines.local_curvature_audit import audit_curve

    same(recorded["caps"], CAPS, "registered curve caps")
    return audit_curve(*args, recorded, deadline=deadline, clock=clock)


def run_phase(
    data,
    phase,
    output,
    *,
    deadline,
    clock=time.monotonic,
    producer_index=None,
    old=reconstruct_old,
    curve=_curve,
    emit=lambda row: None,
    writer=publish,
    prior_bytes=0,
    index_reserve=INDEX_BYTES,
):
    """Bounded state computation; callbacks permit small synthetic timing tests."""
    need(phase in ("producer", "audit"), "phase")
    physical = data["seed"]["physical"]
    rows = [dict(index=i, status="unchecked", reference=None) for i in range(len(physical))]
    status, error, used, old_match, old_gates = "complete", None, 0, False, None
    try:
        _guard(clock, deadline)
        old_result = old(data, phase)
        _guard(clock, deadline)
        same(old_result["gates"], data["old_proof"]["result"]["gates"], "reconstructed old gates")
        old_gates, old_match = old_result["gates"], True
        if phase == "audit":
            need(producer_index is not None, "explicit producer index required")
            same(producer_index["state_sha256"], data["row"]["state_sha256"], "producer state")
            need(len(producer_index["curves"]) == len(physical), "producer copy coverage")
        for i, mapping in enumerate(physical):
            _guard(clock, deadline)
            if prior_bytes + used + CURVE_BYTES + index_reserve > STATE_BYTES:
                status = "report-budget"
                break
            recorded, producer_ref = None, None
            if phase == "audit":
                entry = producer_index["curves"][i]
                need(entry["index"] == i, "producer ordered copies")
                if entry["status"] != "published":
                    status = "incomplete-producer"
                    break
                producer_ref = entry["reference"]
                envelope = read(producer_ref, limit=CURVE_BYTES)
                same(envelope["physical"], mapping, "actual saved copy matrix")
                same(envelope["state_sha256"], data["row"]["state_sha256"], "curve state")
                need(envelope["index"] == i and envelope["phase"] == "producer", "producer curve")
                recorded = envelope["result"]
            result = curve(data, mapping, phase, recorded, deadline, clock)
            expired = clock() >= deadline
            if phase == "producer":
                same(result["caps"], CAPS, "registered curve caps")
            else:
                need(result.get("audit_pass") is True, "independent arithmetic audit")
            need(
                all(
                    result.get(k) is False
                    for k in ("interval_arithmetic", "field_pass", "step4_pass")
                ),
                "curve nonphysical scope",
            )
            payload = dict(
                schema_version=1,
                kind="local-curvature-physical-copy",
                phase=phase,
                index=i,
                physical=mapping,
                state_sha256=data["row"]["state_sha256"],
                producer_report=producer_ref,
                result=result,
                **SCOPE,
            )
            try:
                ref = writer(
                    output,
                    f"curve-{i:02d}.json",
                    payload,
                    limit=CURVE_BYTES,
                    clock=clock,
                    deadline=deadline,
                    failure=expired,
                )
            except TimeoutError:
                # Keep the complete attempted frontier if serialization/persistence
                # crossed the soft deadline. The original tail is never overwritten.
                expired = True
                published = Path(output) / f"curve-{i:02d}.json"
                if published.is_file():
                    ref = reference(published)
                    same(read(ref, limit=CURVE_BYTES), payload, "late published curve")
                else:
                    payload["timed_failure"] = True
                    ref = writer(
                        output,
                        f"curve-{i:02d}-deadline.json",
                        payload,
                        limit=CURVE_BYTES,
                        clock=clock,
                        deadline=deadline,
                        failure=True,
                    )
            used += ref["bytes"]
            need(prior_bytes + used + index_reserve <= STATE_BYTES, "state report byte limit")
            rows[i] = dict(
                index=i,
                status="published",
                reference=ref,
                curvature_pass=result["curvature_pass"] is True,
            )
            emit(dict(event="curve", index=i, reference=ref))
            if expired or result.get("stop_reason") == "deadline":
                raise TimeoutError("curve deadline")
            _guard(clock, deadline)
        if phase == "audit" and producer_index["status"] != "complete":
            status = "incomplete-producer"
    except Exception as caught:
        status = "deadline" if isinstance(caught, TimeoutError) else "error"
        error = dict(type=type(caught).__name__, message=str(caught)[:1000])
        linked = getattr(caught, "published_reference", None)
        if linked is not None:
            need(rows[i]["reference"] is None, "one failed publication per curve")
            used += linked["bytes"]
            rows[i] = dict(
                index=i,
                status="published",
                reference=linked,
                curvature_pass=result["curvature_pass"] is True,
            )
            emit(dict(event="curve", index=i, reference=linked))
            error["publication_reference"] = linked
    if clock() >= deadline:
        status = "deadline"
    complete = status == "complete" and all(r["status"] == "published" for r in rows)
    curvature_pass = complete and all(r.get("curvature_pass") is True for r in rows)
    result = dict(
        schema_version=1,
        kind="local-curvature-state-phase",
        phase=phase,
        state_sha256=data["row"]["state_sha256"],
        label=data["row"]["label"],
        status=status,
        complete=complete,
        old_certificate_matched=old_match,
        old_gates=old_gates,
        curves=rows,
        curve_report_bytes=used,
        error=error,
        curvature_pass=curvature_pass,
        old_geometry_pass=data["old_proof"]["result"]["certified"],
        local_geometry_pass=curvature_pass
        and old_match
        and all(value for key, value in old_gates.items() if key != "curvature"),
        **SCOPE,
    )
    try:
        ref = writer(
            output,
            "index.json",
            result,
            limit=min(INDEX_BYTES // 2, index_reserve),
            clock=clock,
            deadline=deadline,
            failure=not complete,
        )
    except TimeoutError:
        result.update(
            status="deadline", complete=False, curvature_pass=False, local_geometry_pass=False
        )
        status, complete = "deadline", False
        published = Path(output) / "index.json"
        if published.is_file():
            ref = reference(published)
        else:
            ref = writer(
                output,
                "failure-index.json",
                result,
                limit=min(INDEX_BYTES // 2, index_reserve),
                clock=clock,
                deadline=deadline,
                failure=True,
            )
    need(prior_bytes + used + ref["bytes"] <= STATE_BYTES, "total state report limit")
    if clock() >= deadline:
        return dict(status="deadline", complete=False, index=ref, **SCOPE)
    return dict(status=status, complete=complete, index=ref, **SCOPE)


def worker(config):
    deadline, parent_pid = config["deadline"], config["parent_pid"]

    def guard():
        need(os.getppid() == parent_pid, "owned parent lost")
        _guard(time.monotonic, deadline)

    before = execution_gate(config["checkpoint"], config["root"], guard=guard)
    _, manifest = intake(config["root"], guard=guard)
    data = load_state(manifest, config["index"], guard=guard)
    producer = (
        read(config["producer_index"], limit=INDEX_BYTES) if config["producer_index"] else None
    )

    def emit(event):
        print(encode(event).decode().strip(), flush=True)

    result = run_phase(
        data,
        config["phase"],
        config["output"],
        deadline=deadline,
        producer_index=producer,
        emit=emit,
        prior_bytes=config.get("prior_bytes", 0),
        index_reserve=config.get("index_reserve", INDEX_BYTES),
    )
    if time.monotonic() < deadline:
        same(source_snapshot(config["root"]), before, "phase source before/after")
    if time.monotonic() >= deadline:
        result.update(status="deadline", complete=False)
    emit(dict(event="return", result=result))
    return 0


def state_identity(data):
    return dict(
        label=data["row"]["label"],
        state_sha256=data["row"]["state_sha256"],
        physical=data["seed"]["physical"],
        old_gates=data["old_proof"]["result"]["gates"],
        old_geometry_pass=data["old_proof"]["result"]["certified"],
    )


def validate_return(config, returned, prefix):
    """Parent reconstructs structural success from every explicitly returned copy."""
    need(set(returned) == {"status", "complete", "index"} | set(SCOPE), "return schema")
    need(all(returned[k] is False for k in SCOPE), "returned nonphysical scope")
    output = Path(config["output"])
    need(
        Path(returned["index"]["path"]) in {output / "index.json", output / "failure-index.json"},
        "owned returned index",
    )
    index = read(returned["index"], limit=INDEX_BYTES // 2)
    keys = {
        "schema_version",
        "kind",
        "phase",
        "state_sha256",
        "label",
        "status",
        "complete",
        "old_certificate_matched",
        "old_gates",
        "curves",
        "curve_report_bytes",
        "error",
        "curvature_pass",
        "old_geometry_pass",
        "local_geometry_pass",
    } | set(SCOPE)
    need(set(index) == keys, "exact state index schema")
    need(
        type(index["schema_version"]) is int
        and index["schema_version"] == 1
        and index["kind"] == "local-curvature-state-phase",
        "state schema identity",
    )
    identity = config["state_identity"]
    for key in ("state_sha256", "label", "old_geometry_pass"):
        same(index[key], identity[key], "returned " + key)
    same(index["phase"], config["phase"], "returned phase")
    need(all(index[k] is False for k in SCOPE), "index nonphysical scope")
    need(type(index["old_certificate_matched"]) is bool, "old certificate match flag")
    if index["old_certificate_matched"]:
        same(index["old_gates"], identity["old_gates"], "returned old gates")
    else:
        need(index["old_gates"] is None, "unmatched old certificate")
    physical = identity["physical"]
    need(
        type(physical) is list
        and len(physical) > 0
        and type(index["curves"]) is list
        and len(index["curves"]) == len(physical),
        "complete nonempty expected physical-copy count",
    )
    actual, passes, used, unchecked, timed_failure = [], [], 0, False, False
    producer = (
        read(config["producer_index"], limit=INDEX_BYTES // 2)
        if config["phase"] == "audit"
        else None
    )
    for i, (row, mapping) in enumerate(zip(index["curves"], physical, strict=True)):
        need(type(row["index"]) is int and row["index"] == i, "ordered returned copies")
        if row["status"] == "unchecked":
            need(
                set(row) == {"index", "status", "reference"} and row["reference"] is None,
                "unchecked row schema",
            )
            unchecked = True
            continue
        need(
            not unchecked
            and row["status"] == "published"
            and set(row) == {"index", "status", "reference", "curvature_pass"},
            "published prefix schema",
        )
        need(type(row["curvature_pass"]) is bool, "curve pass flag")
        ref = row["reference"]
        need(
            Path(ref["path"])
            in {output / f"curve-{i:02d}.json", output / f"curve-{i:02d}-deadline.json"},
            "owned indexed curve",
        )
        envelope = read(ref, limit=CURVE_BYTES)
        envelope_keys = {
            "schema_version",
            "kind",
            "phase",
            "index",
            "physical",
            "state_sha256",
            "producer_report",
            "result",
        } | set(SCOPE)
        need(
            set(envelope) in (envelope_keys, envelope_keys | {"timed_failure"}),
            "copy envelope schema",
        )
        need(
            envelope["kind"] == "local-curvature-physical-copy"
            and type(envelope["schema_version"]) is int
            and envelope["schema_version"] == 1,
            "copy envelope identity",
        )
        need(all(envelope[k] is False for k in SCOPE), "copy envelope nonphysical scope")
        same(envelope["index"], i, "envelope index")
        same(envelope["phase"], config["phase"], "envelope phase")
        same(envelope["state_sha256"], identity["state_sha256"], "envelope state")
        same(envelope["physical"], mapping, "original physical matrix")
        if "timed_failure" in envelope:
            need(envelope["timed_failure"] is True, "deadline failure flag")
            timed_failure = True
        report = envelope["result"]
        need(
            type(report.get("schema_version")) is int and report["schema_version"] == 1,
            "curve result schema version",
        )
        need(
            type(report.get("curvature_pass")) is bool
            and all(
                report.get(k) is False for k in ("interval_arithmetic", "field_pass", "step4_pass")
            ),
            "curve result scope and pass flag",
        )
        if config["phase"] == "producer":
            need(
                set(report)
                == {
                    "schema_version",
                    "kind",
                    "caps",
                    "nodes",
                    "attempted",
                    "curvature_pass",
                    "stop_reason",
                    "interval_arithmetic",
                    "field_pass",
                    "step4_pass",
                }
                and report["kind"] == "local-homotopy-curvature",
                "producer result schema",
            )
            need(envelope["producer_report"] is None, "producer has no producer-report parent")
            same(report["caps"], CAPS, "parent registered caps")
            need(
                type(report["nodes"]) is list and 0 < len(report["nodes"]) <= 16408,
                "nonempty bounded node report",
            )
            need(
                type(report["attempted"]) is int
                and report["attempted"] == sum(node[1] != "pending" for node in report["nodes"]),
                "parent attempted count",
            )
            passing = (
                report["stop_reason"] == "complete"
                and any(node[1] == "pass" for node in report["nodes"])
                and all(node[1] in ("pass", "split_t", "split_l") for node in report["nodes"])
            )
            same(report["curvature_pass"], passing, "producer reported leaf aggregate")
        else:
            need(
                set(report)
                == {
                    "schema_version",
                    "kind",
                    "audit_pass",
                    "curvature_pass",
                    "attempted",
                    "nodes_checked",
                    "passing_leaves",
                    "unresolved_leaves",
                    "pending_leaves",
                    "interval_arithmetic",
                    "field_pass",
                    "step4_pass",
                }
                and report["kind"] == "local-homotopy-curvature-audit",
                "audit result schema",
            )
            need(report.get("audit_pass") is True, "independent curve audit pass")
            same(
                envelope["producer_report"],
                producer["curves"][i]["reference"],
                "independent audit original producer curve",
            )
            need(
                all(
                    type(report[k]) is int and report[k] >= 0
                    for k in (
                        "attempted",
                        "nodes_checked",
                        "passing_leaves",
                        "unresolved_leaves",
                        "pending_leaves",
                    )
                ),
                "audit work counts",
            )
            original = read(envelope["producer_report"], limit=CURVE_BYTES)["result"]
            passing = (
                original["stop_reason"] == "complete"
                and report["passing_leaves"] > 0
                and report["unresolved_leaves"] == report["pending_leaves"] == 0
            )
            same(report["curvature_pass"], passing, "audit reported leaf aggregate")
        same(row["curvature_pass"], report["curvature_pass"], "copy classification")
        passes.append(report["curvature_pass"])
        used += ref["bytes"]
        actual.append(ref)
    same(actual, prefix, "explicit returned prefix")
    need(
        type(index["curve_report_bytes"]) is int and used == index["curve_report_bytes"],
        "published curve byte accounting",
    )
    need(
        config.get("prior_bytes", 0) + used + returned["index"]["bytes"] <= STATE_BYTES,
        "shared state report byte limit",
    )
    complete = (
        index["status"] == "complete"
        and not unchecked
        and not timed_failure
        and index["old_certificate_matched"]
        and index["error"] is None
    )
    if producer is not None:
        complete = complete and producer["complete"] is True and producer["status"] == "complete"
    same(index["complete"], bool(complete), "reconstructed complete status")
    curvature = bool(complete and all(passes))
    same(index["curvature_pass"], curvature, "reconstructed curvature aggregate")
    same(
        index["local_geometry_pass"],
        bool(
            curvature
            and all(value for key, value in identity["old_gates"].items() if key != "curvature")
        ),
        "seven-gate local geometry aggregate",
    )
    return bool(complete and returned["complete"] is True and returned["status"] == "complete")


def supervise(config, *, clock=time.monotonic, popen=subprocess.Popen):
    """One child process group, bounded control stream, no discovery-based success."""
    output = Path(config["output"])
    output.mkdir(exist_ok=False)
    started = clock()
    config = dict(config, parent_pid=os.getpid(), deadline=started + PHASE_SECONDS)
    config_ref = publish(
        output, "config.json", config, limit=INDEX_BYTES, clock=clock, deadline=config["deadline"]
    )
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", json.dumps(config_ref)]
    env = dict(os.environ, PYTHONPATH=str(Path(config["root"]) / "src"))
    for key in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ):
        env[key] = "1"
    _guard(clock, config["deadline"])
    child = popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        env=env,
    )
    received, raw, error = [], bytearray(), None
    selector = selectors.DefaultSelector()
    selector.register(child.stdout, selectors.EVENT_READ)
    try:
        while selector.get_map():
            if clock() >= started + HARD_SECONDS:
                raise TimeoutError("hard supervisor deadline")
            for key, _ in selector.select(
                timeout=min(0.05, max(0, started + HARD_SECONDS - clock()))
            ):
                chunk = os.read(key.fd, 4096)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                raw.extend(chunk)
                need(len(raw) <= INDEX_BYTES, "bounded control stream")
        child.wait(timeout=max(0.001, started + HARD_SECONDS - clock()))
    except Exception as caught:
        error = dict(type=type(caught).__name__, message=str(caught)[:1000])
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            child.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            error["reap_timeout"] = True
    finally:
        selector.close()
        child.stdout.close()
    # A killed worker can still have explicitly returned a valid prefix.
    for line in bytes(raw).splitlines():
        try:
            received.append(decode(line))
        except (ValueError, UnicodeError):
            error = error or dict(type="ValueError", message="malformed control event")
            break
    returned, prefix, complete, validated = None, [], False, False
    try:
        for event in received:
            need(type(event) is dict, "mapping control event required")
            if event.get("event") == "curve" and returned is None:
                need(
                    set(event) == {"event", "index", "reference"}
                    and type(event["index"]) is int
                    and event["index"] == len(prefix),
                    "ordered explicit prefix",
                )
                ref = event["reference"]
                need(
                    Path(ref["path"])
                    in {
                        output / f"curve-{len(prefix):02d}.json",
                        output / f"curve-{len(prefix):02d}-deadline.json",
                    },
                    "owned curve path",
                )
                read(ref, limit=CURVE_BYTES)
                prefix.append(ref)
            elif event.get("event") == "return" and returned is None:
                need(set(event) == {"event", "result"}, "return control schema")
                returned = event["result"]
            else:
                raise ValueError("invalid control sequence: " + str(event)[:1000])
        if returned is not None:
            complete = validate_return(config, returned, prefix)
            validated = True
    except Exception as caught:
        error = error or dict(type=type(caught).__name__, message=str(caught)[:1000])
        complete = False
    timely = clock() < started + PHASE_SECONDS
    result = dict(
        schema_version=1,
        kind="local-curvature-parent-phase",
        phase=config["phase"],
        config=config_ref,
        returned=returned,
        returned_validated=validated,
        prefix=prefix,
        error=error,
        returncode=child.returncode,
        elapsed_seconds=clock() - started,
        complete=complete and timely and child.returncode == 0 and error is None,
        **SCOPE,
    )
    # Supervisor failure metadata remains publishable after killing a child at
    # 125s. This separate bounded write cannot acknowledge a successful phase.
    publication_deadline = started + PHASE_SECONDS if result["complete"] else clock()
    try:
        ref = publish(
            output,
            "parent.json",
            result,
            limit=INDEX_BYTES,
            clock=clock,
            deadline=publication_deadline,
            failure=not result["complete"],
        )
    except TimeoutError:
        result["complete"] = False
        prior = output / "parent.json"
        if prior.is_file():
            result["superseded_acknowledgement"] = reference(prior)
        ref = publish(
            output,
            "parent-failure.json",
            result,
            limit=INDEX_BYTES,
            clock=clock,
            deadline=clock(),
            failure=True,
        )
    if clock() >= started + PHASE_SECONDS and result["complete"]:
        result["complete"] = False
        result["superseded_acknowledgement"] = ref
        result["error"] = dict(type="TimeoutError", message="deadline after parent publication")
        result["elapsed_seconds"] = clock() - started
        ref = publish(
            output,
            "parent-failure.json",
            result,
            limit=INDEX_BYTES,
            clock=clock,
            deadline=clock(),
            failure=True,
        )
    return result, ref


def run_study(output, checkpoint_ref, root=ROOT):
    before = execution_gate(checkpoint_ref, root)
    _, manifest = intake(root)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    rows, stop = [], None
    for index, label in enumerate(state_labels()):
        if shutil.disk_usage(output).free < RESERVE_BYTES:
            stop = "low-disk"
            break
        directory = output / f"state-{index:02d}-{label}"
        directory.mkdir()
        config = dict(
            root=str(Path(root).resolve()),
            checkpoint=checkpoint_ref,
            index=index,
            producer_index=None,
            output=str(directory / "producer"),
            phase="producer",
            state_identity=state_identity(load_state(manifest, index)),
            prior_bytes=0,
            index_reserve=INDEX_BYTES,
        )
        producer, producer_ref = supervise(config)
        audit, audit_ref = None, None
        if producer["returned_validated"]:
            config.update(
                phase="audit",
                output=str(directory / "audit"),
                producer_index=producer["returned"]["index"],
                prior_bytes=(
                    sum(ref["bytes"] for ref in producer["prefix"])
                    + producer["returned"]["index"]["bytes"]
                ),
                index_reserve=INDEX_BYTES - producer["returned"]["index"]["bytes"],
            )
            audit, audit_ref = supervise(config)
        rows.append(
            dict(
                index=index,
                label=label,
                producer=producer_ref,
                audit=audit_ref,
                complete=producer["complete"] and audit is not None and audit["complete"],
            )
        )
    after = source_snapshot(root)
    result = dict(
        schema_version=1,
        kind="local-curvature-fixed-study",
        source_before=before,
        source_after=after,
        source_unchanged=before == after,
        states=rows,
        unchecked=state_labels()[len(rows) :],
        stop_reason=stop,
        complete=len(rows) == 12 and all(r["complete"] for r in rows) and before == after,
        **SCOPE,
    )
    ref = publish(
        output,
        "study.json",
        result,
        limit=INDEX_BYTES,
        clock=time.monotonic,
        deadline=time.monotonic() + 5,
        failure=True,
    )
    return dict(result, returned_index=ref)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--intake", action="store_true")
    group.add_argument("--output", type=Path)
    group.add_argument("--worker", help=argparse.SUPPRESS)
    parser.add_argument("--checkpoint", type=Path)
    args = parser.parse_args()
    if args.worker:
        try:
            return worker(read(json.loads(args.worker), limit=INDEX_BYTES))
        except Exception as error:
            print(
                encode(dict(event="error", type=type(error).__name__, message=str(error)[:1000]))
                .decode()
                .strip(),
                flush=True,
            )
            return 1
    if args.intake:
        registration, manifest = intake()
        for i in range(12):
            load_state(manifest, i)
        print(
            encode(
                dict(
                    status="intake-pass",
                    states=12,
                    registration=registration,
                    new_bound_evaluations=0,
                    **SCOPE,
                )
            )
            .decode()
            .strip()
        )
        return 0
    need(args.checkpoint is not None, "committed execution checkpoint required")
    result = run_study(args.output, reference(args.checkpoint))
    print(
        encode(dict(complete=result["complete"], returned_index=result["returned_index"], **SCOPE))
        .decode()
        .strip()
    )
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
