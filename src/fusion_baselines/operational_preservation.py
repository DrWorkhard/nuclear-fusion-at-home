"""Exact, reviewed non-scientific maintenance exceptions to the historical tree freeze.

Version 1, public release review of 2026-09-23. This is not a scientific acceptance
change. Original bytes remain in Git; arbitrary future changes fail closed.
"""

import hashlib
import subprocess

# path: (SHA256 of original 5971fee bytes, SHA256 of reviewed replacement bytes)
APPROVED = {
    "scripts/run_core_ci.sh": (
        "97b04c3b98033a45e6098e17d3803e583d40d4d278ebdcf86fcf2876b6ce15ae",
        "39dedbd0d0ba3c853270d413f6d291cd2f3271e527ed1b36a22614bc64953e2e",
    ),
    "src/fusion_baselines/documentation.py": (
        "fe8bd532e099fac4c83dabc92e39f301992de9d91194f8758a92e19aa7c80ca1",
        "3e185a879f958cde227aa5193b1b4cd3c98f33502e2351874cf6d012c119c8e1",
    ),
}


def approved_change(root, base, path):
    """Authorize only the exact old/new byte pair; never a path-wide exemption."""
    if path not in APPROVED or (root / path).is_symlink():
        return False
    try:
        old = subprocess.check_output(["git", "show", f"{base}:{path}"], cwd=root)
        new = (root / path).read_bytes()
    except (OSError, subprocess.CalledProcessError):
        return False
    return (hashlib.sha256(old).hexdigest(), hashlib.sha256(new).hexdigest()) == APPROVED[path]
