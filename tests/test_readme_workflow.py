"""Execute the documented contribution route in a small disposable copy."""

import json
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def copied_tree(tmp_path):
    for name in ("src/fusion_public", "examples", "public_tests"):
        shutil.copytree(ROOT / name, tmp_path / name,
                        ignore=shutil.ignore_patterns("__pycache__"))
    (tmp_path / "scripts").mkdir()
    for name in ("fusion.py", "scripts/test_public.py", ".gitignore"):
        shutil.copyfile(ROOT / name, tmp_path / name)


def test_readme_commands_verbatim_and_trackable_candidate(tmp_path):
    copied_tree(tmp_path)
    blocks = re.findall(r"```bash\n(.*?)```", (ROOT / "README.md").read_text(encoding="utf-8"),
                        flags=re.DOTALL)
    commands = [shlex.split(line) for block in blocks for line in block.splitlines()
                if line.startswith("python ")]
    assert len(commands) == 7
    outputs = []
    for command in commands:
        completed = subprocess.run([sys.executable, "-I", "-S", *command[1:]],
                                   cwd=tmp_path, capture_output=True, text=True, timeout=60)
        assert completed.returncode == 0, completed.stdout + completed.stderr
        outputs.append(completed.stdout)
    demo = json.loads(outputs[1])
    assert demo["reference_reproduced"]
    assert all(v["change"] == 0. for v in demo["comparison"]["scores"].values())
    candidate = json.loads((tmp_path / "submissions/my-coil-study/candidate.json").read_text())
    assert candidate["base_coefficients"][0][0][0] == 0.9609191138350243
    assert json.loads(outputs[-1])["report_replay_pass"]
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    staged = subprocess.run(["git", "add", "submissions/my-coil-study/candidate.json"],
                            cwd=tmp_path, capture_output=True, text=True)
    assert staged.returncode == 0, staged.stderr
    ignored = subprocess.run(["git", "check-ignore", "results/my-report.json"],
                             cwd=tmp_path, capture_output=True, text=True)
    assert ignored.returncode == 0


def test_quickstart_python_example_runs_and_preserves_reference(tmp_path):
    copied_tree(tmp_path)
    text = (ROOT / "docs/validation/PUBLIC_QUICKSTART.md").read_text(encoding="utf-8")
    blocks = re.findall(r"```python\n(.*?)```", text, flags=re.DOTALL)
    assert len(blocks) == 1
    completed = subprocess.run([sys.executable, "-I", "-S", "-c", blocks[0]],
                               cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.count("'delta_m':") == 3
    assert "'sampled_normal_rms': 0.0, 'sampled_inner_vector_rms': 0.0" in completed.stdout
