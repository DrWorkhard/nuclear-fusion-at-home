"""Settings interception controls with synthetic factories; no scientific imports."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from capture_seeded_vmec_settings import capture_row_settings  # noqa: E402


class CaptureSeededSettingsTests(unittest.TestCase):
    def setUp(self):
        self.protocol = json.loads((ROOT / "docs/qi/seeded-comparison-v1.json").read_text(
            encoding="utf-8"))
        self.expected = self.protocol["effective_vmec_settings"]
        self.actual = copy.deepcopy(self.expected)
        self.calls = []
        self.model = SimpleNamespace(model_dump=lambda **kwargs: self.actual)

        def factory(boundary, settings):
            self.calls.append((boundary, settings))
            return self.model

        self.original = factory
        self.module = SimpleNamespace(create_vmec_settings_from_preset=factory)
        self.preset = SimpleNamespace(fidelity="high_fidelity", multithreaded=False, verbose=False)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name)
        self.row = self.protocol["rows"][0]

    def capture(self, row=None):
        return capture_row_settings(self.module, self.output, row or self.row, self.expected)

    def call(self):
        return self.module.create_vmec_settings_from_preset("boundary", settings=self.preset)

    def test_all_three_rows_preserve_original_model_and_factory(self):
        for row in self.protocol["rows"]:
            with self.capture(row) as records:
                self.assertIs(self.call(), self.model)
                self.assertEqual(records, [self.expected])
            self.assertIs(self.module.create_vmec_settings_from_preset, self.original)
            path = self.output / f"{row['target_id']}-effective-settings.json"
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved, dict(global_row=row["global_row"], target_id=row["target_id"],
                                         effective_vmec_settings=self.expected))
        self.assertEqual(len(self.calls), 3)

    def test_every_effective_field_and_nested_step_is_checked_before_solver(self):
        mutations = []
        for key, value in self.expected.items():
            if key != "multigrid_steps":
                data = copy.deepcopy(self.expected)
                data[key] = not value if isinstance(value, bool) else value + 1
                mutations.append(data)
        for index, step in enumerate(self.expected["multigrid_steps"]):
            for key in step:
                data = copy.deepcopy(self.expected)
                data["multigrid_steps"][index][key] += 1
                mutations.append(data)
        for index, data in enumerate(mutations):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as directory:
                self.actual = data
                with self.assertRaisesRegex(ValueError, "differ from frozen"):
                    with capture_row_settings(
                            self.module, Path(directory), self.row, self.expected):
                        self.call()
                        self.fail("changed settings reached solver")
                self.assertIs(self.module.create_vmec_settings_from_preset, self.original)
                self.assertEqual(len(list(Path(directory).glob("*.json"))), 1)

    def test_missing_extra_and_changed_json_type_rejected(self):
        for data in ({k: v for k, v in self.expected.items() if k != "time_step"},
                     dict(self.expected, extra=0), dict(self.expected, max_threads=True),
                     dict(self.expected, verbose=0)):
            self.actual = data
            with tempfile.TemporaryDirectory() as directory:
                with self.assertRaisesRegex(ValueError, "differ from frozen"):
                    with capture_row_settings(
                            self.module, Path(directory), self.row, self.expected):
                        self.call()

    def test_no_call_duplicate_call_and_output_reuse_rejected(self):
        with self.assertRaisesRegex(ValueError, "one effective"):
            with self.capture():
                pass
        with self.assertRaisesRegex(ValueError, "multiple effective"):
            with self.capture():
                self.call()
                self.call()
        self.assertEqual(len(self.calls), 1)
        path = self.output / f"{self.row['target_id']}-effective-settings.json"
        original = path.read_bytes()
        with self.assertRaises(FileExistsError):
            with self.capture():
                self.call()
        self.assertEqual(path.read_bytes(), original)
        self.assertIs(self.module.create_vmec_settings_from_preset, self.original)

    def test_factory_error_and_nonfinite_settings_restore_factory(self):
        def broken_factory(boundary, settings):
            raise RuntimeError("factory failure")

        self.module.create_vmec_settings_from_preset = broken_factory
        with self.assertRaisesRegex(RuntimeError, "factory failure"):
            with self.capture():
                self.call()
        self.assertIs(self.module.create_vmec_settings_from_preset, broken_factory)
        self.module.create_vmec_settings_from_preset = self.original
        self.actual["time_step"] = float("nan")
        with self.assertRaises(ValueError):
            with self.capture():
                self.call()
                self.fail("nonfinite settings reached solver")
        self.assertIs(self.module.create_vmec_settings_from_preset, self.original)

    def test_failure_and_bad_preset_restore_factory(self):
        with self.assertRaisesRegex(RuntimeError, "solver failure"):
            with self.capture():
                self.call()
                raise RuntimeError("solver failure")
        self.assertIs(self.module.create_vmec_settings_from_preset, self.original)
        for key, value in (("fidelity", "low_fidelity"), ("multithreaded", True),
                           ("verbose", True)):
            old = getattr(self.preset, key)
            setattr(self.preset, key, value)
            with self.assertRaisesRegex(ValueError, "unchanged default"):
                with self.capture(self.protocol["rows"][1]):
                    self.call()
            setattr(self.preset, key, old)
            self.assertIs(self.module.create_vmec_settings_from_preset, self.original)
        self.assertEqual(len(self.calls), 1)


if __name__ == "__main__":
    unittest.main()
