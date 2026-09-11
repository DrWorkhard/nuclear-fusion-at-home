"""Active-penalty derivative qualification before guarded feasibility search."""

import argparse
import json
import time
from pathlib import Path

import numpy as np
from simsopt import load

from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.refined_curvature import make_refined_penalty


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    source = root / "evidence/affine-feasibility-v1-holdout.json"
    data = json.loads(source.read_text())
    result = {"schema_version": 1, "repository": git_state(root), "input": reference(source),
              "protocol": reference(root / "docs/optimization/GUARDED_FEASIBILITY_PROTOCOL.md"),
              "code": [reference(p) for p in (Path(__file__),
                  root / "src/fusion_baselines/refined_curvature.py")], "cases": []}
    for candidate in data["candidates"]:
        started = time.monotonic()
        path = Path(candidate["field"]["path"])
        if sha256_file(path) != candidate["field"]["sha256"]:
            raise ValueError("field hash mismatch")
        field = load(str(path))
        bases = [c.curve for c in field.coils[:4]]
        penalty = make_refined_penalty(bases, 0.99*candidate["a0"])
        x0 = penalty.x.copy()
        sizes = [len(base.x) for base in bases]
        split = np.cumsum(sizes)[:-1]
        direction = np.random.default_rng(43).normal(size=len(x0))
        direction /= np.linalg.norm(direction)
        calls = 0

        def evaluate(x, bases=bases, penalty=penalty, split=split):
            nonlocal calls
            calls += 1
            for base, values in zip(bases, np.split(x, split), strict=True):
                base.x = values.copy()
            return penalty.J(), penalty.dJ()

        value, gradient = evaluate(x0)
        analytic = float(gradient @ direction)
        checks = []
        try:
            for eps in [1e-4, 1e-5, 1e-6]:
                plus, _ = evaluate(x0 + eps*direction)
                minus, _ = evaluate(x0 - eps*direction)
                fd = (plus-minus)/(2*eps)
                checks.append({"eps": eps, "finite_difference": fd, "analytic": analytic,
                               "normalized_error": abs(fd-analytic)/max(1, abs(analytic))})
        finally:
            for base, values in zip(bases, np.split(x0, split), strict=True):
                base.x = values.copy()
        passed = (value > 0 and calls == 7 and checks[-1]["normalized_error"] <= 1e-6
                  and all(len(c.curve.quadpoints) == 200 for c in field.coils))
        result["cases"].append({"method": candidate["method"], "field": reference(path),
            "active_penalty": value, "checks": checks, "geometry_only_requests": calls,
            "full_vector_bundles": 0, "field_quadrature_unchanged": 200,
            "pass": passed, "elapsed_seconds": time.monotonic()-started})
    result["all_pass"] = all(c["pass"] for c in result["cases"])
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
