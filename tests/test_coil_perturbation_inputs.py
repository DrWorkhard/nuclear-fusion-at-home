"""Source admission controls; no new geometric or magnetic evaluations."""

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import coil_perturbation_inputs as binder  # noqa: E402


def fixture():
    source = dict(matrix=binder.previous.physical_cases(), repository=dict(commit="old"))
    false = dict(
        physical_seed_pass=False, search_allowed=False, transfer_pass=False, step4_pass=False
    )
    scope = dict(equilibrium_solves=0, search_calls=0)
    cells = []
    for case in source["matrix"]:
        cells.append(
            dict(
                case=case,
                status="completed",
                arithmetic_and_source_pass=True,
                startup_pass=True,
                **false,
                **scope,
                checks=dict(
                    startup=True,
                    normal_rms=False,
                    normal_max=False,
                    vector_rms=False,
                    current=True,
                    lengths=True,
                    curvature=True,
                    coil_distance=True,
                    plasma_distance=True,
                ),
                work=dict(
                    passed=True,
                    events=524,
                    work=dict(
                        native_requests=262,
                        completed_requests=262,
                        values=202,
                        vjps=60,
                        initialization_requests=10,
                        full_bundles=20,
                        equilibrium_solves=0,
                        search_calls=0,
                    ),
                ),
                qualification={
                    m: dict(
                        passed=True,
                        rows=[{} for _ in range(10)],
                        derivatives=dict(
                            passed=True,
                            exact_repeat=True,
                            checks=[dict(passed=True) for _ in range(8)],
                        ),
                    )
                    for m in ("N", "V")
                },
                identity=dict(passed=True),
                diagnostics=[dict(status="completed") for _ in range(6)],
                refinement=dict(passed=True, checks=[dict(passed=True) for _ in range(5)]),
                flux=[
                    dict(
                        ncoil=n,
                        passed=True,
                        grids=[{} for _ in range(9)],
                        values=[0.1] * 9,
                        checks=[dict(passed=True) for _ in range(27)],
                    )
                    for n in (256, 512)
                ],
                flux_coil_comparison=dict(
                    passed=True, checks=[dict(passed=True) for _ in range(9)]
                ),
                direct_point_reconstructions=96,
                direct_field_comparisons=192,
            )
        )
    audit = dict(
        status="completed",
        all_pass=True,
        arithmetic_and_source_pass=True,
        independent_audit_pass=True,
        startup_pass=True,
        **false,
        **scope,
        source=copy.deepcopy(source),
        cells=cells,
    )
    run = dict(
        status="completed",
        kind="clear-coil-field-start",
        producer_complete=True,
        source_unchanged=True,
        admission_status="pending-independent-audit",
        all_pass=False,
        startup_pass=False,
        independent_audit_pass=False,
        **false,
        **scope,
        source_before=copy.deepcopy(source),
        source_after=copy.deepcopy(source),
        matrix=copy.deepcopy(source["matrix"]),
        rows=[{} for _ in range(4)],
    )
    current = copy.deepcopy(source)
    current["repository"] = dict(commit="later", dirty=True)
    return audit, run, current


def test_complete_numerical_positive_physically_negative_source():
    documents = fixture()
    before = copy.deepcopy(documents)
    binder.startup_gate(*documents)
    assert documents == before
    assert binder.matrix() == [
        dict(label="n6-shape-d100mm", nbase=6, order=5, geometry_report_index=3),
        dict(label="n8-shape-d100mm", nbase=8, order=7, geometry_report_index=9),
    ]


@pytest.mark.parametrize(
    "key",
    [
        "all_pass",
        "arithmetic_and_source_pass",
        "independent_audit_pass",
        "startup_pass",
        "physical_seed_pass",
        "search_allowed",
        "transfer_pass",
        "step4_pass",
    ],
)
def test_overall_startup_cannot_be_relabelled(key):
    audit, run, current = fixture()
    audit[key] = not audit[key]
    with pytest.raises(ValueError):
        binder.startup_gate(audit, run, current)


