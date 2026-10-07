"""Opt-in dense target-surface diagnostic; no native intake or acceptance changes."""

import math
import time

from .data import ROOT, canonical, loads, require, sha, validate_candidate, vector
from .dense import flux_loop
from .field import field, physical_curves
from .interior import vector_rms

PACKET_DIR = ROOT / "examples/clear-coil-interior-v1"
TARGETS = ("reference401", "selected401")
MANIFEST_SHA = "9f9b32ffb6176b22e149069896500da0ac1aa0c371b5f17be7fa7603ebfb2ccb"


def load_target(target_id, directory=PACKET_DIR):
    require(target_id in TARGETS, "Explicit registered target required")
    raw = (directory / "manifest.json").read_bytes()
    require(sha(raw) == MANIFEST_SHA, "Interior packet manifest identity changed")
    manifest = loads(raw)
    path = directory / f"{target_id}.json"
    require(path.stat().st_size <= 2 * 1024**2, "Bounded target packet required")
    raw = path.read_bytes()
    digest = sha(raw)
    require(digest == manifest["files"][path.name], "Interior packet identity changed")
    packet = loads(raw)
    require(packet["target_id"] == target_id, "Target mismatch")
    rows = packet["samples_xyz_B"]
    require(len(rows) == 12288, "Three 64 by 64 target surfaces required")
    for row in rows:
        vector(row, 6)
    require(abs(sum(sum(x*x for x in row[3:]) for row in rows) / len(rows)
                / packet["B2_scale_T2"] - 1) < 1e-12, "Frozen target B2 mismatch")
    return packet, digest


def signed_scale(measured_flux, target_flux):
    require(math.isfinite(measured_flux) and abs(measured_flux) > 1e-15,
            "Finite nonzero loop flux required")
    require(measured_flux * target_flux > 0, "Loop flux has the wrong sign")
    scale = target_flux / measured_flux
    require(math.isfinite(scale) and scale > 0, "Finite positive current scale required")
    return scale


def evaluate_dense(candidate, case, target_id, seconds=600, check_resources=None):
    """Return report and computed B, with current normalization frozen before fine fields.

    The second return value supports full-array qualification; the CLI emits only
    the compact report. Elapsed time is a resource receipt, not a timing benchmark.
    """
    require(type(seconds) is int and 1 <= seconds <= 600, "Budget must be 1..600 seconds")
    start, wall = time.monotonic(), time.time()

    def guard():
        elapsed, elapsed_wall = time.monotonic() - start, time.time() - wall
        require(max(elapsed, elapsed_wall) <= seconds, "Dense interior time budget exhausted")
        require(abs(elapsed - elapsed_wall) <= 5, "Clock discrepancy exceeds 5 seconds")
        if check_resources is not None:
            check_resources()

    validate_candidate(candidate)
    packet, packet_sha = load_target(target_id)
    points, tangents = flux_loop(packet["boundary"], 256)
    potential = field(points, physical_curves(candidate, case, 256))["A_Tm"]
    measured = sum(sum(a*t for a, t in zip(av, tv, strict=True))
                   for av, tv in zip(potential, tangents, strict=True)) / 256
    scale = signed_scale(measured, packet["signed_target_flux_Wb"])
    guard()
    coils = [(nodes, current * scale) for nodes, current in physical_curves(candidate, case, 512)]
    rows, magnetic = packet["samples_xyz_B"], []
    for offset in range(0, len(rows), 128):
        guard()
        magnetic.extend(field([row[:3] for row in rows[offset:offset+128]], coils)["B_T"])
    target = [row[3:] for row in rows]
    b2 = packet["B2_scale_T2"]
    rms = vector_rms(magnetic, target, b2)
    report = dict(
        schema_version=1, diagnostic="dense-interior-target-surfaces", completed=True,
        target_id=target_id, packet_id=packet["packet_id"], packet_sha256=packet_sha,
        candidate_sha256=sha(canonical(candidate)), case_sha256=sha(canonical(case)),
        source_sha256={
            name: sha((ROOT / "src/fusion_public" / name).read_bytes())
            for name in ("dense_interior.py", "dense.py", "field.py", "data.py", "interior.py")
        },
        B2_scale_T2=b2, signed_target_flux_Wb=packet["signed_target_flux_Wb"],
        measured_unscaled_flux_Wb=measured, flux_scale=scale,
        flux_normalized_max_abs_current_A=max(abs(current) for _, current in coils),
        inner_points=len(rows), surface_s=packet["grid"]["s"],
        flux_loop_points=256, flux_coil_nodes=256, field_coil_nodes=512,
        dense_inner_vector_rms=rms,
        surface_vector_rms=[vector_rms(magnetic[i:i+4096], target[i:i+4096], b2)
                            for i in (0, 4096, 8192)],
        interior_limit=0.01, interior_metric_below_limit=rms <= 0.01,
        quadrature_convergence_checked=False, physical_admission=False, step4_pass=False,
        interpretation="Equal-weight samples on three target surfaces, not a volume integral, "
        "realized-flux comparison, confinement or physical acceptance. Current ratios are "
        "preserved; the signed 256-node normalization is frozen before the 512-node field.",
        elapsed_seconds=time.monotonic() - start,
    )
    guard()
    return report, magnetic
