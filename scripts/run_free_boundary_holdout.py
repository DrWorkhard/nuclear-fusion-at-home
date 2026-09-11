#!/usr/bin/env python3
"""Run a strictly post-optimization VMEC++ vacuum free-boundary holdout."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import time
from importlib.metadata import version
from pathlib import Path

import numpy as np
import vmecpp


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_head(path: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _truncated_input(source: Path, phiedge: float, *, free_boundary: bool):
    original = vmecpp.VmecInput.from_file(source)
    data = original.model_dump(mode="json")
    data.update(
        {
            "mpol": 6,
            "ntor": 6,
            "raxis_c": np.asarray(original.raxis_c[:7], dtype=float),
            "zaxis_s": np.asarray(original.zaxis_s[:7], dtype=float),
            "ntheta": 0,
            "nzeta": 24,
            "ns_array": np.array([8, 16, 31], dtype=np.int64),
            "ftol_array": np.full(3, 1.0e-9),
            "niter_array": np.full(3, 2000, dtype=np.int64),
            "nstep": 200,
            "phiedge": phiedge,
            "gamma": 0.0,
            "am": np.array([0.0]),
            "pres_scale": 0.0,
            "ncurr": 1,
            "pcurr_type": "power_series",
            "ac": np.array([0.0]),
            "curtor": 0.0,
            "lfreeb": free_boundary,
            "mgrid_file": "",
            "nvacskip": 6,
            "return_outputs_even_if_not_converged": True,
        }
    )
    if not free_boundary:
        data["extcur"] = np.array([])
    return vmecpp.VmecInput.model_validate(data)


def _target_modes(vmec_input) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    m_values = []
    n_values = []
    r_values = []
    z_values = []
    ntor = int(vmec_input.ntor)
    for m in range(int(vmec_input.mpol)):
        for n in range(-ntor, ntor + 1):
            r = float(vmec_input.rbc[m, n + ntor])
            z = float(vmec_input.zbs[m, n + ntor])
            if r != 0.0 or z != 0.0:
                m_values.append(m)
                n_values.append(n * int(vmec_input.nfp))
                r_values.append(r)
                z_values.append(z)
    mode_values = (m_values, n_values, r_values, z_values)
    return tuple(np.asarray(values, dtype=float) for values in mode_values)


def _cross_section(
    m: np.ndarray,
    n: np.ndarray,
    r_coeff: np.ndarray,
    z_coeff: np.ndarray,
    phi_fraction: float,
    count: int = 400,
) -> np.ndarray:
    theta = np.linspace(0.0, 2.0 * np.pi, count, endpoint=False)
    phi = 2.0 * np.pi * phi_fraction
    phase = np.outer(theta, m) - phi * n[None, :]
    radius = np.cos(phase) @ r_coeff
    z = np.sin(phase) @ z_coeff
    return np.column_stack((radius, z))


def _wout_modes(wout) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    m = np.asarray(wout.xm, dtype=float)
    n = np.asarray(wout.xn, dtype=float)
    r_all = np.asarray(wout.rmnc, dtype=float)
    z_all = np.asarray(wout.zmns, dtype=float)
    r_edge = r_all[:, -1] if r_all.shape[0] == len(m) else r_all[-1]
    z_edge = z_all[:, -1] if z_all.shape[0] == len(m) else z_all[-1]
    return (
        m,
        n,
        r_edge,
        z_edge,
    )


def _surface_volume(
    m: np.ndarray,
    n: np.ndarray,
    r_coeff: np.ndarray,
    z_coeff: np.ndarray,
    count: int = 256,
) -> float:
    theta = np.linspace(0.0, 2.0 * np.pi, count, endpoint=False)
    phi = np.linspace(0.0, 2.0 * np.pi, count, endpoint=False)
    theta_grid, phi_grid = np.meshgrid(theta, phi, indexing="ij")
    phase = (
        theta_grid[..., None] * m[None, None, :]
        - phi_grid[..., None] * n[None, None, :]
    )
    cosine = np.cos(phase)
    sine = np.sin(phase)
    radius = cosine @ r_coeff
    z = sine @ z_coeff
    r_theta = (-sine * m) @ r_coeff
    r_phi = (sine * n) @ r_coeff
    z_theta = (cosine * m) @ z_coeff
    z_phi = (-cosine * n) @ z_coeff
    cos_phi = np.cos(phi_grid)
    sin_phi = np.sin(phi_grid)
    xyz = np.stack((radius * cos_phi, radius * sin_phi, z), axis=-1)
    d_theta = np.stack((r_theta * cos_phi, r_theta * sin_phi, z_theta), axis=-1)
    d_phi = np.stack(
        (
            r_phi * cos_phi - radius * sin_phi,
            r_phi * sin_phi + radius * cos_phi,
            z_phi,
        ),
        axis=-1,
    )
    integrand = np.sum(xyz * np.cross(d_theta, d_phi), axis=-1) / 3.0
    return abs(float(np.mean(integrand) * (2.0 * np.pi) ** 2))


def _symmetric_rms_distance(first: np.ndarray, second: np.ndarray) -> float:
    squared = np.sum((first[:, None, :] - second[None, :, :]) ** 2, axis=2)
    return math.sqrt(
        0.5 * (float(np.mean(np.min(squared, axis=1))) + float(np.mean(np.min(squared, axis=0))))
    )


def _axis_curve(wout, count: int = 128) -> np.ndarray:
    phi = np.linspace(0.0, 2.0 * np.pi, count, endpoint=False)
    modes = np.arange(len(wout.raxis_cc)) * int(wout.nfp)
    return np.cos(np.outer(phi, modes)) @ np.asarray(wout.raxis_cc, dtype=float)


def _run(vmec_input, *, threads: int, magnetic_field=None) -> tuple[object, float]:
    started = time.perf_counter()
    output = vmecpp.run(
        vmec_input,
        magnetic_field=magnetic_field,
        max_threads=threads,
        verbose=False,
    )
    return output, time.perf_counter() - started


def _summary(wout, elapsed_s: float) -> dict:
    residuals = {name: float(getattr(wout, name)) for name in ("fsqr", "fsqz", "fsql")}
    return {
        "elapsed_s": elapsed_s,
        "ier_flag": int(wout.ier_flag),
        "force_residuals": residuals,
        "residual_converged": int(wout.ier_flag) == 0
        and max(residuals.values()) <= 1.01e-9,
        "niter": int(wout.niter),
        "volume_m3": float(wout.volume_p),
        "aspect": float(wout.aspect),
        "iota_axis": float(wout.iotaf[0]),
        "iota_edge": float(wout.iotaf[-1]),
        "beta_total": float(wout.betatotal),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared-case", type=Path, required=True)
    parser.add_argument("--vmec-input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--mgrid-points", type=int, default=101)
    args = parser.parse_args()
    prepared = json.loads(args.prepared_case.read_text())
    args.output_dir.mkdir(parents=True, exist_ok=True)

    fixed_input = _truncated_input(args.vmec_input, prepared["phiedge_Wb"], free_boundary=False)
    free_input = _truncated_input(args.vmec_input, prepared["phiedge_Wb"], free_boundary=True)
    free_input.extcur = np.asarray(prepared["extcur_A"], dtype=float)
    extent = prepared["target_extent_m"]
    radial_span = extent["r_max"] - extent["r_min"]
    vertical_span = extent["z_max"] - extent["z_min"]
    makegrid = vmecpp.MakegridParameters(
        normalize_by_currents=True,
        assume_stellarator_symmetry=True,
        number_of_field_periods=2,
        r_grid_minimum=extent["r_min"] - 0.4 * radial_span,
        r_grid_maximum=extent["r_max"] + 0.4 * radial_span,
        number_of_r_grid_points=args.mgrid_points,
        z_grid_minimum=extent["z_min"] - 0.4 * vertical_span,
        z_grid_maximum=extent["z_max"] + 0.4 * vertical_span,
        number_of_z_grid_points=args.mgrid_points,
        number_of_phi_grid_points=24,
    )
    response_started = time.perf_counter()
    response = vmecpp.MagneticFieldResponseTable.from_coils_file(
        prepared["coils_file"], makegrid
    )
    response_elapsed = time.perf_counter() - response_started

    fixed_output, fixed_elapsed = _run(fixed_input, threads=args.threads)
    free_output, free_elapsed = _run(
        free_input, threads=args.threads, magnetic_field=response
    )
    fixed_path = args.output_dir / "wout_fixed.nc"
    free_path = args.output_dir / "wout_free.nc"
    fixed_output.wout.save(fixed_path)
    free_output.wout.save(free_path)

    target_modes = _target_modes(fixed_input)
    free_modes = _wout_modes(free_output.wout)
    target_volume = _surface_volume(*target_modes)
    fixed_summary = _summary(fixed_output.wout, fixed_elapsed)
    free_summary = _summary(free_output.wout, free_elapsed)
    axis_fixed = _axis_curve(fixed_output.wout)
    axis_free = _axis_curve(free_output.wout)
    comparisons = {
        "target_volume_m3": target_volume,
        "free_vs_target_volume_relative_error": abs(free_summary["volume_m3"] - target_volume)
        / target_volume,
        "free_vs_fixed_volume_relative_error": abs(
            free_summary["volume_m3"] - fixed_summary["volume_m3"]
        )
        / abs(fixed_summary["volume_m3"]),
        "axis_r_rms_relative_to_fixed_mean_r": float(
            np.sqrt(np.mean((axis_free - axis_fixed) ** 2)) / np.mean(axis_fixed)
        ),
        "cross_sections": {},
    }
    for phi_fraction in (0.0, 0.25):
        target_section = _cross_section(*target_modes, phi_fraction)
        free_section = _cross_section(*free_modes, phi_fraction)
        area = 0.5 * abs(
            float(
                np.sum(
                    target_section[:, 0] * np.roll(target_section[:, 1], -1)
                    - target_section[:, 1] * np.roll(target_section[:, 0], -1)
                )
            )
        )
        minor_proxy = math.sqrt(area / np.pi)
        comparisons["cross_sections"][str(phi_fraction)] = {
            "symmetric_rms_distance_m": _symmetric_rms_distance(
                free_section, target_section
            ),
            "target_minor_radius_proxy_m": minor_proxy,
            "normalized_rms_distance": _symmetric_rms_distance(
                free_section, target_section
            )
            / minor_proxy,
        }

    acceptance = {
        "fixed_converged": fixed_summary["residual_converged"],
        "free_converged": free_summary["residual_converged"],
        "free_target_volume_within_0_05": comparisons[
            "free_vs_target_volume_relative_error"
        ]
        <= 0.05,
        "free_fixed_volume_within_0_05": comparisons[
            "free_vs_fixed_volume_relative_error"
        ]
        <= 0.05,
        "axis_r_rms_within_0_02": comparisons["axis_r_rms_relative_to_fixed_mean_r"]
        <= 0.02,
        "cross_section_rms_within_0_05": all(
            section["normalized_rms_distance"] <= 0.05
            for section in comparisons["cross_sections"].values()
        ),
    }
    evidence = {
        "schema_version": 1,
        "protocol": "docs/engineering/FREE_BOUNDARY_PROTOCOL.md",
        "vmecpp_version": version("vmecpp"),
        "vmecpp_source_commit": _git_head(Path("external/vmecpp")),
        "prepared_case": prepared,
        "prepared_case_sha256": _sha256(args.prepared_case),
        "vmec_input_sha256": _sha256(args.vmec_input),
        "response_grid": {
            "r_points": args.mgrid_points,
            "z_points": args.mgrid_points,
            "phi_points": 24,
            "margin_fraction": 0.4,
            "construction_elapsed_s": response_elapsed,
        },
        "fixed_boundary": fixed_summary,
        "free_boundary": free_summary,
        "comparisons": comparisons,
        "outputs": {
            "fixed_wout_sha256": _sha256(fixed_path),
            "free_wout_sha256": _sha256(free_path),
        },
        "acceptance": acceptance,
        "accepted": all(acceptance.values()),
        "optimization_writeback": False,
    }
    evidence_path = args.output_dir / "evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n")
    if args.evidence is not None:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))
    return 0 if evidence["accepted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
