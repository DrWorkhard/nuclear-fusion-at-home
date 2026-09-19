"""Thin CLI contract controls; scientific backends are never executed here."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

from fusion_baselines import workflow_cli

cli = workflow_cli

PROFILE = "clear-coil-field-start-v1"
SOURCE_ROOT = Path(__file__).resolve().parents[1]


def checkout(path):
    path.mkdir(parents=True)
    (path / "src/fusion_baselines").mkdir(parents=True)
    (path / "src/fusion_baselines/cli.py").write_text("# synthetic checkout marker\n")
    (path / "pyproject.toml").write_text('[project]\nname = "fusion-baselines"\n')
    (path / "scripts").mkdir()
    for name in ("run_clear_coil_field_start.py", "audit_clear_coil_field_start.py"):
        (path / "scripts" / name).write_text(
            "raise RuntimeError('must never execute test backend')\n"
        )
    return path.resolve()


def arguments(operation, output, root=None, source=None, dry=False):
    argv = [operation, "--profile", PROFILE, "--output", str(output)]
    if root is not None:
        argv += ["--project-root", str(root)]
    if source is not None:
        argv += ["--run", str(source)]
    if dry:
        argv += ["--dry-run"]
    return cli._parser().parse_args(argv)


def forbid_dispatch(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("a non-executing CLI operation attempted a subprocess")

    monkeypatch.setattr(workflow_cli.subprocess, "run", forbidden)


def test_catalog_declares_only_fixed_non_candidate_profile_and_returns_isolated_copy():
    catalog = workflow_cli.profile_catalog()
    assert catalog["schema_version"] == 1 and len(catalog["profiles"]) == 1
    profile = catalog["profiles"][0]
    assert profile["id"] == PROFILE and profile["supports_candidate_input"] is False
    assert profile["operations"] == ["evaluate", "audit"]
    assert profile["fixed_matrix"] == {
        "cells": 4,
        "targets": ["reference", "selected"],
        "base_coils": [6, 8],
    }
    assert profile["evaluate_limits"]["automatic_retries"] == 0
    assert profile["evaluate_limits"]["search_calls"] == 0
    profile["fixed_matrix"]["base_coils"].append(100)
    assert workflow_cli.profile_catalog()["profiles"][0]["fixed_matrix"]["base_coils"] == [6, 8]
    json.dumps(workflow_cli.profile_catalog(), allow_nan=False)


@pytest.mark.parametrize("as_json", [False, True])
def test_profiles_cli_is_stable_discovery_without_dispatch_or_output_files(
    monkeypatch, tmp_path, capsys, as_json
):
    monkeypatch.chdir(tmp_path)
    forbid_dispatch(monkeypatch)
    argv = ["fusion-baselines", "profiles"] + (["--json"] if as_json else [])
    monkeypatch.setattr(sys, "argv", argv)
    assert cli.main() == 0
    first = capsys.readouterr().out
    assert cli.main() == 0
    assert capsys.readouterr().out == first
    assert list(tmp_path.iterdir()) == []
    if as_json:
        assert json.loads(first) == workflow_cli.profile_catalog()
    else:
        assert PROFILE in first and "not physical" in first.lower()


@pytest.mark.parametrize("operation", ["evaluate", "audit"])
def test_plan_and_dry_run_keep_absolute_argument_boundaries_without_side_effects(
    monkeypatch, tmp_path, capsys, operation
):
    root = checkout(tmp_path / "research checkout with spaces")
    caller = tmp_path / "outside cwd"
    caller.mkdir()
    monkeypatch.chdir(caller)
    source = caller / "saved run with spaces.json"
    source.write_text("backend performs JSON and scientific admission\n")
    relative_output = Path("missing parent with spaces") / (
        "new run;not-a-shell-command" if operation == "evaluate" else "new audit.json"
    )
    args = arguments(
        operation,
        relative_output,
        root,
        Path(source.name) if operation == "audit" else None,
        dry=True,
    )
    forbid_dispatch(monkeypatch)
    before = sorted(str(path) for path in tmp_path.rglob("*"))
    record = workflow_cli.plan(args)
    expected_output = str(caller / relative_output)
    backend = (
        root
        / "scripts"
        / (
            "run_clear_coil_field_start.py"
            if operation == "evaluate"
            else "audit_clear_coil_field_start.py"
        )
    )
    expected_command = [sys.executable, str(backend)] + (
        ["--raw", expected_output]
        if operation == "evaluate"
        else ["--run", str(source), "--output", expected_output]
    )
    assert record["schema_version"] == 1 and record["kind"] == "fusion-command-plan"
    assert record["operation"] == operation and record["profile"] == PROFILE
    assert record["project_root"] == record["cwd"] == str(root)
    assert record["command"] == expected_command
    assert record["output"] == expected_output and record["dry_run"] is True
    assert record["input"] == (None if operation == "evaluate" else str(source))
    assert record["backend_report"] == (
        str(caller / relative_output / "run.json") if operation == "evaluate" else expected_output
    )
    assert record["physical_admission_implied"] is False
    assert "backend" in record["prerequisites_checked"].lower()
    assert workflow_cli.execute(args) == 0
    assert json.loads(capsys.readouterr().out) == record
    assert sorted(str(path) for path in tmp_path.rglob("*")) == before


@pytest.mark.parametrize("choice", ["explicit", "cwd", "source"])
def test_project_root_resolution_precedence(monkeypatch, tmp_path, choice):
    enclosing = checkout(tmp_path / "enclosing")
    explicit = checkout(tmp_path / "explicit")
    nested = enclosing / "nested/deeper"
    nested.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.chdir(outside if choice == "source" else nested)
    args = arguments("evaluate", "unused-run", explicit if choice == "explicit" else None)
    record = workflow_cli.plan(args)
    expected = {"explicit": explicit, "cwd": enclosing, "source": SOURCE_ROOT}[choice]
    assert record["project_root"] == str(expected.resolve())
    assert not (Path.cwd() / "unused-run").exists()


@pytest.mark.parametrize(
    "bad",
    [
        "missing",
        "wrong-project",
        "missing-cli",
        "missing-backend",
        "backend-directory",
        "backend-escape",
        "malformed-toml",
    ],
)
def test_invalid_explicit_checkout_or_backend_never_falls_back_or_dispatches(
    monkeypatch, tmp_path, bad
):
    root = checkout(tmp_path / "root")
    if bad == "missing":
        root = tmp_path / "absent"
    elif bad == "wrong-project":
        (root / "pyproject.toml").write_text('[project]\nname="unrelated"\n')
    elif bad == "missing-cli":
        (root / "src/fusion_baselines/cli.py").unlink()
    elif bad == "malformed-toml":
        (root / "pyproject.toml").write_text("[invalid syntax\n")
    else:
        backend = root / "scripts/run_clear_coil_field_start.py"
        backend.unlink()
        if bad == "backend-directory":
            backend.mkdir()
        elif bad == "backend-escape":
            elsewhere = tmp_path / "not-allowlisted.py"
            elsewhere.write_text("raise RuntimeError('must not execute')\n")
            backend.symlink_to(elsewhere)
    forbid_dispatch(monkeypatch)
    output = tmp_path / "fresh-output"
    with pytest.raises((ValueError, OSError)):
        workflow_cli.execute(arguments("evaluate", output, root))
    assert not output.exists()


@pytest.mark.parametrize("operation", ["evaluate", "audit"])
@pytest.mark.parametrize(
    "kind", ["file", "directory", "symlink", "dangling-symlink", "parent-file"]
)
def test_nonfresh_or_unusable_output_is_rejected_before_dispatch(
    monkeypatch, tmp_path, operation, kind
):
    root = checkout(tmp_path / "root")
    source = tmp_path / "existing-run.json"
    source.write_text("{}")
    output = tmp_path / "existing-output"
    if kind == "file":
        output.write_text("immutable evidence")
    elif kind == "directory":
        output.mkdir()
    elif kind == "symlink":
        output.symlink_to(source)
    elif kind == "dangling-symlink":
        output.symlink_to(tmp_path / "absent-target")
    else:
        output.write_text("not a directory")
        output = output / "child"
    forbid_dispatch(monkeypatch)
    with pytest.raises((ValueError, OSError)):
        workflow_cli.execute(
            arguments(operation, output, root, source if operation == "audit" else None)
        )
    assert source.read_text() == "{}"


@pytest.mark.parametrize("kind", ["file", "symlink", "dangling-symlink"])
def test_audit_preserves_preexisting_atomic_temp_name(monkeypatch, tmp_path, kind):
    root = checkout(tmp_path / "root")
    source = tmp_path / "run.json"
    source.write_text("{}")
    output = tmp_path / "fresh-audit.json"
    temporary = tmp_path / "fresh-audit.json.tmp"
    if kind == "file":
        temporary.write_text("existing checkpoint")
    else:
        temporary.symlink_to(source if kind == "symlink" else tmp_path / "absent")
    forbid_dispatch(monkeypatch)
    with pytest.raises((ValueError, OSError)):
        workflow_cli.execute(arguments("audit", output, root, source))
    assert not output.exists() and source.read_text() == "{}"
    assert (
        temporary.is_symlink() if kind != "file" else temporary.read_text() == "existing checkpoint"
    )


@pytest.mark.parametrize("kind", ["missing", "directory", "dangling-symlink"])
def test_audit_input_must_be_existing_regular_file(monkeypatch, tmp_path, kind):
    root = checkout(tmp_path / "root")
    source = tmp_path / "input.json"
    if kind == "directory":
        source.mkdir()
    elif kind == "dangling-symlink":
        source.symlink_to(tmp_path / "absent")
    forbid_dispatch(monkeypatch)
    with pytest.raises((ValueError, OSError)):
        workflow_cli.execute(arguments("audit", tmp_path / "out.json", root, source))


@pytest.mark.parametrize("operation", ["evaluate", "audit"])
@pytest.mark.parametrize("returncode", [0, 1, 2, 23])
def test_dispatch_is_single_allowlisted_subprocess_with_inherited_stdio_and_exact_exitcode(
    monkeypatch, tmp_path, capsys, operation, returncode
):
    root = checkout(tmp_path / "root")
    source = tmp_path / "input.json"
    source.write_text("{}")
    monkeypatch.setenv("PYTHONPATH", "must-not-leak-to-backend")
    monkeypatch.setenv("OMP_NUM_THREADS", "32")
    monkeypatch.setenv("OMPI_MCA_btl", "must-be-overridden")
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "explicit mpl cache"))
    monkeypatch.setenv("FUSION_CLI_TEST_SENTINEL", "preserved unrelated environment")
    observed = []

    def launch(command, **kwargs):
        observed.append((command, kwargs))
        return SimpleNamespace(returncode=returncode)

    monkeypatch.setattr(workflow_cli.subprocess, "run", launch)
    args = arguments(
        operation, tmp_path / "new-output", root, source if operation == "audit" else None
    )
    expected = workflow_cli.plan(args)
    assert workflow_cli.execute(args) == returncode and len(observed) == 1
    command, options = observed[0]
    assert command == expected["command"]
    assert options["shell"] is False and options["check"] is False
    assert options["cwd"] == str(root)
    assert not ({"stdin", "stdout", "stderr", "capture_output"} & set(options))
    environment = options["env"]
    assert environment["PYTHONPATH"] == str(root / "src")
    assert all(environment[key] == "1" for key in workflow_cli.THREADS)
    assert environment["OMPI_MCA_btl"] == "self"
    assert environment["MPLCONFIGDIR"] == str(tmp_path / "explicit mpl cache")
    assert environment["FUSION_CLI_TEST_SENTINEL"] == "preserved unrelated environment"
    assert os.environ["OMP_NUM_THREADS"] == "32"
    assert os.environ["PYTHONPATH"] == "must-not-leak-to-backend"
    assert capsys.readouterr().out == ""  # No invented physical pass on backend exit zero.
    assert not (tmp_path / "new-output").exists()


def test_default_mpl_cache_is_only_planned_not_created(monkeypatch, tmp_path):
    root = checkout(tmp_path / "root")
    monkeypatch.delenv("MPLCONFIGDIR", raising=False)
    record = workflow_cli.plan(arguments("evaluate", tmp_path / "fresh", root))
    assert record["environment"]["MPLCONFIGDIR"] == str(
        Path(tempfile.gettempdir()) / "fusion-mpl-cache"
    )


@pytest.mark.parametrize(
    "argv",
    [
        ["evaluate", "--profile", "unregistered", "--output", "x"],
        ["evaluate", "--profile", PROFILE],
        ["audit", "--profile", PROFILE, "--output", "x"],
        *[
            ["evaluate", "--profile", PROFILE, "--output", "x", option, "arbitrary"]
            for option in ("--design", "--backend", "--worker", "--nbase", "--target", "--retry")
        ],
    ],
)
def test_cli_rejects_unregistered_inputs_and_all_candidate_or_backend_overrides(argv):
    with pytest.raises(SystemExit) as error:
        cli._parser().parse_args(argv)
    assert error.value.code == 2


def test_programmatic_unregistered_profile_is_rejected_without_dispatch(monkeypatch, tmp_path):
    forbid_dispatch(monkeypatch)
    args = argparse.Namespace(command="evaluate", profile="unregistered", output=tmp_path / "fresh")
    with pytest.raises(ValueError):
        workflow_cli.execute(args)


def test_main_reports_setup_failure_as_exit_one(monkeypatch, tmp_path, capsys):
    forbid_dispatch(monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fusion-baselines",
            "evaluate",
            "--profile",
            PROFILE,
            "--output",
            str(tmp_path / "new"),
            "--project-root",
            str(tmp_path / "missing-checkout"),
        ],
    )
    assert cli.main() == 1
    assert "ERROR:" in capsys.readouterr().err
    assert not (tmp_path / "new").exists()


@pytest.mark.parametrize("signal", [2, 9, 15])
def test_backend_signal_is_mapped_to_conventional_cli_exit_without_retry(
    monkeypatch, tmp_path, signal
):
    root = checkout(tmp_path / "root")
    calls = []

    def launch(*args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=-signal)

    monkeypatch.setattr(workflow_cli.subprocess, "run", launch)
    assert workflow_cli.execute(arguments("evaluate", tmp_path / "new", root)) == 128 + signal
    assert len(calls) == 1


def test_keyboard_interrupt_is_exit130_not_completed_backend_result(monkeypatch, tmp_path, capsys):
    root = checkout(tmp_path / "root")

    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(workflow_cli.subprocess, "run", interrupted)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fusion-baselines",
            "evaluate",
            "--profile",
            PROFILE,
            "--output",
            str(tmp_path / "new"),
            "--project-root",
            str(root),
        ],
    )
    assert cli.main() == 130
    assert "not a completed result" in capsys.readouterr().err
    assert not (tmp_path / "new").exists()


@pytest.mark.parametrize(
    "argv", [["--help"], ["evaluate", "--help"], ["audit", "--help"], ["profiles", "--json"]]
)
def test_module_entrypoint_discovery_and_help_are_stdlib_only(tmp_path, argv):
    program = textwrap.dedent("""
        import importlib.abc
        import runpy
        import sys
        class NoScientificImports(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname.split('.')[0] in {'numpy', 'scipy', 'netCDF4', 'simsopt', 'simsoptpp'}:
                    raise RuntimeError('unexpected scientific import: ' + fullname)
        sys.meta_path.insert(0, NoScientificImports())
        sys.argv = ['fusion-baselines', *sys.argv[1:]]
        runpy.run_module('fusion_baselines', run_name='__main__')
    """)
    environment = dict(os.environ, PYTHONPATH=str(SOURCE_ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
    completed = subprocess.run(
        [sys.executable, "-c", program, *argv],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert not completed.stderr
    if "--json" in argv:
        assert json.loads(completed.stdout) == workflow_cli.profile_catalog()
    else:
        assert "usage:" in completed.stdout.lower()
    assert list(tmp_path.iterdir()) == []


def test_literal_python_module_entrypoint_from_outside_checkout(tmp_path):
    completed = subprocess.run(
        [sys.executable, "-m", "fusion_baselines", "profiles", "--json"],
        cwd=tmp_path,
        env=dict(os.environ, PYTHONPATH=str(SOURCE_ROOT / "src"), PYTHONDONTWRITEBYTECODE="1"),
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == workflow_cli.profile_catalog()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("argv", [["profiles", "--json"], ["evaluate", "--help"]])
def test_root_launcher_works_without_pythonpath_or_installation_from_outside_checkout(
    tmp_path, argv
):
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    environment.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [sys.executable, str(SOURCE_ROOT / "fusion.py"), *argv],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert not completed.stderr
    if "--json" in argv:
        assert json.loads(completed.stdout) == workflow_cli.profile_catalog()
    else:
        assert "usage:" in completed.stdout.lower()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "relative, expected",
    [
        (
            "src/fusion_baselines/cli.py",
            "86ca7a6102e62c4993082e0253ca9c9ff0c8fa7efa06781dc6865e0129bc3954",
        ),
        ("pyproject.toml", "0af21f7026e1802cbdcf8fda60b0aa2534f56c5c8dc7df54809bf24bad543fa7"),
    ],
)
def test_new_entrypoints_preserve_historical_cli_and_project_config_bytes(relative, expected):
    # Both digests are from committed5971fee, not the new implementation.
    assert hashlib.sha256((SOURCE_ROOT / relative).read_bytes()).hexdigest() == expected
