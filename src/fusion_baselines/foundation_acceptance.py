"""Independent report arithmetic and fail-closed bounded-foundation contracts.

No new field calls: qualification of the underlying physics is supplied separately.
Process completion never substitutes for the recomputed physical classifications.
"""

import math
from xml.etree import ElementTree

import numpy as np

UNSUPPORTED = (
    "global_qi",
    "finite_particle_orbits",
    "full_engineering",
    "squid_c",
    "sota_advance",
    "independent_hardware",
    "hosted_ci",
    "native_abi_certified",
)


def audit_test_xml(path):
    tree = ElementTree.parse(path).getroot()
    cases = list(tree.iter("testcase"))
    keys = [(c.get("classname"), c.get("name")) for c in cases]
    checks = dict(
        full_suite=len(cases) >= 700,
        unique=len(keys) == len(set(keys)),
        no_skips=not list(tree.iter("skipped")),
        no_failures=not list(tree.iter("failure")),
        no_errors=not list(tree.iter("error")),
    )
    return dict(test_count=len(cases), checks=checks, all_pass=all(checks.values()))


def finite_numbers(value):
    if isinstance(value, dict):
        return all(finite_numbers(v) for v in value.values())
    if isinstance(value, list):
        return all(finite_numbers(v) for v in value)
    return not isinstance(value, (int, float)) or math.isfinite(value)


