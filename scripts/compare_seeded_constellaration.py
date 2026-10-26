"""Compare the three frozen #112 dataset rows; no solver or scientific imports."""

import argparse
import hashlib
import json
import math
from pathlib import Path

from constellaration_metrics import check_geometry


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_bound(path, expected):
    raw = Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected, "file SHA-256 mismatch")
    return json.loads(raw)


def finite_scalar(value):
    return type(value) in (int, float) and math.isfinite(value)


def compare_row(protocol, row, report):
    """Require valid pipeline output before assigning a numerical comparison verdict."""
    target = row["target_id"]
    require(set(report["targets"]) == {target}, "target identity mismatch")
    record = report["targets"][target]
    require(record["completed"] is True, "incomplete forward model")
    require(record["input_sha256"] == row["input_sha256"], "input identity mismatch")
    require(report["physical_admission"] is False, "unexpected physical admission")
    require(report["versions"] == protocol["report_versions"], "package versions mismatch")
    for key in ("python", "platform", "machine"):
        require(report[key] == protocol["environment"][key], f"runtime {key} mismatch")
    require(record["settings"] == protocol["settings"], "settings mismatch")
    for key, expected in protocol["vmec"].items():
        require(record["vmec"][key] == expected, f"VMEC {key} mismatch")
    require(report["geometry_relative_tolerance"] == 1e-10, "geometry tolerance mismatch")
    require(record["conversion"]["R00"] == row["R00"], "boundary scale mismatch")
    for key, expected in row["conversion"].items():
        require(record["conversion"][key] == expected, f"conversion {key} mismatch")
    # Recompute the approved gate; a report's pass flag cannot override its residuals.
    check_geometry(record["conversion"], record["geometry_check"])
    require(record["conversion_validation"]["passed"] is True, "conversion not validated")
    metrics = record["metrics"]
    require(set(metrics) == set(protocol["comparison"]["metrics"]), "metric set mismatch")
    require(set(row["stored_metrics"]) == set(metrics), "stored metric set mismatch")
    absolute = protocol["comparison"]["absolute_tolerance"]
    relative = protocol["comparison"]["relative_tolerance"]
    comparisons = {}
    for name in protocol["comparison"]["metrics"]:
        computed, stored = metrics[name], row["stored_metrics"][name]
        require(finite_scalar(computed) and finite_scalar(stored), f"invalid scalar: {name}")
        delta = computed - stored
        limit = absolute + relative * abs(stored)
        require(math.isfinite(delta) and math.isfinite(limit), f"overflow: {name}")
        comparisons[name] = dict(stored=stored, computed=computed, signed_difference=delta,
                                 absolute_difference=abs(delta), tolerance=limit,
                                 passed=abs(delta) <= limit)
    return dict(status="agree" if all(x["passed"] for x in comparisons.values()) else "mismatch",
                metrics=comparisons)


def compare(protocol, reports):
    """Keep every fixed row, including unstarted or invalid rows, in the result."""
    expected = {str(row["global_row"]) for row in protocol["rows"]}
    require(set(reports) <= expected, "unexpected dataset row")
    rows = []
    for row in protocol["rows"]:
        number = str(row["global_row"])
        if number not in reports:
            result = dict(status="not-run", reason="no report supplied")
        else:
            try:
                result = compare_row(protocol, row, reports[number])
            except (KeyError, TypeError, ValueError) as error:
                result = dict(status="invalid", reason=str(error))
        rows.append(dict(global_row=row["global_row"], **result))
    return dict(all_agree=all(row["status"] == "agree" for row in rows), rows=rows,
                physical_admission=False, interpretation=protocol["interpretation"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--report", nargs=3, action="append", default=[],
                        metavar=("ROW", "FILE", "SHA256"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    protocol = read_bound(args.protocol, args.protocol_sha256)
    reports, identities = {}, {}
    for number, filename, digest in args.report:
        require(number not in reports, "duplicate dataset row")
        reports[number] = read_bound(filename, digest)
        identities[number] = digest
    result = compare(protocol, reports)
    result.update(protocol_sha256=args.protocol_sha256, report_sha256=identities)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    return 0 if result["all_agree"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
