"""Synthetic low-mode startup checks, not field/gradient physical verification."""

import copy
import math

import numpy as np
import pytest

from fusion_baselines.protected_startup import derivative_screen, exact_bundle_replay, points


def scalar_directions(n, order):
    width = 2 * order + 1
    modes = [((k % width) + 1) // 2 for k in range(n * 3 * width)]
    result = []
    for function in (math.sin, math.cos):
        vector = [function(k + 1) / (1 + m*m) if m <= 2 else 0.
                  for k, m in enumerate(modes)]
        norm = math.sqrt(sum(v*v for v in vector))
        result.append([v / norm for v in vector])
    return modes, result


def fixture(n=6, order=5):
    seed = np.zeros(n * 3 * (2 * order + 1))
    seed[0] = .25
    seed[5] = -0.
    gradient = np.sin(np.arange(len(seed)) + 1)
    rows = [dict(x=x.tolist(), value=float(gradient @ x), gradient=gradient.tolist(),
                 metrics={"current": 100000.}) for x in points(seed, n, order)]
    return seed, rows


@pytest.mark.parametrize("n,order", [(6, 5), (8, 7)])
def test_full_index_directions_and_inactive_bits(n, order):
    seed, rows = fixture(n, order)
    modes, vectors = scalar_directions(n, order)
    assert len(rows) == 10
    for k, direction in enumerate(vectors):
        for j, step in enumerate((1e-5, 5e-6)):
            for sign_index, sign in enumerate((1, -1)):
                actual = np.array(rows[1 + 4*k + 2*j + sign_index]["x"])
                for i, m in enumerate(modes):
                    if m > 2:
                        assert actual[i].tobytes() == seed[i].tobytes()
                    else:
                        assert abs(actual[i] - (seed[i] + sign*step*direction[i])) < 1e-20
    result = derivative_screen(seed, n, order, rows, [r["value"] for r in rows])
    assert result["startup_screen_pass"] and len(result["checks"]) == 8
    assert not result["physical_admission"] and not result["raw_arrays_replayed"]


def test_recorded_only_is_not_independent_values():
    seed, rows = fixture()
    report = derivative_screen(seed, 6, 5, rows)
    assert report["startup_screen_pass"] and len(report["checks"]) == 4
    assert not report["independently_supplied_values"]


def test_unrepresentable_probe_displacements_fail_closed():
    seed = np.full(198, 1e30)
    rows = [dict(x=x.tolist(), value=0., gradient=np.zeros(198).tolist(),
                 metrics={"current": 1.}) for x in points(seed, 6, 5)]
    with pytest.raises(ValueError, match="representable"):
        derivative_screen(seed, 6, 5, rows, [0.] * 10)


def test_independent_seed_repeat_must_also_be_exact():
    seed, rows = fixture()
    own = [r["value"] for r in rows]
    own[-1] += 1e-11
    report = derivative_screen(seed, 6, 5, rows, own)
    assert not report["startup_screen_pass"]
    assert report["exact_independent_value_repeat"] is False


@pytest.mark.parametrize("fault", ["old-directions", "wrong-x", "nan", "missing", "bool",
                                   "independent-size", "independent-value"])
def test_malformed_startup_fails_closed(fault):
    seed, rows = fixture()
    independent = [r["value"] for r in rows]
    if fault == "old-directions":
        direction = np.sin(np.arange(len(seed)) + 1)
        rows[1]["x"] = (seed + 1e-5 * direction / np.linalg.norm(direction)).tolist()
    elif fault == "wrong-x":
        rows[1]["x"][0] += 1e-10
    elif fault == "nan":
        rows[0]["gradient"][5] = float("nan")
    elif fault == "missing":
        rows.pop()
    elif fault == "bool":
        rows[0]["value"] = True
    elif fault == "independent-size":
        independent.pop()
    else:
        independent[0] += .1
    with pytest.raises(ValueError):
        derivative_screen(seed, 6, 5, rows, independent)


def test_numerical_failure_is_a_negative_screen_not_raised_or_accepted():
    seed, rows = fixture()
    rows[0]["gradient"] = rows[-1]["gradient"] = np.zeros(len(seed)).tolist()
    result = derivative_screen(seed, 6, 5, rows)
    assert not result["startup_screen_pass"]
    assert not result["derivative_pass"] and result["exact_state_repeat"]


@pytest.mark.parametrize("part", ["value", "gradient", "metrics"])
def test_repeat_is_exact(part):
    seed, rows = fixture()
    if part == "value":
        rows[-1][part] = np.nextafter(rows[-1][part], np.inf).item()
    elif part == "gradient":
        rows[-1][part][0] = np.nextafter(rows[-1][part][0], np.inf).item()
    else:
        rows[-1][part]["current"] += 1e-10
    result = derivative_screen(seed, 6, 5, rows)
    assert not result["exact_state_repeat"] and not result["startup_screen_pass"]


def bundle():
    return dict(state={"x": [-0., 1.], "value": .5}, snapshot={"name": "seed"},
                arrays={"B": np.arange(6.).reshape(2, 3)})


def test_exact_numerical_replay_does_not_claim_whole_search():
    result = exact_bundle_replay(copy.deepcopy(bundle()), bundle())
    assert result["exact_bundle_replay"] and not result["whole_search_repeated"]
    assert not result["physical_admission"]
    assert result["bundle_schema_verified"] is False


@pytest.mark.parametrize("fault", ["state", "snapshot", "array", "dtype", "shape", "keys",
                                   "signed-zero", "nan", "missing"])
def test_replay_rejects_every_component_mutation(fault):
    original, actual = bundle(), bundle()
    if fault in ("state", "snapshot"):
        actual[fault]["changed"] = True
    elif fault == "array":
        actual["arrays"]["B"][0, 0] = np.nextafter(0., 1.)
    elif fault == "dtype":
        actual["arrays"]["B"] = actual["arrays"]["B"].astype("f4")
    elif fault == "shape":
        actual["arrays"]["B"] = actual["arrays"]["B"].ravel()
    elif fault == "keys":
        actual["arrays"]["extra"] = np.zeros(1)
    elif fault == "signed-zero":
        actual["state"]["x"][0] = 0.
    elif fault == "nan":
        actual["arrays"]["B"][0, 0] = np.nan
    else:
        actual.pop("state")
    with pytest.raises(ValueError):
        exact_bundle_replay(actual, original)
