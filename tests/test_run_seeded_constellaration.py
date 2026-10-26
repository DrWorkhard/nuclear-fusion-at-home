"""Serial workflow controls using a synthetic scorer; no scientific imports."""

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_seeded_constellaration as workflow  # noqa: E402


class SeededWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.protocol_path = ROOT / "docs/qi/seeded-comparison-v1.json"
        self.protocol = json.loads(self.protocol_path.read_text(encoding="utf-8"))
        self.inputs, self.calls, self.solves = {}, [], []
        self.checks = 0
        self.change = lambda index, report: None
        self.code = lambda index: 0
        self.settings = copy.deepcopy(self.protocol["effective_vmec_settings"])
        self.preset = SimpleNamespace(fidelity="high_fidelity", multithreaded=False, verbose=False)
        self.factory = lambda boundary, settings: SimpleNamespace(
            model_dump=lambda **kwargs: self.settings)
        self.module = SimpleNamespace(create_vmec_settings_from_preset=self.factory)
        for row in self.protocol["rows"]:
            number = str(row["global_row"])
            path = self.root / (number + ".json")
            path.write_text(number, encoding="utf-8")
            self.inputs[number] = path
            row["input_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.scorer = SimpleNamespace(__file__="synthetic-scorer.py", main=self.score)
        self.output = self.root / "run"

    def check_ready(self):
        self.checks += 1

    def score(self):
        args = dict(zip(sys.argv[1::2], sys.argv[2::2], strict=True))
        target = args["--target-id"]
        row = next(row for row in self.protocol["rows"] if row["target_id"] == target)
        index = len(self.calls)
        self.calls.append(target)
        self.assertNotIn("--confirm", sys.argv)
        self.assertEqual(args["--sha256"], row["input_sha256"])
        self.assertEqual(Path(args["--input"]), self.inputs[str(row["global_row"])])
        self.module.create_vmec_settings_from_preset(None, settings=self.preset)
        self.solves.append(target)
        record = dict(completed=True, input_sha256=row["input_sha256"],
                      settings=self.protocol["settings"], vmec=self.protocol["vmec"],
                      conversion=dict(R00=row["R00"], **row["conversion"],
                                      max_abs_difference_to_vmecpp_reader=0.),
                      geometry_check=dict(surface_vs_input=0., vmec_boundary_vs_input=0.,
                                          surface_coefficient_bound=0.,
                                          vmec_boundary_coefficient_bound=0.),
                      conversion_validation=dict(passed=True), metrics=row["stored_metrics"].copy())
        report = dict(targets={target: record}, physical_admission=False,
                      geometry_relative_tolerance=1e-10, versions=self.protocol["report_versions"],
                      **{k: self.protocol["environment"][k]
                         for k in ("python", "platform", "machine")})
        self.change(index, report)
        output = Path(args["--output"])
        output.mkdir()
        (output / "report.json").write_text(json.dumps(report), encoding="utf-8")
        return self.code(index)

    def run_rows(self, check=None):
        # Synthetic input hashes differ. Production always reads the immutable public freeze.
        with patch.object(workflow, "read_bound", return_value=self.protocol) as bound:
            result = workflow.run_rows(self.scorer, self.module, self.protocol_path,
                                       self.inputs, self.output,
                                       check_ready=check or self.check_ready)
            bound.assert_called_once_with(self.protocol_path, workflow.PROTOCOL_SHA256)
        self.assertIs(self.module.create_vmec_settings_from_preset, self.factory)
        return result

    def test_three_serial_calls_bind_reports_settings_and_restore_argv(self):
        original = sys.argv
        result = self.run_rows()
        self.assertIs(sys.argv, original)
        self.assertTrue(result["completed"])
        self.assertTrue(result["all_agree"])
        self.assertEqual(self.calls, [row["target_id"] for row in self.protocol["rows"]])
        self.assertEqual(self.checks, 6)
        self.assertEqual(len(result["report_sha256"]), 3)
        self.assertEqual([len(row["metrics"]) for row in result["rows"]], [12, 12, 12])
        self.assertEqual(len(list(self.output.glob("*-effective-settings.json"))), 3)

    def test_numerical_mismatch_does_not_stop_or_change_rows(self):
        def mismatch(index, report):
            next(iter(report["targets"].values()))["metrics"]["qi"] += 1

        self.change = mismatch
        result = self.run_rows()
        self.assertTrue(result["completed"])
        self.assertFalse(result["all_agree"])
        self.assertEqual([row["status"] for row in result["rows"]], ["mismatch"] * 3)
        self.assertEqual(len(self.solves), 3)

    def test_nonzero_exit_stops_at_each_position_even_with_valid_report(self):
        for position in range(3):
            with self.subTest(position=position):
                self.calls.clear()
                self.output = self.root / f"failure-{position}"
                self.code = lambda index, position=position: 1 if index == position else 0
                result = self.run_rows()
                self.assertFalse(result["completed"])
                self.assertFalse(result["all_agree"])
                self.assertEqual(len(self.calls), position + 1)
                self.assertEqual([row["status"] for row in result["rows"]],
                                 ["agree"] * position + ["invalid"] + ["not-run"] * (2-position))
                self.assertEqual(len(result["report_sha256"]), position + 1)

    def test_settings_failure_prevents_solve_and_preserves_record(self):
        self.settings["max_threads"] = 2
        result = self.run_rows()
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.solves, [])
        self.assertEqual([row["status"] for row in result["rows"]],
                         ["invalid", "not-run", "not-run"])
        self.assertEqual(len(list(self.output.glob("*-effective-settings.json"))), 1)

    def test_invalid_report_stops_remaining_calls(self):
        def invalid(index, report):
            report["python"] = "wrong runtime"

        self.change = invalid
        result = self.run_rows()
        self.assertEqual(len(self.calls), 1)
        self.assertFalse(result["completed"])
        self.assertIn("runtime python mismatch", result["execution"][0]["error"])

    def test_late_return_and_pre_call_live_failure_are_not_completed(self):
        for fail_at in (1, 2):
            self.calls.clear()
            self.checks = 0
            self.output = self.root / f"live-{fail_at}"

            def check(fail_at=fail_at):
                self.checks += 1
                if self.checks == fail_at:
                    raise TimeoutError("resource/deadline failure")

            result = self.run_rows(check)
            self.assertFalse(result["completed"])
            self.assertFalse(result["all_agree"])
            self.assertEqual(len(self.calls), fail_at - 1)
            self.assertEqual(result["rows"][0]["status"], "invalid")

    def test_exception_restores_argv_and_retains_partial_output(self):
        original = sys.argv

        def broken():
            self.module.create_vmec_settings_from_preset(None, settings=self.preset)
            raise RuntimeError("solver failure")

        self.scorer.main = broken
        result = self.run_rows()
        self.assertIs(sys.argv, original)
        self.assertIn("solver failure", result["execution"][0]["error"])
        self.assertEqual(len(list(self.output.glob("*-effective-settings.json"))), 1)

    def test_missing_or_duplicate_factory_call_stops_workflow(self):
        for count in (0, 2):
            self.output = self.root / f"settings-calls-{count}"

            def invalid_scorer(count=count):
                for _ in range(count):
                    self.module.create_vmec_settings_from_preset(None, settings=self.preset)
                return 0

            self.scorer.main = invalid_scorer
            result = self.run_rows()
            self.assertFalse(result["completed"])
            self.assertFalse(result["all_agree"])
            self.assertEqual(len(result["execution"]), 1)
            self.assertEqual([row["status"] for row in result["rows"]],
                             ["invalid", "not-run", "not-run"])

    def test_system_exit_before_and_after_report_preserves_failure(self):
        original = sys.argv
        for after_report in (False, True):
            with self.subTest(after_report=after_report):
                self.calls.clear()
                self.output = self.root / f"system-exit-{after_report}"

                def exit_scorer(after_report=after_report):
                    if after_report:
                        self.score()
                    raise SystemExit(2)

                self.scorer.main = exit_scorer
                result = self.run_rows()
                self.assertIs(sys.argv, original)
                self.assertFalse(result["completed"])
                self.assertFalse(result["all_agree"])
                self.assertEqual([row["status"] for row in result["rows"]],
                                 ["invalid", "not-run", "not-run"])
                self.assertEqual(len(result["execution"]), 1)
                self.assertIn("SystemExit: 2", result["execution"][0]["error"])
                self.assertEqual(len(result["report_sha256"]), int(after_report))
                self.assertEqual(len(list(self.output.glob("*-execution.json"))), 1)
                self.assertEqual(json.loads((self.output / "comparison.json").read_text()),
                                 json.loads(json.dumps(result)))

    def test_input_changed_between_rows_rejected_before_second_call(self):
        def check():
            self.checks += 1
            if self.checks == 3:
                row = self.protocol["rows"][1]
                self.inputs[str(row["global_row"])].write_text("changed", encoding="utf-8")

        result = self.run_rows(check)
        self.assertEqual(len(self.calls), 1)
        self.assertFalse(result["completed"])
        self.assertEqual([row["status"] for row in result["rows"]],
                         ["agree", "invalid", "not-run"])

    def test_protocol_input_and_output_reuse_fail_before_scorer(self):
        with self.assertRaisesRegex(ValueError, "frozen input"):
            workflow.run_rows(self.scorer, self.module, self.protocol_path, self.inputs,
                              self.output, check_ready=self.check_ready)
        self.assertFalse(self.output.exists())
        result = self.run_rows()
        self.assertTrue(result["completed"])
        original = (self.output / "comparison.json").read_bytes()
        self.calls.clear()
        with self.assertRaises(FileExistsError):
            self.run_rows()
        self.assertEqual(self.calls, [])
        self.assertEqual((self.output / "comparison.json").read_bytes(), original)
        self.output = self.root / "tampered"
        next(iter(self.inputs.values())).write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "frozen input"):
            self.run_rows()
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
