"""Additive first-ranked source preparation; old warm-start preparation is untouched."""

import contextlib
import json
import time

import numpy as np
from qualify_optimization_oracle import CapturedContext
from run_jac_scaled_study import require_committed
from run_natural_auglag_jac import checked, reference
from simsopt.field import Current, coils_via_symmetries
from simsopt.geo import CurveXYZFourier, SurfaceRZFourier
from stellcoilbench.case_loader import load_case
from stellcoilbench.coil_optimization import _optimization_loop as loop

from fusion_baselines.current_normalization import (
    CANONICAL_TOTAL,
    fixed_serialized_total,
    normalize_currents,
)
from fusion_baselines.provenance import sha256_file
from fusion_baselines.refined_curvature import make_refined_penalty
from fusion_baselines.serialized_field_state import serialized_state

SOURCE_SHA = "40c3abd2c172fdfc94be6a2b5de05ef2e29c3f37c8b4fbd04c6fdb47eef69b4a"


def prepare(root, raw):
    started = time.monotonic()
    prior_path = root / "evidence/upstream-lpqa-reconstruction-v1.json"
    audit_path = root / "evidence/upstream-lpqa-reconstruction-v1-audit.json"
    prior, audit = json.loads(prior_path.read_text()), json.loads(audit_path.read_text())
    if audit["all_pass"] is not True or audit["source"] != reference(prior_path):
        raise ValueError("passing bound reconstruction audit required")
    for path in (prior_path, audit_path, root / "docs/optimization/UPSTREAM_START_PROTOCOL.md"):
        require_committed(root, path)
    candidate = prior["candidates"][0]
    source = checked(candidate["source_field"])
    if sha256_file(source) != SOURCE_SHA:
        raise ValueError("only the preregistered first-ranked source is allowed")
    old = root / "fixtures/rejected-lpqa-warmstart/field.json"
    canonical = fixed_serialized_total(json.loads(old.read_text()))
    if canonical != CANONICAL_TOTAL:
        raise ValueError("old canonical fixed total changed")
    state = serialized_state(json.loads(source.read_text()))
    normalized, factor = normalize_currents(state["currents"][:4])
    curves = []
    for coefficients in state["coefficients"]:
        curve = CurveXYZFourier(200, 8)
        curve.local_full_x = coefficients.copy()
        curves.append(curve)
    currents = [Current(float(value) / 1e7) * 1e7 for value in normalized[:3]]
    total = Current(CANONICAL_TOTAL)
    total.fix_all()
    currents.append(total - sum(currents))
    coils = coils_via_symmetries(
        curves, currents, 2, True, regularizations=state["base_regularizations"].tolist()
    )
    previous = json.loads((root / "evidence/natural-auglag-jac-v1/summary.json").read_text())
    surface_path = checked(previous["preparation"]["surface"])
    surface = SurfaceRZFourier.from_vmec_input(
        str(surface_path), range="half period", nphi=32, ntheta=32
    )
    case = checked(previous["preparation"]["case"])
    terms = dict(load_case(case).coil_objective_terms)
    terms.update(length_threshold=219.9, flux_threshold=8e-9)
    original = loop._run_optimization_step

    def capture(ctx):
        raise CapturedContext(ctx)

    loop._run_optimization_step = capture
    try:
        with (raw / "preparation.log").open("x") as stream, contextlib.redirect_stdout(stream):
            try:
                loop._optimize_coils_loop_impl(
                    surface, out_dir=raw / "setup", ncoils=4, order=8,
                    initial_coils=coils, coil_objective_terms=terms, algorithm="L-BFGS-B",
                    verbose=False, save_coils_surface_vtk=False, save_initial_state=False,
                    **{key: value for key, value in terms.items() if key.endswith("_threshold")},
                )
            except CapturedContext as caught:
                ctx = caught.context
            else:
                raise RuntimeError("optimizer context capture did not execute")
    finally:
        loop._run_optimization_step = original
    index = next(i for i, term in ctx.constraint_idx_to_term.items() if term == "coil_curvature")
    ctx.c_list[index] = make_refined_penalty(curves, 0.99 * ctx.th["curvature_threshold"])
    guard = dict(
        component_index=index, curvature_resolution=1600, curvature_target_reactor=0.99,
        length_target_reactor=219.9, flux_target=8e-9, field_quadrature_unchanged=200,
    )
    if ctx.th != previous["preparation"]["thresholds"] or guard != previous["preparation"][
        "guarded_search_targets"
    ]:
        raise ValueError("canonical physical thresholds or construction guards changed")
    field_path = raw / "normalized_start.json"
    ctx.Jf.field.save(str(field_path))
    reconstructed = serialized_state(json.loads(field_path.read_text()))
    actual = np.array([c.current.get_value() for c in ctx.Jf.field.coils])
    error = float(np.max(np.abs(actual - factor * state["currents"]) /
                         np.maximum(1, np.abs(factor * state["currents"]))))
    checks = dict(
        coefficients=np.array_equal(reconstructed["coefficients"], state["coefficients"]),
        regularizations=np.array_equal(
            reconstructed["base_regularizations"], state["base_regularizations"]),
        all_currents=error <= 1e-12,
        serialized_currents=np.array_equal(reconstructed["currents"], actual),
        fixed_total=fixed_serialized_total(json.loads(field_path.read_text())) == canonical,
        parameter_count=len(ctx.Jf.x) == 207,
    )
    prep = dict(
        source=reference(source), reconstruction=reference(prior_path),
        reconstruction_audit=reference(audit_path), canonical_fixture=reference(old),
        source_currents=state["currents"][:4].tolist(), current_factor=factor,
        canonical_total=canonical, physical_currents=actual.tolist(),
        normalization_error=error, identity_checks={k: bool(v) for k, v in checks.items()},
        normalized_start=reference(field_path), surface=reference(surface_path),
        case=reference(case), thresholds=ctx.th, guarded_search_targets=guard,
        degrees_of_freedom=list(ctx.Jf.dof_names), source_field_probe=candidate[
            "independent_fields"][0]["arrays"],
        shared_preparation_seconds=time.monotonic() - started,
        preparation_is_shared_and_outside_per_arm_budget=True,
    )
    if not all(checks.values()):
        raise ValueError(f"normalized source identity failed: {checks}")
    return ctx, prep
