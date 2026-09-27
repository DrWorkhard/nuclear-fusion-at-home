"""UI compatibility without modifying the source-bound numerical evaluator."""

import copy
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

from fusion_public.data import ROOT, load_case, parameter_names, save_new
from fusion_public.report import evaluate
from fusion_public.usability import score_comparison, set_coefficient, validate_for_cli


class UsabilityTests(unittest.TestCase):
    def setUp(self):
        self.case, _ = load_case()
        self.seed = self.case["seed"]

    def test_all_198_named_positions_and_no_input_mutation(self):
        before = copy.deepcopy(self.seed)
        for index, name in enumerate(parameter_names()):
            coil, remainder = divmod(index, 33)
            axis, k = divmod(remainder, 11)
            with self.subTest(name=name):
                changed = set_coefficient(self.seed, name, 0.123)
                expected = copy.deepcopy(before)
                expected["base_coefficients"][coil][axis][k] = 0.123
                self.assertEqual(changed, expected)
        self.assertEqual(self.seed, before)

    def test_unknown_name_and_bad_values(self):
        with self.assertRaisesRegex(ValueError, "Unknown coefficient"):
            set_coefficient(self.seed, "coil[6]/xc(0)", 0)
        for value in (True, float("nan"), float("inf"), 11):
            with self.subTest(value=value), self.assertRaises(ValueError):
                set_coefficient(self.seed, "coil[0]/xc(0)", value)

    def test_shape_errors_name_coil_and_axis(self):
        for i in range(6):
            for axis in range(3):
                candidate = copy.deepcopy(self.seed)
                candidate["base_coefficients"][i][axis].pop()
                message = rf"coil\[{i}\], axis {'xyz'[axis]}: exactly 11"
                with self.assertRaisesRegex(ValueError, message):
                    validate_for_cli(candidate)
        candidate = copy.deepcopy(self.seed)
        candidate["base_coefficients"][2].pop()
        with self.assertRaisesRegex(ValueError, r"coil\[2\]: exactly 3"):
            validate_for_cli(candidate)

    def test_coefficient_errors_name_exact_component(self):
        candidate = copy.deepcopy(self.seed)
        candidate["base_coefficients"][5][2][10] = 11
        with self.assertRaisesRegex(ValueError, r"coil\[5\]/zc\(5\)"):
            validate_for_cli(candidate)

    def test_other_schema_errors_still_reject(self):
        for candidate in (None, [], {}, dict(self.seed, physical_admission=True)):
            with self.subTest(candidate=type(candidate)), self.assertRaises(ValueError):
                validate_for_cli(candidate)

    def test_reference_and_change_are_explained(self):
        candidate_scores = dict(sampled_normal_rms=0.25, sampled_inner_vector_rms=0.4)
        result = score_comparison({"levels": [{}, {"metrics": candidate_scores}]}, self.case)
        normal = result["scores"]["sampled_normal_rms"]
        inner = result["scores"]["sampled_inner_vector_rms"]
        self.assertAlmostEqual(normal["reference"], 0.3042070281)
        self.assertAlmostEqual(inner["reference"], 0.3804347184)
        self.assertAlmostEqual(normal["change"], 0.25 - normal["reference"])
        self.assertAlmostEqual(normal["change_percent"], 100 * (0.25 / normal["reference"] - 1))
        self.assertLess(normal["change"], 0)
        self.assertGreater(inner["change"], 0)
        self.assertIn("not a public pass/fail", result["interpretation"])
        self.assertIn("Reference and candidate", result["reference_scope"])
        self.assertIn("512 nodes", result["reference_scope"])

    def test_unchanged_reference_has_exactly_zero_matched_resolution_change(self):
        case, digest = load_case()
        report = evaluate(case["seed"], case, digest)
        before = copy.deepcopy(report)
        comparison = score_comparison(report, case)
        for score in comparison["scores"].values():
            self.assertEqual(score["reference"], score["candidate"])
            self.assertEqual(score["change"], 0.0)
            self.assertEqual(score["change_percent"], 0.0)
        self.assertEqual(report, before)
        self.assertTrue(report["seed_native_reference"]["passed"])
        self.assertFalse(report["scope"]["physical_admission"])

    def test_help_explains_absolute_metres_and_quoted_name(self):
        result = subprocess.run([sys.executable, "-I", "-S", str(ROOT / "fusion.py"),
                                 "public", "set-coefficient", "--help"],
                                capture_output=True, text=True, check=True)
        self.assertIn('"coil[0]/xc(0)"', result.stdout)
        self.assertIn("Absolute value in metres, not a delta", result.stdout)
        self.assertIn("double quotes", result.stdout)

    def test_discovery_and_root_help_have_readable_spacing(self):
        for args in (("--help",), ("public", "cases")):
            result = subprocess.run([sys.executable, "-I", "-S", str(ROOT / "fusion.py"),
                                     *args], capture_output=True, text=True, check=True)
            self.assertIn("Python 3.11+", result.stdout)
            self.assertNotIn("Python3", result.stdout)
            self.assertNotIn("boundary,64", result.stdout)
        self.assertIn("64 boundary, 64 inner, 64 loop", result.stdout)

    def test_cli_set_by_name_and_existing_output_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate, output = Path(directory) / "candidate.json", Path(directory) / "changed.json"
            save_new(candidate, self.seed)
            command = [sys.executable, "-I", "-S", str(ROOT / "fusion.py"), "public",
                       "set-coefficient", "--candidate", str(candidate), "--name", "coil[1]/ys(3)",
                       "--value", "0.123", "--output", str(output)]
            run = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")),
                             set_coefficient(self.seed, "coil[1]/ys(3)", 0.123))
            before = output.read_bytes()
            repeated = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(repeated.returncode, 2)
            self.assertIn("already exists", repeated.stderr)
            self.assertEqual(before, output.read_bytes())

    def test_unsupported_version_before_imports(self):
        spec = importlib.util.spec_from_file_location("launcher", ROOT / "fusion.py")
        launcher = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(launcher)
        for version, args, required in (
            ((3, 9, 6), ["public", "demo"], "3.11+"),
            ((3, 10, 9), ["--help"], "3.11+"),
        ):
            stderr = io.StringIO()
            with patch.object(sys, "version_info", version), patch.object(
                sys, "argv", ["fusion.py", *args]
            ), redirect_stderr(stderr):
                self.assertEqual(launcher.main(), 2)
            self.assertIn(required, stderr.getvalue())
            self.assertIn("python3.12", stderr.getvalue())
            self.assertIn("py -3.12", stderr.getvalue())

    def test_retired_research_command_explains_freeze_without_native_imports(self):
        result = subprocess.run(
            [sys.executable, "-I", "-S", str(ROOT / "fusion.py"), "profiles"],
            capture_output=True, text=True, check=False, timeout=20,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("research-freeze-2026-09-27", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
