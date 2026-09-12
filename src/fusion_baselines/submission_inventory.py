"""Conservative extraction of reported metadata, never physical admission."""

import math

KEYS = (
    "final_squared_flux",
    "final_normalized_squared_flux",
    "flux_threshold",
    "final_total_length",
    "final_max_curvature",
    "final_min_cc_separation",
    "final_min_cs_separation",
    "final_B_field",
    "target_B_field",
    "avg_BdotN_over_B",
    "final_current_per_coil",
    "final_length_per_coil",
    "total_current_after",
)


def number(value):
    return value if type(value) in (float, int) and math.isfinite(value) else None


def extract(document):
    metrics = document.get("metrics", document)
    if not isinstance(metrics, dict):
        raise ValueError("metrics object required")
    row = dict(
        schema="wrapped" if "metrics" in document else "flat",
        producer=document.get("version_info"),
        reported={key: metrics.get(key) for key in KEYS},
        order=metrics.get("final_order", metrics.get("fourier_order")),
        issues=[],
    )
    cached = metrics.get("_cached_thresholds", {})
    row["a0"] = cached.get("a0")
    row["cached_flux_threshold"] = cached.get("flux_threshold")
    currents = metrics.get("final_current_per_coil")
    row["base_coils"] = len(currents) if isinstance(currents, list) else None
    row["current_sum"] = (
        sum(currents)
        if (
            isinstance(currents, list) and currents and all(number(i) is not None for i in currents)
        )
        else None
    )
    if isinstance(currents, list) and row["current_sum"] is None:
        row["issues"].append("invalid_current_list")
    lengths = metrics.get("final_length_per_coil")
    if isinstance(lengths, list) and len(lengths) != row["base_coils"]:
        row["issues"].append("length_current_count_mismatch")
    if metrics.get("fourier_continuation"):
        stages = metrics.get("continuation_results", [])
        if not stages or stages[-1].get("fourier_order") != row["order"]:
            row["issues"].append("ambiguous_continuation_endpoint")
        elif any(
            key in stages[-1] and key in metrics and stages[-1][key] != metrics[key] for key in KEYS
        ):
            row["issues"].append("continuation_endpoint_disagrees")
    row["reported_zero_flux"] = metrics.get("final_squared_flux") == 0
    row["raw_flux_verified"] = False
    return row


def screen(row):
    values = row["reported"]
    scale = number(row["a0"])
    scales_ok = scale is not None and scale > 0

    def scaled_limit(key, limit, *, lower=False, curvature=False):
        value = number(values[key])
        if not scales_ok or value is None or value < 0:
            return False
        result = value / scale if curvature else value * scale
        return result >= limit if lower else result <= limit

    mean_b, norm_error = number(values["final_B_field"]), number(values["avg_BdotN_over_B"])
    return dict(
        four_coils=row["base_coils"] == 4,
        order_eight=row["order"] == 8,
        no_issues=not row["issues"],
        endpoint_field_available=bool(row.get("endpoint_field")),
        field_strength=bool(
            number(values["target_B_field"]) == 1.0 and mean_b is not None and 0.9 <= mean_b <= 1.1
        ),
        length=scaled_limit("final_total_length", 220),
        curvature=scaled_limit("final_max_curvature", 1, curvature=True),
        coil_clearance=scaled_limit("final_min_cc_separation", 1.06, lower=True),
        plasma_clearance=scaled_limit("final_min_cs_separation", 1.3, lower=True),
        ranking_value=norm_error is not None and norm_error >= 0,
    )


def shortlist(rows):
    eligible = [row for row in rows if "checks" in row and all(row["checks"].values())]
    return [
        row["source"]["path"]
        for row in sorted(
            eligible, key=lambda row: (row["reported"]["avg_BdotN_over_B"], row["source"]["path"])
        )[:5]
    ]
