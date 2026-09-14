"""Explicit diagnostic adapter: NOT a historical two-poll search report."""

import argparse
import json
import sys
from pathlib import Path

import validate_plasma_design as validation
from balanced_plasma_inputs import sources
from current_diagnostic_inputs import reference
from plasma_inputs import root_path

from fusion_baselines.provenance import write_json_atomic


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    folder, raw = args.study.resolve(), args.raw.resolve()
    _, binding, old = sources(root_path())
    path = folder / "endpoints.json"
    end = json.loads(path.read_text())
    if (
        end["status"] != "completed"
        or end["source"] != binding
        or any(r.get("error") for r in end["rows"])
    ):
        raise ValueError("complete frozen balanced endpoints required")
    adapter = folder / "diagnostic-adapter"
    if adapter.exists():
        raise FileExistsError("new immutable diagnostic adapter required")
    adapter.mkdir()
    payload = dict(
        record_kind="balanced-diagnostic-adapter-not-a-two-poll-search",
        status="completed",
        balanced_endpoints=reference(path),
        source=binding["legacy"],
        step3_pass=False,
        cells=[old["cells"][0], end["selected"]["native"]],
        search=dict(selected=1),
        endpoints=[end["rows"][0]["native"], old["endpoints"][1], end["rows"][1]["native"]],
    )
    write_json_atomic(adapter / "summary.json", payload)
    sys.argv = [
        "validate_plasma_design.py",
        str(adapter),
        str(folder / "validation.json"),
        str(raw),
    ]
    return validation.main()


if __name__ == "__main__":
    raise SystemExit(main())
