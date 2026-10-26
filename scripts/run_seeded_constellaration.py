"""Serial #112 seeded workflow, called only inside a separately gated native child.

No CLI, scientific imports or resource authorization. The final launcher must bind
this file, the scorer/runtime/inputs and the live check supplied as ``check_ready``.
Adapted from the recorded-plasma workflow; comparison and evaluator stay unchanged.
"""

import hashlib
import json
import sys
import traceback
from pathlib import Path

from capture_seeded_vmec_settings import capture_row_settings
from compare_seeded_constellaration import compare, read_bound, require

PROTOCOL_SHA256 = "df71882af62631557cc4bad55472e7a0a1f0bdb665a7f9c51fb1c602bea7303b"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_new(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def run_rows(scorer, settings_module, protocol_path, inputs, output, *, check_ready):
    """Call each fixed row at most once; mismatch continues, execution failure stops.

    ``check_ready`` must raise when the launcher's live resource/deadline gates
    fail. Call it before every row and after every scorer return, before accepting
    a report. A resource supervisor must also enforce limits during blocking calls.
    """
    protocol = read_bound(protocol_path, PROTOCOL_SHA256)
    expected = {str(row["global_row"]) for row in protocol["rows"]}
    require(set(inputs) == expected, "exactly the three frozen input rows required")
    require(callable(check_ready), "launcher live check required")
    for row in protocol["rows"]:
        require(digest(inputs[str(row["global_row"])]) == row["input_sha256"],
                "frozen input SHA-256 mismatch")
    output = Path(output)
    output.mkdir(exist_ok=False)
    reports, identities, execution = {}, {}, []
    failed_row = None
    for row in protocol["rows"]:
        number, target = str(row["global_row"]), row["target_id"]
        report_path = output / target / "report.json"
        record = dict(global_row=row["global_row"], completed=False, scorer_started=False)
        original_argv = sys.argv
        try:
            check_ready()
            require(digest(inputs[number]) == row["input_sha256"], "input changed before call")
            with capture_row_settings(settings_module, output, row,
                                      protocol["effective_vmec_settings"]):
                sys.argv = [str(scorer.__file__), "--input", str(inputs[number]),
                            "--sha256", row["input_sha256"], "--target-id", target,
                            "--output", str(output / target)]
                record["scorer_started"] = True
                record["exit_code"] = scorer.main()
            check_ready()
            require(type(record["exit_code"]) is int and record["exit_code"] == 0,
                    "scorer failed")
            reports[number] = json.loads(report_path.read_bytes())
            identities[number] = digest(report_path)
            verdict = compare(protocol, {number: reports[number]})
            result = next(item for item in verdict["rows"]
                          if item["global_row"] == row["global_row"])
            require(result["status"] in ("agree", "mismatch"),
                    "invalid scorer report: " + result.get("reason", "unknown"))
            record["completed"] = True
        except (Exception, SystemExit):
            failed_row = row["global_row"]
            record["error"] = traceback.format_exc()
        finally:
            sys.argv = original_argv
        # Keep any failed scorer report too, without trusting it as a completed call.
        if report_path.is_file() and number not in identities:
            identities[number] = digest(report_path)
            try:
                reports[number] = json.loads(report_path.read_bytes())
            except (ValueError, UnicodeError):
                pass
        execution.append(record)
        write_new(output / f"{target}-execution.json", record)
        if failed_row is not None:
            break
    result = compare(protocol, reports)
    if failed_row is not None:
        row_result = next(item for item in result["rows"] if item["global_row"] == failed_row)
        row_result.update(status="invalid", reason="workflow failure; see per-row execution record")
        result["all_agree"] = False
    result.update(completed=failed_row is None and len(execution) == 3,
                  protocol_sha256=PROTOCOL_SHA256, report_sha256=identities, execution=execution)
    write_new(output / "comparison.json", result)
    return result
