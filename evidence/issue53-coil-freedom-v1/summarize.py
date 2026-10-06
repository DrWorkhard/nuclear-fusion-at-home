"""Post-run reduction of the frozen issue-53 records; no new optimization."""

import hashlib
import json
from datetime import datetime
from pathlib import Path

PRODUCER = "fd99245147308b9dbd23473002968e3283bd08fe"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def summarize(root):
    study = read(root/"run/study.json")
    assert study["completed"] and study["sources_before"] == study["sources_after"]
    assert study["provenance"]["repository"]["commit"] == PRODUCER
    assert study["provenance"]["repository"]["dirty"] is False
    result = dict(producer=PRODUCER, producer_dirty=False, completed=True,
                  physical_admission=False, search_seconds=1800, diagnostic_seconds=900,
                  clock="monotonic; wall timestamps show unexplained discrepancies",
                  external_host_load_verified=False, arms={})
    for arm, order in (("C", 5), ("P", 8)):
        path = root/"run"/arm
        fit, trace = read(path/"fit/result.json"), read(path/"trace/result.json")
        supervisor, seed = read(path/"supervisor.json"), read(path/"fit/seed.json")
        assert all(row["completed"] for row in (fit, trace, supervisor))
        assert fit["sources_before"] == fit["sources_after"]
        assert seed["order"] == order
        for row in (fit, trace):
            assert row["provenance"]["repository"]["commit"] == PRODUCER
            assert row["provenance"]["repository"]["dirty"] is False
        selected = fit["search"]["selected"]
        assert selected["status"] == "completed" and selected["role"] == "search"
        assert selected == read(path/"fit"/f"trial-{selected['index']:05}.json")
        assert len(fit["fine"]) == 2 and len(fit["interior"]) == 3
        assert all(row["checks_pass"] for row in fit["fine"]+fit["interior"])
        assert trace["transits"] == 200 and len(trace["lines"]) == 10
        assert max(trace["kernel_control"].values()) <= 1e-12
        assert all(supervisor[stage]["completed"]
                   and supervisor[stage]["stop_reason"] is None for stage in ("fit", "trace"))
        assert supervisor["fit"]["deadline_monotonic"] == (
            supervisor["trace"]["deadline_monotonic"])
        assert supervisor["elapsed_s"] < 2700
        assert supervisor["retained_bytes"] < 256*1024**2
        level = fit["geometry"]["levels"][-1]
        geometry = level["geometry"]
        times = [datetime.fromisoformat(row["provenance"]["host"]["captured_at"])
                 for row in (fit, trace)]
        result["arms"][arm] = dict(
            order=order, named_coefficients=len(seed["names"]), selected_trial=selected["index"],
            selected_snapshot_sha256=hashlib.sha256(
                (path/"fit/selected-snapshot.json").read_bytes()).hexdigest(),
            boundary_rms=max(row["metrics"]["normal_rms"] for row in fit["fine"]),
            boundary_max=max(row["metrics"]["normal_max"] for row in fit["fine"]),
            interior_rms=fit["interior"][-1]["metrics"]["vector_rms"],
            current_A=fit["fine"][0]["metrics"]["current"], geometry=fit["geometry"]["status"],
            length_upper_m=max(geometry["length_upper"]),
            coil_clearance_lower_m=geometry["coil_lower"],
            plasma_clearance_lower_m=geometry["plasma_lower"],
            curvature_upper_per_m=max(row["maximum_upper_bound"] for row in level["curvature"]),
            trace_summary=trace["summary"], search_status=fit["search"]["status"],
            intake_model_s=fit["model_ready_s"], startup_s=fit["search"]["startup_s"],
            search_s=fit["search"]["search_s"], fit_monotonic_s=supervisor["fit"]["elapsed_s"],
            trace_monotonic_s=supervisor["trace"]["elapsed_s"],
            total_monotonic_s=supervisor["elapsed_s"],
            fit_to_trace_wall_timestamp_s=(times[1]-times[0]).total_seconds(),
            retained_bytes_before_supervisor_record=supervisor["retained_bytes"])
    control, probe = (result["arms"][arm] for arm in ("C", "P"))
    ratio = probe["boundary_rms"]/control["boundary_rms"]
    qualifies = (ratio <= .5 and probe["geometry"] == "pass"
                 and probe["interior_rms"] <= control["interior_rms"])
    result.update(boundary_ratio_P_over_C=ratio, richer_family_hurdle_met=qualifies,
                  next_research_route="richer coil family" if qualifies else
                  "joint plasma/coil optimization",
                  limitations="One seed, one local optimizer, nominal monotonic budgets; "
                  "unverified external host load and wall-clock discrepancies. "
                  "Not a controlled throughput or causal/global family comparison. "
                  "No nested-surface, realized-flux equivalence or benefit-transfer proof.")
    return result


if __name__ == "__main__":
    print(json.dumps(summarize(Path(__file__).resolve().parent), indent=2, allow_nan=False))
