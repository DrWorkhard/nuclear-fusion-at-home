"""Final launch gates and supervision integration without scientific imports."""

import json
import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import launch_seeded_constellaration as launch  # noqa: E402


class LaunchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.now = datetime(2026, 10, 26, 7, tzinfo=UTC)
        self.digest = "a" * 64
        self.grant = dict(line="CAL-REQ-008 explicit seeded task window",
                          start=(self.now-timedelta(hours=1)).isoformat(),
                          end=(self.now+timedelta(days=1)).isoformat())
        self.manifest = dict(peer_grant=self.grant)
        self.coordination = self.root / "coordination"
        (self.coordination / "notes").mkdir(parents=True)
        (self.coordination / "automation").mkdir()
        (self.coordination / "notes/claude.md").write_text(self.grant["line"]+"\n")
        self.own = self.coordination / "notes/codex.md"
        self.own.write_text(f"C18-SEEDED-V1 CLAIM manifest={self.digest} "
                            f"start={self.now.isoformat()} "
                            f"end={(self.now+timedelta(hours=1)).isoformat()}\n")
        self.inventory = dict(checked_at=self.now.isoformat(), native_compute_pids=[],
                              controller_lock_held=True, other_codex_exec_worker=False)
        self.save_inventory(self.inventory)

    def save_inventory(self, inventory):
        (self.coordination / "automation/process-check.json").write_text(json.dumps(inventory))

    def live(self, **kwargs):
        return launch.check_live(self.manifest, self.digest, self.root, now=self.now, **kwargs)

    def test_current_full_window_and_exact_sixty_second_boundary(self):
        self.assertEqual(self.live(require_full_window=True)["inventory_age_seconds"], 0)
        self.inventory["checked_at"] = (self.now-timedelta(seconds=60)).isoformat()
        self.save_inventory(self.inventory)
        self.assertEqual(self.live()["inventory_age_seconds"], 60)

    def test_stale_future_occupied_and_unowned_inventory_rejected(self):
        cases = [dict(checked_at=(self.now-timedelta(seconds=60.001)).isoformat()),
                 dict(checked_at=(self.now+timedelta(seconds=.001)).isoformat()),
                 dict(native_compute_pids=[123]), dict(controller_lock_held=False),
                 dict(other_codex_exec_worker=True)]
        for change in cases:
            with self.subTest(change=change):
                inventory = {**self.inventory, **change}
                self.save_inventory(inventory)
                with self.assertRaises(ValueError):
                    self.live()

    def test_stop_missing_peer_and_wrong_manifest_claim_rejected(self):
        stop = self.coordination / "automation/STOP"
        stop.touch()
        with self.assertRaisesRegex(ValueError, "STOP"):
            self.live()
        stop.unlink()
        with self.assertRaisesRegex(ValueError, "manifest-specific"):
            launch.check_live(self.manifest, "b"*64, self.root, now=self.now)
        (self.coordination / "notes/claude.md").write_text("general lane free\n")
        with self.assertRaisesRegex(ValueError, "task-specific"):
            self.live()

    def test_live_inventory_allows_only_the_owned_native_child(self):
        self.inventory["native_compute_pids"] = [123]
        self.save_inventory(self.inventory)
        with self.assertRaisesRegex(ValueError, "occupied"):
            self.live()
        self.live(owned_native_pid=123)
        self.inventory["native_compute_pids"].append(456)
        self.save_inventory(self.inventory)
        with self.assertRaisesRegex(ValueError, "occupied"):
            self.live(owned_native_pid=123)

    def test_expired_short_future_and_duplicate_grants_rejected(self):
        for start, end in [(self.now-timedelta(hours=2), self.now),
                           (self.now+timedelta(seconds=1), self.now+timedelta(hours=1)),
                           (self.now-timedelta(hours=1), self.now+timedelta(seconds=1799))]:
            with self.subTest(start=start, end=end):
                self.manifest["peer_grant"] = {**self.grant, "start": start.isoformat(),
                                               "end": end.isoformat()}
                with self.assertRaises(ValueError):
                    self.live(require_full_window=True)
        self.manifest["peer_grant"] = self.grant
        (self.coordination / "notes/claude.md").write_text((self.grant["line"]+"\n")*2)
        with self.assertRaisesRegex(ValueError, "task-specific"):
            self.live()

    def test_path_escape_and_output_resource_limits(self):
        for value in ("/tmp/outside", "../outside", "a/../../outside"):
            with self.assertRaisesRegex(ValueError, "leaves"):
                launch.resolve(self.root, value)
        output = self.root / "output"
        output.mkdir()
        (output / "data").write_bytes(b"1234")
        limits = dict(start_disk_reserve_bytes=3, runtime_disk_reserve_bytes=2, output_bytes=4)
        with patch.object(launch.shutil, "disk_usage", return_value=SimpleNamespace(free=3)):
            launch.check_resources(output, limits, initial=True)
            with self.assertRaisesRegex(ValueError, "output size"):
                launch.check_resources(output, limits)
        with patch.object(launch.shutil, "disk_usage", return_value=SimpleNamespace(free=1)):
            with self.assertRaisesRegex(ValueError, "disk reserve"):
                launch.check_resources(output, limits)

    def test_main_readiness_no_spawn_and_supervised_outcomes(self):
        protocol = json.loads((ROOT / "docs/qi/seeded-comparison-v1.json").read_text())
        manifest = dict(self.manifest, output="output", native_python="native/bin/python",
                        supervisor="timer.py", resource_guard="guard.py", limits=protocol["limits"])
        path = self.root / "manifest.json"
        path.write_text(json.dumps(manifest))
        guard = SimpleNamespace(LIMITS={},
                                clean_environment=lambda output: {"OMP_NUM_THREADS": "1"})
        timer = SimpleNamespace(supervise=None, deadline=lambda *args: None)
        def modules(name, path):
            return timer if name == "seeded_timer" else guard
        argv = ["launcher", "--manifest", str(path), "--manifest-sha256", launch.sha(path),
                "--alignment-root", str(self.root)]
        for mode in ("ready", "mismatch", "failure", "late"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(dir=self.root) as directory:
                manifest["output"] = str(Path(directory).relative_to(self.root) / "output")
                path.write_text(json.dumps(manifest))
                argv[4] = launch.sha(path)
                calls = []

                def supervise(command, output, env, stop, *, limits, reservation_end,
                              calls=calls, mode=mode):
                    calls.append((command, limits))
                    launch.write(output / "child-started.json", dict(
                        manifest_sha256=launch.sha(path), pid=123))
                    (output / "rows").mkdir()
                    launch.write(output / "rows/comparison.json", dict(completed=True,
                                                                        all_agree=False))
                    return dict(exit_code=1 if mode == "failure" else 0,
                                stop_reason="elapsed-time limit" if mode == "late" else None)

                timer.supervise = supervise
                live = dict(claim_end=(datetime.now(UTC)+timedelta(hours=1)).isoformat())
                with patch.object(sys, "argv", argv+([] if mode == "ready" else ["--execute"])), \
                     patch.object(launch, "verify_files"), \
                     patch.object(launch, "check_live", return_value=live), \
                     patch.object(launch, "check_resources"), \
                     patch.object(launch, "module_from", side_effect=modules):
                    code = launch.main()
                self.assertEqual(len(calls), 0 if mode == "ready" else 1)
                output = self.root / manifest["output"]
                if mode == "ready":
                    self.assertFalse(output.exists())
                else:
                    outcome = launch.load(output / "launch-result.json")
                    self.assertEqual(code, 0 if mode == "mismatch" else 1)
                    self.assertEqual(outcome["completed"], mode == "mismatch")
                    self.assertLessEqual(calls[0][1]["wall_seconds"], 1740)
                    self.assertIn("--child", calls[0][0])
                    self.assertFalse(outcome["physical_admission"])

    def test_changed_file_blocks_before_support_import(self):
        path = self.root / "frozen.py"
        path.write_text("original")
        manifest = dict(files_sha256={"frozen.py": launch.sha(path)})
        path.write_text("changed")
        with self.assertRaisesRegex(ValueError, "frozen file mismatch"):
            launch.verify_files(manifest, self.root)


if __name__ == "__main__":
    unittest.main()
