"""Release copy and failure controls without subprocesses, waits or field studies."""

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "verify_public_release", ROOT / "scripts/verify_public_release.py"
)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def test_copy_retains_notices_and_direct_references(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "qualification"
            # Stop after copying; the real eight-operation run is a separate qualification.
            with patch.object(
                release.subprocess, "run",
                return_value=subprocess.CompletedProcess([], 2, "stop after copy\n"),
            ) as run:
                with self.assertRaisesRegex(ValueError, "Failed release check: public-unit-tests"):
                    release.verify(output)
            run.assert_called_once()
            qualification = json.loads((output / "qualification.json").read_text(encoding="utf-8"))
            for relative in (
                "LICENSE", "NOTICE.md", "examples/clear-coil-samples-v1/README.md",
                "references/public-data-sources.json", "references/external_sources.json",
            ):
                with self.subTest(path=relative):
                    source = (ROOT / relative).read_bytes()
                    exported = output / "checkout with spaces" / relative
                    self.assertTrue(exported.is_file(), f"Missing exported notice: {relative}")
                    self.assertEqual(exported.read_bytes(), source)
                    self.assertEqual(qualification["copied_files"][relative],
                                     hashlib.sha256(source).hexdigest())

    def assert_failed_qualification(self, output, run, error_type, partial):
        qualification = json.loads((output / "qualification.json").read_text(encoding="utf-8"))
        self.assertFalse(qualification["complete"])
        self.assertFalse(qualification["physical_admission"])
        self.assertFalse(qualification["step4_pass"])
        self.assertTrue(qualification["python_socket_audit_guard"])
        self.assertEqual(qualification["error_type"], error_type)
        operations = qualification["operations"]
        self.assertEqual([row["label"] for row in operations],
                         ["public-unit-tests", "discovery"])
        self.assertEqual(operations[0]["output"], "earlier success\n")
        self.assertTrue(operations[0]["passed"])
        self.assertEqual(operations[0]["returncode"], 0)
        self.assertEqual(operations[0]["elapsed_seconds"], 0.25)
        for index, record in enumerate(operations):
            path = output / f"{index:02d}-{record['label']}.json"
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), record)
        failed = operations[1]
        self.assertEqual(failed["argv"], ["fusion.py", "public", "cases"])
        self.assertEqual(failed["expected_returncode"], 0)
        self.assertEqual(failed["elapsed_seconds"], 1.5)
        self.assertEqual(failed["output"], partial)
        self.assertFalse(failed["passed"])
        self.assertEqual(run.call_count, 2, "No checks may run after the failure")
        for call in run.call_args_list:
            command = call.args[0]
            self.assertIsInstance(command, list)
            self.assertEqual(command[:4], [sys.executable, "-I", "-S", "-c"])
            self.assertIn("sys.addaudithook(guard)", command[4])
            self.assertIn("event.startswith('socket.')", command[4])
            self.assertEqual(call.kwargs["timeout"], 180)
            self.assertTrue(call.kwargs["text"])
            self.assertEqual(call.kwargs["stdout"], subprocess.PIPE)
            self.assertEqual(call.kwargs["stderr"], subprocess.STDOUT)
        self.assertEqual(run.call_args.args[0][5:], failed["argv"])

        # A retry must preserve even an incomplete qualification and its logs.
        before = {p: p.read_bytes() for p in output.rglob("*") if p.is_file()}
        with patch.object(release.subprocess, "run") as retry:
            with self.assertRaises(FileExistsError):
                release.verify(output)
        retry.assert_not_called()
        self.assertEqual(before, {p: p.read_bytes() for p in output.rglob("*")
                                  if p.is_file()})
        return failed

    def test_timeout_retains_partial_output_and_failed_operation(self):
        for partial, expected in (
            (b"timeout bytes evidence\n", "timeout bytes evidence\n"),
            ("timeout text evidence: \u03bc\n", "timeout text evidence: \u03bc\n"),
            (None, ""),
            (b"truncated UTF-8: \xe2\x82", "truncated UTF-8: \ufffd"),
        ):
            with self.subTest(partial=partial), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "qualification"
                error = subprocess.TimeoutExpired(
                    ["fusion.py", "public", "cases"], 180, output=partial
                )
                with patch.object(release.subprocess, "run", side_effect=[
                    subprocess.CompletedProcess([], 0, "earlier success\n"), error,
                ]) as run, patch.object(release.time, "monotonic",
                                        side_effect=[10.0, 10.25, 20.0, 21.5]):
                    with self.assertRaises(subprocess.TimeoutExpired) as caught:
                        release.verify(output)
                self.assertIs(caught.exception, error)
                failed = self.assert_failed_qualification(
                    output, run, "TimeoutExpired", expected
                )
                self.assertIsNone(failed["returncode"])
                self.assertTrue(failed["timed_out"])
                self.assertEqual(failed["timeout_seconds"], 180)

    def test_nonzero_exit_retains_output_and_failed_operation(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "qualification"
            with patch.object(release.subprocess, "run", side_effect=[
                subprocess.CompletedProcess([], 0, "earlier success\n"),
                subprocess.CompletedProcess([], 2, "ordinary failure\n"),
            ]) as run, patch.object(release.time, "monotonic",
                                    side_effect=[10.0, 10.25, 20.0, 21.5]):
                with self.assertRaisesRegex(ValueError, "Failed release check: discovery"):
                    release.verify(output)
            failed = self.assert_failed_qualification(
                output, run, "ValueError", "ordinary failure\n"
            )
            self.assertEqual(failed["returncode"], 2)
            self.assertNotIn("timed_out", failed)


if __name__ == "__main__":
    unittest.main()
