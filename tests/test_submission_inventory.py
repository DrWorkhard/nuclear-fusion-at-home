from copy import deepcopy

import pytest

from fusion_baselines.submission_inventory import extract, screen, shortlist


def data():
    return dict(
        final_order=8,
        final_squared_flux=0.0,
        flux_threshold=1e-3,
        _cached_thresholds=dict(a0=10.0, flux_threshold=1e-3),
        final_current_per_coil=[1.0] * 4,
        final_length_per_coil=[5.0] * 4,
        final_total_length=20.0,
        final_max_curvature=5.0,
        final_min_cc_separation=0.11,
        final_min_cs_separation=0.2,
        final_B_field=1.0,
        target_B_field=1.0,
        avg_BdotN_over_B=0.001,
    )


@pytest.mark.parametrize("wrapped", [False, True])
def test_flat_and_wrapped_metadata_not_admitted(wrapped):
    original = data()
    row = extract(dict(metrics=original) if wrapped else original)
    row["endpoint_field"] = "placeholder"
    assert all(screen(row).values())
    assert row["reported_zero_flux"] and not row["raw_flux_verified"]


@pytest.mark.parametrize(
    "key",
    [
        "_cached_thresholds",
        "final_current_per_coil",
        "final_order",
        "target_B_field",
        "avg_BdotN_over_B",
    ],
)
def test_missing_value_never_counts_as_pass(key):
    original = data()
    del original[key]
    row = extract(original)
    row["endpoint_field"] = "placeholder"
    assert not all(screen(row).values())


def test_continuation_uses_explicit_end_without_early_substitution():
    original = data()
    final = deepcopy(original)
    final["fourier_order"] = 8
    original.update(
        fourier_continuation=True,
        continuation_results=[dict(fourier_order=4, final_squared_flux=1.0), final],
    )
    assert not extract(original)["issues"]
    original["continuation_results"].reverse()
    assert "ambiguous_continuation_endpoint" in extract(original)["issues"]


def test_inconsistent_final_metrics_rejected():
    original = data()
    original.update(
        fourier_continuation=True,
        continuation_results=[dict(fourier_order=8, final_squared_flux=1.0)],
    )
    assert "continuation_endpoint_disagrees" in extract(original)["issues"]


@pytest.mark.parametrize("count", [3, 5])
def test_wrong_coil_count_rejected(count):
    original = data()
    original["final_current_per_coil"] = [1.0] * count
    assert not screen(extract(original))["four_coils"]


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True, "0.001", -1.0])
def test_invalid_ranking_value_rejected(value):
    original = data()
    original["avg_BdotN_over_B"] = value
    assert not screen(extract(original))["ranking_value"]


def test_stable_five_item_selection_and_rejection():
    rows = []
    for i in range(8):
        row = extract(data())
        row["source"] = {"path": str(i)}
        row["endpoint_field"] = "placeholder"
        row["checks"] = screen(row)
        rows.append(row)
    rows[0]["checks"]["length"] = False
    assert shortlist(rows[::-1]) == [str(i) for i in range(1, 6)]
