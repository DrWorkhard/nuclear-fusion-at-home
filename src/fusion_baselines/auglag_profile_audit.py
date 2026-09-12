"""Independent fixed registration checks, without importing solver options."""

import numpy as np


def audit_analytic_control(control):
    """Recheck the closed-form quadratic, not just its reported pass flag."""
    x = np.asarray(control["x"], dtype=float)
    stages = control["stages"]
    last = stages[-1]
    values = np.asarray(last["selected_values"])
    target = np.array([2.0, -1.0])
    expected = np.r_[0.5 * (x - target) @ (x - target), 1 - x[0], x[1]]
    lam = np.asarray(last["updated_multipliers"])
    stationarity = x - target - np.array([-lam[0], lam[1]])
    violation = max(0.0, -float(np.min(expected[1:])))
    counters = control["counters"]
    return dict(
        solution=bool(x.shape == (2,) and np.max(np.abs(x - [1, 0])) <= 1e-5),
        direct_values=bool(np.allclose(values, expected, rtol=0, atol=1e-14)),
        violation=bool(violation <= 1e-8 and abs(violation - last["violation"]) <= 1e-14),
        stationarity=bool(
            np.isfinite(stationarity).all()
            and np.max(np.abs(stationarity)) <= 1e-6
            and abs(np.max(np.abs(stationarity)) - last["lagrangian_gradient_max"]) <= 1e-14
        ),
        multiplier_signs=bool(np.isfinite(lam).all() and np.min(lam) >= 0),
        complementarity=bool(np.max(np.abs(lam * expected[1:])) <= 1e-8),
        fixed_control=bool(
            control["pass_control"] is True
            and len(stages) == 8
            and control["stop_reason"] == "eight_stages_completed"
            and counters["failed_attempts"] == counters["denied"] == 0
            and counters["limit"] == 1033
            and counters["requests"] == counters["attempts"] + counters["cache_hits"]
            and counters["attempts"] <= 1033
        ),
    )


def audit_jac_profile(study, arms):
    expected = dict(
        method="trf",
        tr_solver="exact",
        loss="linear",
        x_scale="jac",
        ftol=1e-10,
        xtol=1e-10,
        gtol=1e-10,
        max_nfev=100000,
    )
    checks = dict(
        study_profile=bool(
            study["methods"] == ["natural-auglag-jac"]
            and study["status"] == "completed"
            and study["qualification_pass"] is True
            and study["flux_scale"] == 1e-6
            and study["construction_tolerance"] == 1e-8
        ),
        solver_options=study["solver_options"] == expected,
        threads=study["thread_environment"]
        == {
            key: "1"
            for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
        },
        arm_profiles=bool(
            len(arms) == 2
            and [a["repeat"] for a in arms] == [1, 2]
            and all(
                a["method"] == "natural-auglag-jac"
                and a["representation"] == "direct"
                and a["coordinate_scale"] == 0.01
                and a["selection_tolerance"] == 1e-8
                for a in arms
            )
        ),
    )
    checks.update(
        {
            f"analytic_{key}": value
            for key, value in audit_analytic_control(study["analytic_control"]).items()
        }
    )
    return checks
