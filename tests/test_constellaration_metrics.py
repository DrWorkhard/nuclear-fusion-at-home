"""Boundary identity and conversion failure controls without native dependencies."""

import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("constellaration_metrics", ROOT / "scripts" /
                                              "constellaration_metrics.py")
scorer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scorer)


def boundary():
    return dict(lasym=False, rbs=None, zbc=None, nfp=2,
                rbc=[dict(m=0, n=0, value=1.), dict(m=1, n=-1, value=0.)],
                zbs=[dict(m=1, n=0, value=.1)])


class BoundaryIntakeTests(unittest.TestCase):
    def test_hash_checked_before_parsing_and_case_insensitive(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "boundary.json"
            raw = json.dumps(boundary()).encode()
            path.write_bytes(raw)
            sha = hashlib.sha256(raw).hexdigest()
            self.assertEqual(scorer.load_input(path, sha.upper()), boundary())
            path.write_bytes(raw + b"\n")
            with self.assertRaisesRegex(ValueError, "source identity changed"):
                scorer.load_input(path, sha)
            path.write_text("invalid JSON")
            with self.assertRaisesRegex(ValueError, "source identity changed"):
                scorer.load_input(path, sha)
            with self.assertRaisesRegex(ValueError, "64 hexadecimal"):
                scorer.load_input(path, "../input")

    def test_registered_inputs_keep_their_hashes(self):
        for target in scorer.TARGETS:
            with self.subTest(target=target):
                relative, sha, data = scorer.load(target)
                self.assertEqual(scorer.load_input(ROOT / relative, sha), data)

    def test_duplicate_zero_mode_is_rejected_in_each_array(self):
        for key in ("rbc", "zbs"):
            data = boundary()
            data[key] = [dict(m=0, n=0, value=0.), dict(m=0, n=0, value=1.)]
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "duplicate"):
                scorer.validate_boundary(data)

    def test_invalid_boundaries_fail_before_native_conversion(self):
        cases = []
        for key, value in (("nfp", True), ("nfp", 0), ("nfp", 2.5), ("lasym", True),
                           ("rbs", []), ("zbc", []), ("rbc", []), ("zbs", None)):
            data = boundary()
            data[key] = value
            cases.append(data)
        for key, value in (("m", -1), ("m", True), ("n", .5), ("value", float("nan")),
                           ("value", float("inf")), ("value", True), ("value", "1")):
            data = boundary()
            data["zbs"][0][key] = value
            cases.append(data)
        for value in (0., -1.):
            data = boundary()
            data["rbc"][0]["value"] = value
            cases.append(data)
        data = boundary()
        data["rbc"] = data["rbc"][1:]
        cases.append(data)
        for index, data in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(ValueError):
                scorer.validate_boundary(data)

    def test_geometry_failure_cannot_pass_using_theta_flip(self):
        conversion = dict(R00=2., max_abs_difference_to_vmecpp_reader=0.)
        good = dict(surface_vs_input=1e-15, vmec_boundary_vs_input=1e-15,
                    surface_coefficient_bound=0., vmec_boundary_coefficient_bound=0.,
                    vmec_boundary_vs_input_theta_flipped=0.5)
        self.assertTrue(scorer.check_geometry(conversion, good)["passed"])
        for key in ("surface_vs_input", "vmec_boundary_vs_input",
                    "surface_coefficient_bound", "vmec_boundary_coefficient_bound"):
            for value in (1e-5, float("nan"), float("inf")):
                bad = dict(good, **{key: value}, vmec_boundary_vs_input_theta_flipped=0.)
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    scorer.check_geometry(conversion, bad)
        with self.assertRaises(ValueError):
            scorer.check_geometry(dict(conversion, max_abs_difference_to_vmecpp_reader=1e-15),
                                  good)

    def test_cli_rejects_ambiguous_identity_and_unsafe_output_names(self):
        for options in (("--input", "x"), ("--sha256", "a" * 64),
                        ("--target-id", "custom"),
                        ("--input", "x", "--sha256", "a" * 64, "--target-id", "../escape")):
            with self.subTest(options=options), patch.object(sys, "argv", [
                    "scorer", "--output", "unused", *options]):
                with self.assertRaises(SystemExit) as error, patch("sys.stderr"):
                    scorer.main()
                self.assertEqual(error.exception.code, 2)

    def test_metrics_on_failed_record_do_not_make_cli_successful(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            failed = dict(completed=False, metrics={"some_metric": 1.}, error="conversion failed")
            with patch.object(sys, "argv", ["scorer", "--output", str(output)]), \
                    patch.object(scorer.importlib.metadata, "version", return_value="0.2.6"), \
                    patch.dict(scorer.os.environ, {k: "1" for k in scorer.THREADS}), \
                    patch.object(scorer, "evaluate", return_value=copy.deepcopy(failed)), \
                    patch("builtins.print"):
                self.assertEqual(scorer.main(), 1)
            report = json.loads((output / "report.json").read_text())
            self.assertNotIn("rule", report)
            self.assertFalse(report["physical_admission"])
            self.assertFalse(report["targets"]["reference401"]["completed"])

    def test_custom_cli_keeps_identity_and_omits_registered_comparison_rule(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "boundary.json"
            source.write_text(json.dumps(boundary()), encoding="utf-8")
            sha = hashlib.sha256(source.read_bytes()).hexdigest()
            output = Path(directory) / "run"
            with patch.object(sys, "argv", ["scorer", "--output", str(output),
                    "--input", str(source), "--sha256", sha, "--target-id", "probe"]), \
                    patch.object(scorer.importlib.metadata, "version", return_value="0.2.6"), \
                    patch.dict(scorer.os.environ, {k: "1" for k in scorer.THREADS}), \
                    patch.object(scorer, "evaluate", return_value={"completed": True}) as run, \
                    patch("builtins.print"):
                self.assertEqual(scorer.main(), 0)
            run.assert_called_once_with("probe", output, False, (source, sha))
            report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["kind"], "constellaration-metrics-custom-boundary")
            self.assertEqual(list(report["targets"]), ["probe"])
            self.assertNotIn("rule", report)
            self.assertFalse(report["physical_admission"])

    def test_wrong_environment_rejected_before_output_created(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            with patch.object(sys, "argv", ["scorer", "--output", str(output)]), \
                    patch.object(scorer.importlib.metadata, "version", return_value="0.2.7"):
                with self.assertRaisesRegex(ValueError, "0.2.6 required"):
                    scorer.main()
            self.assertFalse(output.exists())


class WoutRetentionTests(unittest.TestCase):
    """Exercise the real evaluate() with synthetic scientific modules only."""

    def run_case(self, failure=None, save_fails=False):
        numpy = ModuleType("numpy")
        numpy.nan = float("nan")
        numpy.asarray = lambda value: SimpleNamespace(item=lambda: value)
        package = ModuleType("constellaration")
        wout = SimpleNamespace(save=Mock(), **{key: 0 for key in (
            "ns", "mpol", "ntor", "fsqr", "fsqz", "fsql", "ier_flag", "aspect", "Aminor_p",
            "Rmajor_p")})
        wout.save.side_effect = lambda path: Path(path).write_bytes(b"synthetic Wout")
        if save_fails:
            wout.save.side_effect = OSError("synthetic save failure")
        model = Mock(return_value=(SimpleNamespace(model_dump=lambda: {"metric": 1.}), wout))
        if failure == "forward_model":
            model.side_effect = RuntimeError("synthetic model failure")
        package.forward_model = SimpleNamespace(
            ConstellarationSettings=SimpleNamespace(default_high_fidelity=lambda:
                SimpleNamespace(model_dump_json=lambda: "{}")), forward_model=model)
        conversion = dict(R00=1., max_abs_difference_to_vmecpp_reader=0.)
        geometry = dict(surface_vs_input=0., vmec_boundary_vs_input=0.,
                        surface_coefficient_bound=0., vmec_boundary_coefficient_bound=0.)
        if failure == "gate":
            geometry["vmec_boundary_coefficient_bound"] = 1.
        geometry_stub = Mock(return_value=geometry)
        if failure == "geometry":
            geometry_stub.side_effect = ValueError("synthetic geometry failure")
        benchmark = Mock(return_value={"synthetic": True})
        if failure == "benchmarks":
            benchmark.side_effect = ValueError("synthetic benchmark failure")
        confirm = Mock(return_value={"synthetic": True})
        if failure == "confirm":
            confirm.side_effect = ValueError("synthetic confirmation failure")
        with tempfile.TemporaryDirectory() as directory, patch.dict(sys.modules, {
                "numpy": numpy, "constellaration": package}), \
                patch.object(scorer, "load_input", return_value={}), \
                patch.object(scorer, "convert", return_value=(
                    SimpleNamespace(model_dump_json=lambda: "{}"), conversion)), \
                patch.object(scorer, "geometry_check", geometry_stub), \
                patch.object(scorer, "benchmarks", benchmark), \
                patch.object(scorer, "leaderboard_path", confirm):
            output = Path(directory)
            record = scorer.evaluate("synthetic", output, confirm=True,
                                     source=(Path("unused"), "a" * 64))
            if failure == "forward_model":
                wout.save.assert_not_called()
            else:
                wout.save.assert_called_once_with(str(output / "wout_synthetic.nc"))
            artifact = output / "wout_synthetic.nc"
            self.assertEqual(artifact.exists(), failure != "forward_model" and not save_fails)
            if artifact.exists():
                self.assertEqual(artifact.read_bytes(), b"synthetic Wout")
        model.assert_called_once()
        json.dumps(record, allow_nan=False)
        return record, benchmark, confirm

    def test_success_and_optional_save_failure_keep_completion(self):
        for save_fails in (False, True):
            with self.subTest(save_fails=save_fails):
                record, benchmark, confirm = self.run_case(save_fails=save_fails)
                self.assertTrue(record["completed"])
                self.assertTrue(record["conversion_validation"]["passed"])
                self.assertNotIn("error", record)
                self.assertEqual("wout_save_error" in record, save_fails)
                benchmark.assert_called_once()
                confirm.assert_called_once()

    def test_later_failure_retains_wout_and_original_error(self):
        for failure in ("gate", "geometry", "benchmarks", "confirm"):
            for save_fails in (False, True):
                with self.subTest(failure=failure, save_fails=save_fails):
                    record, benchmark, confirm = self.run_case(failure, save_fails)
                    self.assertFalse(record["completed"])
                    self.assertEqual(record["metrics"], {"metric": 1.})
                    expected = {
                        "gate": "geometry check failed: vmec_boundary_coefficient_bound",
                        "geometry": "synthetic geometry failure",
                        "benchmarks": "synthetic benchmark failure",
                        "confirm": "synthetic confirmation failure",
                    }[failure]
                    self.assertIn(expected, record["error"])
                    self.assertNotIn("synthetic save failure", record["error"])
                    self.assertEqual("wout_save_error" in record, save_fails)
                    if save_fails:
                        self.assertIn("synthetic save failure", record["wout_save_error"])
                    if failure in ("gate", "geometry"):
                        self.assertNotIn("conversion_validation", record)
                        benchmark.assert_not_called()
                        confirm.assert_not_called()

    def test_forward_model_failure_has_no_wout_to_save(self):
        record, benchmark, confirm = self.run_case("forward_model")
        self.assertFalse(record["completed"])
        self.assertIn("synthetic model failure", record["error"])
        self.assertNotIn("metrics", record)
        self.assertNotIn("wout_save_error", record)
        benchmark.assert_not_called()
        confirm.assert_not_called()


if __name__ == "__main__":
    unittest.main()
