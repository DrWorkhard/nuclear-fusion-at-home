"""Stream independent candidate partition and every stored narrow-phase certificate."""

import gzip
import json
from pathlib import Path

import numpy as np

from fusion_baselines.provenance import sha256_file
from fusion_baselines.tetra_partition_audit import audit_partition
from fusion_baselines.tetra_witness_audit import audit_interior, audit_separation


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError("immutable certificate hash mismatch")
    return path


def audit_scan(points, cells, tags, source):
    with gzip.open(checked(source["partition"]), "rt", encoding="utf-8") as stream:
        partition = json.load(stream)
    processed = source["processed_candidates"]
    if type(processed) is not int or processed < 0:
        raise ValueError("explicit nonnegative processed-prefix length required")
    caps = source["caps"]
    if (source["status"] not in {"completed", "pair_cap", "time_cap", "error"}
            or source["sat_calls"] > caps["sat_pairs"]
            or (source["status"] == "pair_cap" and source["sat_calls"] != caps["sat_pairs"])
            or (source["status"] == "time_cap" and source["elapsed_seconds"] < caps["seconds"])
            or (source["status"] == "completed" and (
                not source["complete"] or source["elapsed_seconds"] > caps["seconds"]))):
        raise ValueError("consistent bounded terminal status required")
    counts = dict(processed_candidates=0, shared_vertex_pairs=0, sat_calls=0, lp_calls=0,
                  separated_pairs=0, positive_interior_pairs=0, unresolved_pairs=0,
                  narrow_errors=0, positive_within_tag=0, positive_between_tags=0)
    witness_checks = []
    with gzip.open(checked(source["witnesses"]), "rt", encoding="utf-8") as stream:
        def visit(pairs):
            for i, j in pairs:
                if counts["processed_candidates"] >= processed:
                    return
                counts["processed_candidates"] += 1
                if set(cells[i]).intersection(cells[j]):
                    counts["shared_vertex_pairs"] += 1
                    continue
                line = stream.readline()
                if not line:
                    raise ValueError("missing nonlocal witness in processed prefix")
                row = json.loads(line)
                if row["pair"] != [int(i), int(j)]:
                    raise ValueError("wrong, duplicate or out-of-order physical pair witness")
                counts["sat_calls"] += 1
                first, second = points[cells[i]], points[cells[j]]
                if "error" in row:
                    counts["narrow_errors"] += 1
                    # If separation completed, the reported exception occurred in the LP branch.
                    if "separation" in row:
                        if row["separation"]["status"] != "unresolved":
                            raise ValueError("failure branch inconsistent with stored separation")
                        counts["lp_calls"] += 1
                        if not audit_separation(first, second, row["separation"])["valid"]:
                            raise ValueError("invalid pre-error separation arithmetic")
                    continue
                sep = audit_separation(first, second, row["separation"])
                if not sep["valid"]:
                    raise ValueError("invalid independent separation projection")
                if sep["separation_verified"]:
                    if "interior" in row:
                        raise ValueError("unexpected LP after proven separation")
                    counts["separated_pairs"] += 1
                else:
                    counts["lp_calls"] += 1
                    inside = audit_interior(first, second, row["interior"])
                    if not inside["valid"]:
                        raise ValueError("invalid independent barycentric witness")
                    if inside["positive_interior_verified"]:
                        counts["positive_interior_pairs"] += 1
                        key = "positive_within_tag" if tags[i] == tags[j] else (
                            "positive_between_tags")
                        counts[key] += 1
                        witness_checks.append(dict(pair=[int(i), int(j)], positive_interior=True))
                    else:
                        counts["unresolved_pairs"] += 1
                        witness_checks.append(dict(pair=[int(i), int(j)], unresolved=True))
        broad = audit_partition(points, cells, np.asarray(partition["indices"]),
                                 partition["nodes"], partition["events"], partition["padding"],
                                 visit=visit)
        if stream.readline():
            raise ValueError("extra narrow-phase record outside physical processed prefix")
    if counts["processed_candidates"] != processed or any(counts[k] != source[k] for k in counts):
        raise ValueError("independent narrow-phase accounting mismatch")
    b = source["broad_phase"]
    if any(b[k] != broad[v] for k, v in (
            ("pairs_accounted", "covered_pairs"), ("candidates_delivered", "candidate_count"),
            ("box_separated_pairs", "box_separated_pairs"), ("nodes", "nodes"),
            ("events", "events"), ("total_pairs", "total_pairs"))):
        raise ValueError("independent broad-phase bookkeeping mismatch")
    # A generator can have no pending events yet remain unexhausted after its last yield.
    if b["finished"] and not broad["complete"]:
        raise ValueError("false completed generator flag")
    coverage = broad["complete"] and processed == broad["candidate_count"] and b["finished"]
    completed = coverage and source["status"] == "completed"
    if source["complete"] != completed:
        raise ValueError("false complete-scan claim")
    passed = completed and not any(counts[k] for k in (
        "positive_interior_pairs", "unresolved_pairs", "narrow_errors"))
    if source["nonlocal_screen_pass"] != passed:
        raise ValueError("false nonlocal admission classification")
    return dict(all_pass=True, independent_partition=broad, independent_counts=counts,
                exceptional_witnesses=witness_checks, complete=completed,
                nonlocal_screen_pass=passed, full_engineering_admission=False)