def audit_candidate(holdout, curvature, clearance, native, field, scale, thresholds):
    """Recompute all reported acceptance flags, keeping rejection a valid outcome."""
    h, k, c, n = holdout, curvature, clearance, native
    checks = dict(
        source=all(row["field"] == field for row in (h, k, c, n)),
        scale=h["a0"] == k["a0"] == c["a0"] == scale,
        finite=all(finite_numbers(row) for row in (h, k, c, n)),
        no_engineering=h["full_engineering_admission_pass"] is False
        and c["actual_mesh_enclosure_or_self_intersection_certified"] is False,
        flux_levels=[(r["surface_resolution"], r["coil_quadrature"]) for r in h["flux"]]
        == [(32, 200), (64, 200), (128, 200), (128, 800)],
        geometry_levels=set(h["geometry"]) == {"200", "1000", "5000", "20000"},
        coil_levels=set(h["coil_coil"]) == {"200", "1000", "5000", "20000"},
        plasma_levels=set(h["coil_plasma"]) == {"64", "128", "256", "512"},
        native_levels=[r["resolution"] for r in n["levels"]] == [200, 800, 3200],
        curvature_levels=[r["resolution"] for r in k["levels"]]
        == [200, 400, 800, 1600, 3200, 6400, 12800],
        physical_copies=k["orthogonal_copies_verified"] is True,
    )
    if not all(checks.values()):
        return dict(checks=checks, all_pass=False, bounded_candidate_pass=False)
    flux = [r["unthresholded_quadratic_flux"] for r in h["flux"]]
    flags = dict(
        flux_cut_in=flux[-1] <= 1e-8,
        surface_flux_refinement=abs(flux[2] - flux[1]) <= max(1e-10, 0.01 * flux[1]),
        coil_flux_refinement=abs(flux[3] - flux[2]) <= max(1e-10, 0.01 * flux[2]),
        length=h["geometry"]["20000"]["unique_total_length_reactor_m"] <= 220,
        curvature=h["geometry"]["20000"]["maximum_curvature_reactor_inverse_m"] <= 1,
        coil_coil_clearance=h["coil_coil"]["20000"]["centerline_distance_reactor_m"] >= 1.06,
        coil_plasma_clearance=h["coil_plasma"]["512"] >= 1.3,
    )
    checks["holdout_classification"] = h["checks"] == flags and (
        h["bounded_geometry_flux_screen_pass"] is all(flags.values())
    )
    checks["positive_physical_values"] = all(f >= 0 for f in flux) and all(
        r["mean_B_magnitude_T"] > 0 for r in h["flux"]
    )
    native_flags = {}
    for metric, threshold in (
        ("msc", "msc_threshold"),
        ("arclength_variation", "arclength_variation_threshold"),
    ):
        values = np.asarray([r[metric] for r in n["levels"]])
        checks[metric + "_shape"] = values.shape == (3, 4)
        native_flags[metric + "_finite"] = bool(np.isfinite(values).all())
        native_flags[metric + "_all_levels_pass"] = bool(np.all(values <= thresholds[threshold]))
        native_flags[metric + "_refinement"] = bool(
            np.max(abs(values[-1] - values[-2]) / np.maximum(1, abs(values[-1]))) <= 1e-6
        )
    native_flags["linking_zero_all_levels"] = all(r["linking_number"] == 0 for r in n["levels"][:2])
    checks["native_classification"] = n["checks"] == native_flags and (
        n["pass"] is all(native_flags.values())
    )
    classifications = []
    for level in k["levels"]:
        classes = []
        checks[f"curves_{level['resolution']}"] = len(level["curves"]) == 4
        for curve in level["curves"]:
            lower, upper = curve["maximum_lower_bound"], curve["maximum_upper_bound"]
            kind = "unresolved"
            if lower is not None and lower > scale:
                kind = "fail"
            elif curve["regularity_resolved"] and upper is not None and upper <= scale:
                kind = "pass"
            classes.append(kind)
            checks[f"curve_{level['resolution']}_{len(classes)}"] = (
                curve["classification"] == kind
                and curve["resolution"] == level["resolution"]
                and all(
                    curve[key + "_reactor"] == (None if curve[key] is None else curve[key] / scale)
                    for key in ("maximum_lower_bound", "maximum_upper_bound")
                )
            )
        kind = (
            "fail"
            if "fail" in classes
            else ("pass" if all(s == "pass" for s in classes) else "unresolved")
        )
        checks[f"curvature_classification_{level['resolution']}"] = level["classification"] == kind
        classifications.append(kind)
    checks["curvature_final"] = k["classification"] == classifications[-1]
    # Independently evaluate the squared-distance interpolation allowance.
    speed, accel, separation = (
        c[key]
        for key in ("global_speed_bound", "global_acceleration_bound", "global_separation_bound")
    )
    sampled = h["coil_coil"]["20000"]["centerline_distance_reactor_m"] / scale
    allowance = (speed * speed + separation * accel) / (2 * 20000**2)
    lower = math.sqrt(max(0, sampled * sampled - allowance))
    checks["clearance_arithmetic"] = (
        c["sampled_minimum_device_m"] == sampled
        and math.isclose(c["squared_distance_interpolation_error_bound"], allowance, rel_tol=1e-12)
        and math.isclose(c["continuous_distance_lower_bound"], lower, rel_tol=1e-12, abs_tol=1e-14)
        and c["continuous_centerline_lower_bound_reactor_m"]
        == c["continuous_distance_lower_bound"] * scale
    )
    clearance_pass = c["continuous_centerline_lower_bound_reactor_m"] >= 1.06
    checks["clearance_classification"] = c["centerline_requirement_pass"] is clearance_pass
    return dict(
        checks={key: bool(value) for key, value in checks.items()},
        all_pass=all(checks.values()),
        raw_fine_flux=flux[-1],
        flux_limit=1e-8,
        bounded_candidate_pass=all(flags.values())
        and all(native_flags.values())
        and classifications[-1] == "pass"
        and clearance_pass,
    )


def assess(step1, step2, capabilities):
    """Exact required gates; empty/partial dictionaries and extra claims cannot pass."""
    expected1 = {
        "regression",
        "scientific",
        "warning",
        "preserved_native",
        "source_and_derivatives",
        "holdout_audit",
        "preservation",
        "checks",
    }
    expected2 = {"cycle", "holdout_audit", "provenance"}
    scope = set(capabilities) == set(UNSUPPORTED) and all(v is False for v in capabilities.values())
    first = scope and set(step1) == expected1 and all(v is True for v in step1.values())
    second = scope and set(step2) == expected2 and all(v is True for v in step2.values())
    return dict(
        step1_pass=first,
        step2_pass=second,
        all_pass=first and second,
        unsupported_capabilities=capabilities,
    )
