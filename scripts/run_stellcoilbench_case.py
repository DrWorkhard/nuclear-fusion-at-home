"""Run one pinned StellCoilBench case in an explicit, self-describing directory."""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
from pathlib import Path

from stellcoilbench.case_loader import load_case
from stellcoilbench.cli_helpers import NumpyJSONEncoder
from stellcoilbench.coil_optimization import optimize_coils
from stellcoilbench.submission_packaging import _build_submission_dict

from fusion_baselines.provenance import build_run_record, sha256_file, write_json_atomic


def instrument_auglag_scipy_calls() -> tuple[object, list[dict[str, object]]]:
    """Wrap SciPy minimizations made inside SIMSOPT's augmented Lagrangian."""
    module = importlib.import_module("simsopt.solve.augmented_lagrangian")
    original = module.minimize
    calls: list[dict[str, object]] = []

    def counted_minimize(*args, **kwargs):
        result = original(*args, **kwargs)
        calls.append(
            {
                "nfev": int(getattr(result, "nfev", 0)),
                "njev": int(getattr(result, "njev", 0)),
                "nit": int(getattr(result, "nit", 0)),
                "success": bool(getattr(result, "success", False)),
                "message": str(getattr(result, "message", "")),
            }
        )
        return result

    module.minimize = counted_minimize
    return original, calls


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    case_path = args.case.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    local_case = output / "case.yaml"
    shutil.copy2(case_path, local_case)

    original_config = load_case(case_path)
    surface_name = original_config.surface_params["surface"]
    source_surface = project_root / "external/stellcoilbench/plasma_surfaces" / surface_name
    if not source_surface.is_file():
        raise FileNotFoundError(f"Pinned surface is missing: {source_surface}")
    local_surface = output / surface_name
    shutil.copy2(source_surface, local_surface)

    provenance = build_run_record(
        project_root,
        {
            "stellcoilbench": project_root / "external/stellcoilbench",
            "simsopt": project_root / "external/simsopt",
        },
    )
    provenance["input"] = {
        "original_path": str(case_path),
        "local_path": str(local_case),
        "sha256": sha256_file(local_case),
        "surface_original_path": str(source_surface),
        "surface_local_path": str(local_surface),
        "surface_sha256": sha256_file(local_surface),
    }
    write_json_atomic(output / "provenance.json", provenance)

    case_config = load_case(local_case)
    original_minimize = None
    auglag_calls: list[dict[str, object]] = []
    if str(case_config.optimizer_params.get("algorithm", "")).lower() == (
        "augmented_lagrangian"
    ):
        original_minimize, auglag_calls = instrument_auglag_scipy_calls()
    try:
        metrics = optimize_coils(
            case_path=local_case,
            coils_out_path=output / "coils.json",
            case_cfg=case_config,
            output_dir=output,
        )
    finally:
        if original_minimize is not None:
            module = importlib.import_module("simsopt.solve.augmented_lagrangian")
            module.minimize = original_minimize
    submission = _build_submission_dict(metrics, case_config)
    if auglag_calls:
        submission["metrics"]["auglag_scipy_accounting"] = {
            "scope": "inner scipy.optimize.minimize calls only",
            "outer_subproblems": auglag_calls,
            "total_nfev": sum(int(call["nfev"]) for call in auglag_calls),
            "total_njev": sum(int(call["njev"]) for call in auglag_calls),
            "total_nit": sum(int(call["nit"]) for call in auglag_calls),
            "excludes": [
                "augmented-Lagrangian setup and post-step evaluations",
                "Taylor-test evaluations",
                "post-processing evaluations",
            ],
        }
    (output / "results.json").write_text(
        json.dumps(submission, indent=2, cls=NumpyJSONEncoder) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
