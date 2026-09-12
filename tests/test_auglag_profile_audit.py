from copy import deepcopy

import pytest

from fusion_baselines.auglag_profile_audit import audit_analytic_control, audit_jac_profile


def control():
    return dict(
        x=[1.0, 0.0],
        pass_control=True,
        stop_reason="eight_stages_completed",
        counters=dict(
            limit=1033, attempts=9, requests=20, cache_hits=11, failed_attempts=0, denied=0
        ),
        stages=[
            dict(
                selected_values=[1.0, 0.0, 0.0],
                updated_multipliers=[1.0, 1.0],
                violation=0.0,
                lagrangian_gradient_max=0.0,
            )
        ]
        * 8,
    )


def profile():
    study = dict(
        methods=["natural-auglag-jac"],
        status="completed",
        qualification_pass=True,
        flux_scale=1e-6,
        construction_tolerance=1e-8,
        solver_options=dict(
            method="trf",
            tr_solver="exact",
            loss="linear",
            x_scale="jac",
            ftol=1e-10,
            xtol=1e-10,
            gtol=1e-10,
            max_nfev=100000,
        ),
        thread_environment={
            key: "1"
            for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
        },
        analytic_control=control(),
    )
    arms = [
        dict(
            method="natural-auglag-jac",
            repeat=i,
            representation="direct",
            coordinate_scale=0.01,
            selection_tolerance=1e-8,
        )
        for i in (1, 2)
    ]
    return study, arms


def test_exact_control_and_profile_pass_without_mutation():
    study, arms = profile()
    old = deepcopy((study, arms))
    assert all(audit_analytic_control(control()).values())
    assert all(audit_jac_profile(study, arms).values())
    assert (study, arms) == old


@pytest.mark.parametrize(
    "key,value",
    [
        ("methods", ["natural-auglag"]),
        ("status", "running"),
        ("qualification_pass", False),
        ("flux_scale", 1e-5),
        ("construction_tolerance", 1e-7),
    ],
)
def test_wrong_study_profile_rejected(key, value):
    study, arms = profile()
    study[key] = value
    assert not all(audit_jac_profile(study, arms).values())


@pytest.mark.parametrize("key,value", [("x_scale", 1), ("gtol", 1e-8), ("new_option", True)])
def test_option_drift_rejected(key, value):
    study, arms = profile()
    study["solver_options"][key] = value
    assert not audit_jac_profile(study, arms)["solver_options"]


@pytest.mark.parametrize(
    "key,value",
    [
        ("repeat", 1),
        ("method", "natural-auglag"),
        ("coordinate_scale", 1.0),
        ("selection_tolerance", 1e-6),
        ("representation", "scalar"),
    ],
)
def test_wrong_arm_rejected(key, value):
    study, arms = profile()
    arms[1][key] = value
    assert not audit_jac_profile(study, arms)["arm_profiles"]


@pytest.mark.parametrize(
    "key,value",
    [
        ("x", [1.0, 1.0]),
        ("pass_control", False),
        ("stop_reason", "construction_target"),
    ],
)
def test_control_pass_flag_does_not_replace_direct_recheck(key, value):
    report = control()
    report[key] = value
    assert not all(audit_analytic_control(report).values())


def test_false_stationarity_rejected():
    report = control()
    report["stages"][-1]["updated_multipliers"] = [0.0, 0.0]
    assert not audit_analytic_control(report)["stationarity"]


def test_complementarity_independently_recomputed():
    report = control()
    report["x"] = [1.0 - 1e-6, 0.0]
    assert not audit_analytic_control(report)["complementarity"]


def test_negative_multiplier_rejected():
    report = control()
    report["stages"][-1]["updated_multipliers"] = [-1.0, 1.0]
    assert not audit_analytic_control(report)["multiplier_signs"]


def test_counter_mismatch_rejected():
    report = control()
    report["counters"]["requests"] += 1
    assert not audit_analytic_control(report)["fixed_control"]


def test_thread_drift_rejected():
    study, arms = profile()
    study["thread_environment"]["OMP_NUM_THREADS"] = "2"
    assert not audit_jac_profile(study, arms)["threads"]