@pytest.mark.parametrize(
    "key", ["all_pass", "startup_pass", "independent_audit_pass", "search_allowed"]
)
def test_producer_cannot_issue_admission(key):
    audit, run, current = fixture()
    run[key] = True
    with pytest.raises(ValueError):
        binder.startup_gate(audit, run, current)


@pytest.mark.parametrize(
    "mutation",
    [
        "cell_missing",
        "wrong_case",
        "physical_relabelled",
        "normal_gate",
        "geometry_gate",
        "events_bool",
        "native_counter",
        "qualification_missing",
        "fd_false",
        "fd_omitted",
        "repeat",
        "diagnostic_missing",
        "diagnostic_status",
        "refinement_false",
        "identity",
        "flux_grid_missing",
        "flux_check_false",
        "flux_ncoil",
        "coil_flux_false",
        "direct_counter",
    ],
)
def test_all_original_individual_checks_required(mutation):
    audit, run, current = fixture()
    cell = audit["cells"][0]
    if mutation == "cell_missing":
        audit["cells"].pop()
    elif mutation == "wrong_case":
        cell["case"]["label"] = "different"
    elif mutation == "physical_relabelled":
        cell["physical_seed_pass"] = True
    elif mutation == "normal_gate":
        cell["checks"]["normal_rms"] = True
    elif mutation == "geometry_gate":
        cell["checks"]["plasma_distance"] = False
    elif mutation == "events_bool":
        cell["work"]["events"] = True
    elif mutation == "native_counter":
        cell["work"]["work"]["values"] -= 1
    elif mutation == "qualification_missing":
        cell["qualification"].pop("V")
    elif mutation == "fd_false":
        cell["qualification"]["N"]["derivatives"]["checks"][0]["passed"] = False
    elif mutation == "fd_omitted":
        cell["qualification"]["V"]["derivatives"]["checks"].pop()
    elif mutation == "repeat":
        cell["qualification"]["N"]["derivatives"]["exact_repeat"] = False
    elif mutation == "diagnostic_missing":
        cell["diagnostics"].pop()
    elif mutation == "diagnostic_status":
        cell["diagnostics"][0]["status"] = "running"
    elif mutation == "refinement_false":
        cell["refinement"]["checks"][0]["passed"] = False
    elif mutation == "identity":
        cell["identity"]["passed"] = False
    elif mutation == "flux_grid_missing":
        cell["flux"][0]["grids"].pop()
    elif mutation == "flux_check_false":
        cell["flux"][1]["checks"][0]["passed"] = False
    elif mutation == "flux_ncoil":
        cell["flux"][1]["ncoil"] = 256
    elif mutation == "coil_flux_false":
        cell["flux_coil_comparison"]["checks"][0]["passed"] = False
    elif mutation == "direct_counter":
        cell["direct_field_comparisons"] = 96
    with pytest.raises(ValueError):
        binder.startup_gate(audit, run, current)


@pytest.mark.parametrize("where", ["current", "before", "after"])
def test_only_later_root_metadata_can_differ(where):
    audit, run, current = fixture()
    target = current if where == "current" else run[f"source_{where}"]
    target["new_unbound_source"] = "changed"
    with pytest.raises(ValueError):
        binder.startup_gate(audit, run, current)


def test_actual_prerequisites_are_hash_pinned_without_candidate_math():
    assert (
        binder.STARTUP_AUDIT_HASH
        == "e6fa7cda853cc2576f9660501043fc6f8c0d7121c1ce0a819df47544fd262fd8"
    )
    assert (
        binder.STARTUP_RUN_HASH
        == "e4949a9be9518c9acaa727c3f6de238703028e9baca16bf89ec15bb145cb9714"
    )
    assert binder.STARTUP_REVISION == "3334f1e"
    assert all(
        value is False
        for key, value in binder.SCOPE.items()
        if key.endswith("pass") or key == "search_allowed"
    )
    assert all(
        type(value) is int and value == 0
        for key, value in binder.SCOPE.items()
        if key.endswith("calls") or key == "equilibrium_solves"
    )
