"""Run public unit/analytic controls with the standard library, without field studies."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

if __name__ == "__main__":
    tests = unittest.defaultTestLoader.discover(str(ROOT / "public_tests"))
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    raise SystemExit(0 if result.wasSuccessful() else 1)
