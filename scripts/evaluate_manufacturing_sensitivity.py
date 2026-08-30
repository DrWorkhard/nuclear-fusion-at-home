#!/usr/bin/env python3
"""Evaluate the frozen reactor-scale manufacturing-sensitivity screen."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np
from simsopt.objectives import SquaredFlux
from stellcoilbench.path_utils import load_yaml
from stellcoilbench.post_processing import load_coils_and_surface
from stellcoilbench.sensitivity import compute_fb_perturbed, find_critical_sigma
from stellcoilbench.sensitivity._sensitivity_samplers import _build_unit_samplers


def sha256(path: Path) -> str:
    """Return the SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def percentile_ratio(values: np.ndarray, nominal: float, percentile: float) -> float:
    """Return the requested degradation percentile."""
    return float(np.percentile(values / nominal, percentile))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("coils_json", type=Path)
    parser.add_argument("case_yaml", type=Path)
    parser.add_argument("results_json", type=Path)
    parser.add_argument("output_json", type=Path)
    parser.add_argument("--plasma-surfaces-dir", type=Path)
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260830)
    args = parser.parse_args()

    for path in (args.coils_json, args.case_yaml, args.results_json):
        if not path.is_file():
            raise FileNotFoundError(path)

    recorded = json.loads(args.results_json.read_text())
    scaling = recorded["reactor_scale_metrics"]["scaling_factors"]
    length_scale = float(scaling["length_scale"])
    if not np.isfinite(length_scale) or length_scale <= 0:
        raise ValueError("invalid reactor length scale")

    protocol = {
        "version": 1,
        "correlation_length_reactor_m": 1.0,
        "sigma_min_reactor_m": 0.0001,
        "sigma_max_reactor_m": 0.05,
        "factor": 2.0,
        "percentile": 95.0,
        "samples_per_amplitude": args.samples,
        "seed": args.seed,
        "bisection_relative_tolerance": 0.05,
        "max_bisection_iterations": 20,
    }
    correlation_length = protocol["correlation_length_reactor_m"] / length_scale
    sigma_min = protocol["sigma_min_reactor_m"] / length_scale
    sigma_max = protocol["sigma_max_reactor_m"] / length_scale

    started = time.perf_counter()
    field, surface = load_coils_and_surface(
        args.coils_json,
        args.case_yaml,
        args.plasma_surfaces_dir,
    )
    case = load_yaml(path=args.case_yaml)
    case_terms = case.get("coil_objective_terms", {})
    recorded_thresholds = recorded.get("metrics", {}).get("_cached_thresholds", {})
    flux_threshold_source = "results.metrics._cached_thresholds.flux_threshold"
    flux_threshold = recorded_thresholds.get("flux_threshold")
    if flux_threshold is None:
        flux_threshold_source = "case.coil_objective_terms"
        flux_threshold = case_terms.get("flux_threshold")
    if flux_threshold is None:
        flux_threshold = case_terms.get("squared_flux", {}).get("threshold", 0.0)
    nominal = float(SquaredFlux(surface, field, threshold=flux_threshold).J())
    samplers = _build_unit_samplers(field.coils, correlation_length)

    endpoint_values = {}
    for name, sigma in (("lower", sigma_min), ("upper", sigma_max)):
        values = compute_fb_perturbed(
            field,
            surface,
            sigma=sigma,
            correlation_length_m=correlation_length,
            n_samples=args.samples,
            seed=args.seed,
            flux_threshold=flux_threshold,
            samplers=samplers,
        )
        endpoint_values[name] = {
            "sigma_device_m": sigma,
            "sigma_reactor_m": sigma * length_scale,
            "percentile_ratio": percentile_ratio(
                values, nominal, protocol["percentile"]
            ),
            "mean_ratio": float(np.mean(values / nominal)),
            "finite": bool(np.all(np.isfinite(values))),
        }

    bracketed = (
        endpoint_values["lower"]["percentile_ratio"] <= protocol["factor"]
        and endpoint_values["upper"]["percentile_ratio"] > protocol["factor"]
    )
    sigma_star_device = None
    history = []
    if bracketed:
        sigma_star_device, raw_history = find_critical_sigma(
            field,
            surface,
            nominal_fb=nominal,
            correlation_length_m=correlation_length,
            n_samples=args.samples,
            factor=protocol["factor"],
            percentile=protocol["percentile"],
            sigma_min=sigma_min,
            sigma_max=sigma_max,
            seed=args.seed,
            flux_threshold=flux_threshold,
            bisection_tol=protocol["bisection_relative_tolerance"],
            max_bisection_iter=protocol["max_bisection_iterations"],
            samplers=samplers,
        )
        history = [
            {
                "sigma_device_m": step.sigma,
                "sigma_reactor_m": step.sigma * length_scale,
                "percentile_ratio": step.percentile_ratio,
                "n_samples": step.n_samples,
            }
            for step in raw_history
        ]

    output = {
        "schema_version": 1,
        "metric": "stellcoilbench_gp_manufacturing_sensitivity",
        "protocol": protocol,
        "coordinate_scaling": {
            "length_scale": length_scale,
            "correlation_length_device_m": correlation_length,
            "sigma_min_device_m": sigma_min,
            "sigma_max_device_m": sigma_max,
        },
        "result": {
            "nominal_squared_flux": nominal,
            "flux_threshold": flux_threshold,
            "flux_threshold_source": flux_threshold_source,
            "physical_coil_count": len(field.coils),
            "endpoints": endpoint_values,
            "bracketed": bracketed,
            "critical_sigma_device_m": sigma_star_device,
            "critical_sigma_reactor_m": (
                sigma_star_device * length_scale if sigma_star_device is not None else None
            ),
            "bisection_history": history,
            "elapsed_seconds": time.perf_counter() - started,
        },
        "inputs": {
            "coils_json": str(args.coils_json.resolve()),
            "coils_sha256": sha256(args.coils_json),
            "case_yaml": str(args.case_yaml.resolve()),
            "case_sha256": sha256(args.case_yaml),
            "results_json": str(args.results_json.resolve()),
            "results_sha256": sha256(args.results_json),
        },
        "host": {"machine": platform.machine(), "python": platform.python_version()},
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
