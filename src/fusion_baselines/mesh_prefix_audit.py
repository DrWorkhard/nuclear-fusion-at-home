"""Exact prior spatial-certificate prefix without new geometry calculations."""

import gzip
import json

from fusion_baselines.mesh_nonlocal_audit import checked


def audit_prefix(old, new):
    partitions = []
    for record in (old, new):
        with gzip.open(checked(record["partition"]), "rt", encoding="utf-8") as stream:
            partitions.append(json.load(stream))
    a, b = partitions
    checks = {k: a[k] == b[k] for k in ("indices", "nodes", "padding")}
    checks["all_old_events"] = b["events"][:len(a["events"])] == a["events"]
    count, identical = 0, True
    with gzip.open(checked(old["witnesses"]), "rt", encoding="utf-8") as first:
        with gzip.open(checked(new["witnesses"]), "rt", encoding="utf-8") as second:
            for line in first:
                count += 1
                # JSON-independent byte-level equality is stricter than number equality.
                if line != second.readline():
                    identical = False
    checks["all_old_witnesses"] = identical and count == old["sat_calls"]
    checks["new_work_covers_prefix"] = new["sat_calls"] >= count
    return dict(checks=checks, old_witnesses_checked=count, all_pass=all(checks.values()),
                old_events_checked=len(a["events"]), new_physics_calls=0)
