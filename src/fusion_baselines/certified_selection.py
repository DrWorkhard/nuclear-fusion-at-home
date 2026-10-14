"""Latest geometry-certified checkpoint of a completed coil-fit recording (#109).

The fitter selects by sampled limits only. This rule re-reads a completed v3
recording, takes the best-so-far eligible point at fixed completed-bundle checkpoints
under the fitter's own selection rule, and certifies those points backward from the
run's selected point. The first that passes is selected: best-so-far values only
decrease, so it is the lowest-value certified checkpoint. The recording is only read.
"""

import copy
import hashlib
import json
import struct

import numpy as np

from fusion_baselines.coil_fit import RECORDING_FORMAT, VECTOR_STORE

SELECTION_ROLES = ("startup-seed", "search")
RULE = ("best-so-far eligible trial (fitter rule) at every k-th completed-bundle index and "
        "at the end; certified backward from the end; first pass selected")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value):
    """The value as it reads back from a recorded JSON file."""
    return json.loads(json.dumps(value, allow_nan=False))


def eligible(row, length_max):
    """Selection eligibility of coil_fit.search, applied to one recorded trial."""
    metrics = row.get("metrics") or {}
    return (row.get("status") == "completed" and row.get("role") in SELECTION_ROLES
            and metrics.get("sampled_geometry_limits_met") is True
            and metrics.get("current_limit_met") is True
            and max(metrics["lengths"]) <= length_max)


def selection_value(row):
    metrics = row["metrics"]
    return metrics.get("selection_value", metrics["normal_rms"])


def checkpoints(run, every):
    """[(checkpoint index, best-so-far eligible trial)] at every, 2*every, ... and the end."""
    if not isinstance(every, int) or isinstance(every, bool) or every < 1:
        raise ValueError("positive integer checkpoint spacing required")
    recording = read_json(run/"inputs.json")["recording"]
    if recording.get("format") != RECORDING_FORMAT:
        raise ValueError("recording v3 required")
    length_max = recording["constraints"]["selection"]["length_max_m"]
    attempted = read_json(run/"search.json")["bundles_attempted"]
    best, points = None, []
    for index in range(attempted):
        row = read_json(run/f"trial-{index:05}.json")
        if row.get("index") != index:
            raise ValueError(f"trial {index} records index {row.get('index')}")
        if eligible(row, length_max) and (best is None or selection_value(row)
                                          < selection_value(best)):
            best = row
        if index and index % every == 0 and best is not None:
            points.append((index, best))
    if best is None:
        raise ValueError("no eligible trial")
    if not points or points[-1][0] != attempted-1:
        points.append((attempted-1, best))
    return points


def vector(run, ref):
    """One referenced vector from the run's store, checked against its SHA-256."""
    if ref.get("store") != VECTOR_STORE:
        raise ValueError("vector store reference required")
    with (run/VECTOR_STORE).open("rb") as stream:
        stream.seek(ref["offset_bytes"])
        payload = stream.read(8*ref["count"])
    if len(payload) != 8*ref["count"] or hashlib.sha256(payload).hexdigest() != ref["sha256"]:
        raise ValueError("vector does not match its recorded SHA-256")
    return np.array(struct.unpack(f"<{ref['count']}d", payload))


def snapshot(seed, row, x):
    """Selected-snapshot construction of coil_fit.fine for one recorded trial."""
    scale = row["metrics"]["scale"]
    result = copy.deepcopy(seed)
    result.update(base_coefficients=np.asarray(x).reshape(6, 3, -1).tolist(), scale=scale,
                  unit_flux=row["metrics"]["unit_flux"])
    for coil in result["physical"]:
        coil["current"] = 1e5*scale*(-1 if coil["flip"] else 1)
    return result


def select(points, certify, certificates):
    """Certify distinct best-so-far trials backward, appending each certificate as it is
    made (so an interrupted search keeps them); returns the first passing trial or None."""
    seen = set()
    for checkpoint, row in reversed(points):
        if row["index"] in seen:
            continue
        seen.add(row["index"])
        certificate = dict(certify(row), checkpoint=checkpoint, index=row["index"],
                           selection_value=selection_value(row))
        certificates.append(certificate)
        if certificate["status"] == "pass":
            return row
    return None
