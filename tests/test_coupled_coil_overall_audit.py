"""Synthetic fail-closed pilot accounting/provenance controls, no target runs."""

import copy
import json
import sys
import time
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_coupled_coil_pilot as audit
from current_diagnostic_inputs import reference


def matrix():
    return [
        dict(
            label=f"{target}-n{nbase}-{method}",
            target=target,
            nbase=nbase,
            order=order,
            method=method,
        )
        for target in ("reference", "selected")
        for nbase, order in ((6, 5), (8, 7))
        for method in ("N", "V")
    ]


def common_run():
    case = matrix()[0]
    binding = dict(matrix=matrix())
    run = dict(
        schema_version=1,
        phase="qualification",
        status="completed",
        source=binding,
        case=case,
        seed_x=audit.canonical_seed(6, 5).tolist(),
        names=audit.independent.parameter_names(6, 5),
        transfer_pass=False,
        step4_pass=False,
        equilibrium_solves=0,
        threads={
            key: "1"
            for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
        },
    )
    return run, binding


def rows(seed):
    return [
        dict(index=i, status="completed", x=x.tolist(), J=float(x @ x), gradient=(2 * x).tolist())
        for i, x in enumerate(audit.qualification_coordinates(seed))
    ]


def test_independent_registered_seed_and_all_cases():
    for case in matrix():
        value = audit.canonical_seed(case["nbase"], case["order"])
        assert value.shape == (case["nbase"] * 3 * (2 * case["order"] + 1),)
        coils = value.reshape(case["nbase"], 3, 2 * case["order"] + 1)
        np.testing.assert_array_equal(coils[:, 2, 1], -0.35)
        assert np.all(coils[:, :, 3:] == 0)
    run, binding = common_run()
    assert audit.common(run, binding)[0] == run["case"]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r.pop("step4_pass"),
        lambda r: r.update(step4_pass=True),
        lambda r: r.update(transfer_pass=True),
        lambda r: r.update(schema_version=True),
        lambda r: r.update(status="running"),
        lambda r: r.update(source={}),
        lambda r: r["names"].reverse(),
        lambda r: r["seed_x"].__setitem__(0, r["seed_x"][0] + 1e-15),
        lambda r: r["case"].update(order=8),
    ],
)
def test_common_identity_rejects_missing_false_or_mutated_provenance(mutation):
    run, binding = common_run()
    binding = copy.deepcopy(binding)
    mutation(run)
    with pytest.raises((ValueError, KeyError)):
        audit.common(run, binding)


def test_two_direction_two_step_finite_differences_and_exact_repeat():
    seed = np.linspace(0.01, 0.04, 12)
    sample = rows(seed)
    result = audit.derivative_audit(sample, seed)
    assert result["passed"] and result["exact_repeat"] and len(result["rows"]) == 8
    sample[0]["gradient"][0] += 1
    assert not audit.derivative_audit(sample, seed)["passed"]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r.pop(),
        lambda r: r[1].update(status="failed"),
        lambda r: r[1]["x"].__setitem__(0, 0.9),
        lambda r: r[0]["gradient"].pop(),
        lambda r: r[0].update(J=float("nan")),
    ],
)
def test_derivative_qualification_fails_closed(mutation):
    seed = np.linspace(0.01, 0.04, 12)
    sample = rows(seed)
    mutation(sample)
    with pytest.raises((ValueError, KeyError)):
        audit.derivative_audit(sample, seed)


def test_independently_recomputed_objective_is_also_differentiated():
    seed = np.linspace(0.01, 0.04, 12)
    sample = rows(seed)
    wrong = [r["J"] for r in sample]
    wrong[1] += 1e-5
    assert not audit.derivative_audit(sample, seed, wrong)["passed"]


def search_rows():
    seed = np.array([0.0, 0.0])
    values = [
        dict(index=i, status="completed", x=[0.0, i * 0.01], J=j, gradient=[0.0, 0.0])
        for i, j in enumerate((4.0, 2.0, 2.0))
    ]
    return seed, values


def test_actual_search_minimum_preserves_ties_and_counts_failed_attempt():
    seed, sample = search_rows()
    sample.append(dict(index=3, status="attempted", x=[0.01, 0.01]))
    assert audit.search_selection(sample, seed) == 1
    sample[-1].update(status="failed", error="retained failure")
    assert audit.search_selection(sample, seed) == 1


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r[0].update(x=[0.0, 0.01]),
        lambda r: r[1].update(index=10),
        lambda r: r[1].update(x=[0.121, 0.0]),
        lambda r: r[1].update(J=float("nan")),
        lambda r: r[1].update(gradient=[0.0]),
        lambda r: r[1].update(status="failed"),
        lambda r: r[-1].update(status="failed"),
        lambda r: r.extend(copy.deepcopy(r) * 43),
    ],
)
def test_invalid_search_ledger_cannot_select(mutation):
    seed, sample = search_rows()
    mutation(sample)
    with pytest.raises((ValueError, KeyError)):
        audit.search_selection(sample, seed)


def test_exact_metric_convention_and_no_zero_field_escape():
    assert audit.relative_components(np.ones((64, 3)), np.ones((64, 3)), "B") == 0
    with pytest.raises(ValueError):
        audit.relative_components(np.zeros((64, 3)), np.zeros((64, 3)), "B")
    with pytest.raises(ValueError):
        audit.relative_components(np.ones((64, 3)) + 1e-9, np.ones((64, 3)), "B")
    assert len(set(audit.indices(64))) == 64
    assert audit.indices(1024)[[0, -1]].tolist() == [0, 1023]
    with pytest.raises(ValueError):
        audit.indices(63)


def save_npz(path, **values):
    with path.open("xb") as stream:
        np.savez_compressed(stream, **values)
    return reference(path)


def test_archived64_native_coordinates_are_nested_without_pest_mixing(tmp_path):
    phi, theta = np.meshgrid(
        np.pi * np.arange(64) / 64, 2 * np.pi * np.arange(64) / 64, indexing="ij"
    )
    radius, height = 1 + 0.1 * np.cos(theta), 0.1 * np.sin(theta)
    et = np.stack(
        (-np.cos(phi) * np.sin(theta), -np.sin(phi) * np.sin(theta), np.cos(theta)), axis=-1
    )
    ep = np.stack((-radius * np.sin(phi), radius * np.cos(phi), np.zeros_like(phi)), axis=-1)
    bt, bp = np.full((64, 64), 0.05), np.ones((64, 64))
    native = bt[..., None] * et + bp[..., None] * ep
    ref = save_npz(
        tmp_path / "archive.npz",
        phi=phi,
        theta=theta,
        radius=radius,
        height=height,
        et=et,
        ep=ep,
        bt=bt,
        bp=bp,
        native=native,
    )
    wout = dict(path="synthetic", sha256="not-a-real-target")
    binding = dict(
        targets=dict(reference=dict(wout=wout)),
        target_archives=dict(
            reference=dict(
                wout=wout, fields=[dict(s=s, n=64, arrays=ref) for s in (0.25, 0.5, 0.75)]
            )
        ),
    )
    for n in (16, 32, 64):
        xyz, b = audit.target_arrays(binding, dict(target="reference"), n)
        assert xyz.shape == b.shape == (3 * n * n, 3)
        np.testing.assert_array_equal(b[: n * n], native[:: 64 // n, :: 64 // n].reshape(-1, 3))
    binding["target_archives"]["reference"]["fields"].pop()
    with pytest.raises(ValueError):
        audit.target_arrays(binding, dict(target="reference"), 16)


def analytic_flux_fixture(tmp_path, monkeypatch):
    data = dict(
        lasym=False,
        nfp=2,
        mpol=2,
        ntor=0,
        rbc=[dict(m=0, n=0, value=1.0), dict(m=1, n=0, value=0.1)],
        zbs=[dict(m=1, n=0, value=0.1)],
    )
    target = -2 * np.pi * (1 - np.sqrt(1 - 0.1**2))
    snapshot = dict(scale=1.0, B2_scale=1.0, target_flux=target)

    def field(snapshot, points, ncoil):
        b = np.column_stack((np.zeros(len(points)), 1 / points[:, 0], np.zeros(len(points))))
        a = np.column_stack((np.zeros(len(points)), np.zeros(len(points)), -np.log(points[:, 0])))
        return b, a

    monkeypatch.setattr(audit.independent, "direct_field", field)
    record = dict(
        status="completed",
        ncoil=128,
        **snapshot,
        lines=[],
        areas=[],
        full_bundles=0,
        native_calls=[],
    )
    for n in (256, 512, 1024):
        p, t = audit.independent.loop(data, n)
        b, a = field(snapshot, p, 128)
        ref = save_npz(tmp_path / f"line-{n}.npz", points=p, tangents=t, B=b, A=a)
        record["lines"].append(
            dict(
                status="completed", ntheta=n, arrays=ref, flux=float(np.mean(np.sum(a * t, axis=1)))
            )
        )
        record["native_calls"] += [
            dict(quantity=k, points=n, status="completed") for k in ("B", "A")
        ]
    for r in (16, 32):
        for n in (256, 512, 1024):
            p, normals = audit.independent.fan_area(data, r, n)
            b, a = field(snapshot, p, 128)
            ref = save_npz(
                tmp_path / f"area-{r}-{n}.npz", points=p, weighted_normals=normals, B=b, A=a
            )
            record["areas"].append(
                dict(
                    status="completed",
                    nrho=r,
                    ntheta=n,
                    arrays=ref,
                    flux=float(np.sum(b * normals)),
                )
            )
            record["native_calls"] += [
                dict(quantity=k, points=r * n, status="completed") for k in ("B", "A")
            ]
    return data, snapshot, record


def test_analytic_signed_stokes_all_registered_resolutions(tmp_path, monkeypatch):
    data, snapshot, record = analytic_flux_fixture(tmp_path, monkeypatch)
    result = audit.flux_audit(record, snapshot, data)
    assert result["passed"] and len(result["checks"]) == 6
    assert len(result["direct_errors"]) == 18


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r["areas"].pop(),
        lambda r: r["lines"].reverse(),
        lambda r: r["areas"][0].update(status="error"),
        lambda r: r["areas"][0].update(flux=1.0),
        lambda r: r.update(scale=2.0),
    ],
)
def test_flux_evidence_mutations_rejected(tmp_path, monkeypatch, mutation):
    data, snapshot, record = analytic_flux_fixture(tmp_path, monkeypatch)
    mutation(record)
    with pytest.raises((ValueError, KeyError)):
        audit.flux_audit(record, snapshot, data)


def test_source_hash_mutation_rejected_before_numerical_use(tmp_path):
    path = tmp_path / "state.json"
    path.write_text(json.dumps(dict(kept=True)))
    ref = reference(path)
    assert audit.read(ref) == dict(kept=True)
    path.write_text(json.dumps(dict(kept=False)))
    with pytest.raises(ValueError):
        audit.bind_tree(dict(nested=[ref]))


def test_fine_refinement_uses_coarse_denominator_and_absolute_floor():
    assert audit.refinement(0.1, 0.1005)["passed"]
    assert not audit.refinement(0.1, 0.102)["passed"]
    assert audit.refinement(0, 1e-7)["passed"]
    with pytest.raises(ValueError):
        audit.refinement(float("nan"), 0.1)


@pytest.mark.parametrize(
    "message",
    [
        "strictly positive speed not certified between curve nodes",
        "detected coincident non-endpoint filament positions within roundoff",
        "zero-speed filament",
        "degenerate zero-speed curve",
    ],
)
def test_reproduced_uncertified_geometry_is_open_gate_not_arithmetic_corruption(
    monkeypatch, message
):
    def unavailable(*args):
        raise ValueError(message)

    monkeypatch.setattr(audit.independent, "geometry_certificates", unavailable)
    record = dict(status="uncertified", certificate_available=False, error=f"ValueError: {message}")
    assert audit.geometry_audit(record, {}, {})["geometry_pass"] is False
    record["certificate_available"] = True
    with pytest.raises(ValueError):
        audit.geometry_audit(record, {}, {})


def test_unknown_geometry_error_is_not_relabelled_uncertified(monkeypatch):
    def corrupt(*args):
        raise ValueError("wrong physical mapping")

    monkeypatch.setattr(audit.independent, "geometry_certificates", corrupt)
    record = dict(
        status="uncertified",
        certificate_available=False,
        error="ValueError: wrong physical mapping",
    )
    with pytest.raises(ValueError):
        audit.geometry_audit(record, {}, {})


def test_synthetic_native_qualification_end_to_end_without_real_target(tmp_path, monkeypatch):
    from run_coupled_coil_pilot import save_bundle
    from validate_coupled_coil_pilot import flux_diagnostics

    from fusion_baselines import coupled_coils as core

    data = dict(
        lasym=False,
        lfreeb=False,
        nfp=2,
        mpol=5,
        ntor=10,
        ns_array=[401],
        pres_scale=0,
        curtor=0,
        phiedge=np.pi / 100,
        rbc=[dict(m=0, n=0, value=1.0), dict(m=1, n=0, value=0.1)],
        zbs=[dict(m=1, n=0, value=0.1)],
    )
    input_path, wout_path = tmp_path / "synthetic-input.json", tmp_path / "synthetic-wout.txt"
    input_path.write_text(json.dumps(data))
    wout_path.write_text("synthetic control; not an equilibrium")
    target_source = dict(input=reference(input_path), wout=reference(wout_path))

    def sampled(s, n):
        phi, theta = np.meshgrid(
            np.pi * np.arange(n) / n, 2 * np.pi * np.arange(n) / n, indexing="ij"
        )
        rminor = 0.1 * np.sqrt(s)
        radius, height = 1 + rminor * np.cos(theta), rminor * np.sin(theta)
        et = np.stack(
            (
                -rminor * np.cos(phi) * np.sin(theta),
                -rminor * np.sin(phi) * np.sin(theta),
                rminor * np.cos(theta),
            ),
            axis=-1,
        )
        ep = np.stack((-radius * np.sin(phi), radius * np.cos(phi), np.zeros_like(phi)), axis=-1)
        bt, bp = np.zeros_like(phi), 1 / radius**2
        native = bt[..., None] * et + bp[..., None] * ep
        return dict(
            phi=phi,
            theta=theta,
            radius=radius,
            height=height,
            et=et,
            ep=ep,
            bt=bt,
            bp=bp,
            native=native,
        )

    fields = []
    for s in (0.25, 0.5, 0.75):
        fields.append(
            dict(s=s, n=64, arrays=save_npz(tmp_path / f"archive-{s}.npz", **sampled(s, 64)))
        )
    run, binding = common_run()
    binding.update(
        targets=dict(reference=target_source),
        target_archives=dict(reference=dict(wout=target_source["wout"], fields=fields)),
    )
    monkeypatch.setattr(audit, "sources", lambda root: binding)

    def synthetic_target(wout, input_json, n):
        points, values = [], []
        for s in (0.25, 0.5, 0.75):
            raw = sampled(s, n)
            phi, radius = raw["phi"], raw["radius"]
            points.append(
                np.stack(
                    (radius * np.cos(phi), radius * np.sin(phi), raw["height"]), axis=-1
                ).reshape(-1, 3)
            )
            values.append(raw["native"].reshape(-1, 3))
        return dict(
            input=data,
            inner_points=np.concatenate(points),
            inner_target=np.concatenate(values),
            target_flux=-np.pi / 100,
            sources=target_source,
        )

    monkeypatch.setattr(core, "load_target", synthetic_target)
    model = core.CoupledCoils(wout_path, input_path, 6, 5, "N")
    np.testing.assert_array_equal(model.seed_x, audit.canonical_seed(6, 5))
    run.update(
        initialization_work=model.initialization_work,
        flux_initialization_work=model.initialization_work,
        attempted_bundles=10,
        rows=[],
    )
    for i, x in enumerate(audit.qualification_coordinates(model.seed_x)):
        attempt_path = tmp_path / f"attempt-{i}.json"
        attempt_path.write_text(
            json.dumps(
                dict(index=i, status="attempted", x=x.tolist(), started_monotonic=time.monotonic())
            )
        )
        row = save_bundle(model, x, tmp_path / f"bundle-{i}", i)
        row["attempt"] = reference(attempt_path)
        run["rows"].append(row)
    snapshot = audit.read(run["rows"][0]["snapshot"])
    run["flux"] = flux_diagnostics(model, model.seed_x, snapshot, tmp_path / "flux", ncoil=128)
    result = audit.audit(run, tmp_path)
    assert result["qualification_pass"] is True
    assert result["arithmetic_and_source_pass"] is True
    assert result["transfer_pass"] is False and result["step4_pass"] is False
    run["rows"][1]["J"] += 0.01
    with pytest.raises(ValueError):
        audit.audit(run, tmp_path)


def clock_run(tmp_path):
    marker = tmp_path / "marker.json"
    marker.write_text(json.dumps(dict(monotonic=100.0)))
    run = dict(
        search_clock=dict(
            start_monotonic=100.0,
            parent_stop_monotonic=110.0,
            check_interval=0.5,
            timeout_seconds=600,
            termination_grace_seconds=5,
            marker=reference(marker),
        ),
        terminal=dict(reason="solver_return", parent_stop_monotonic=110.0, nfev=2, njev=2),
        rows=[],
        attempted_bundles=2,
    )
    for i in range(2):
        attempt = tmp_path / f"clock-attempt-{i}.json"
        start = 101.0 + 2 * i
        attempt.write_text(
            json.dumps(dict(index=i, status="attempted", x=[0.0], started_monotonic=start))
        )
        run["rows"].append(
            dict(
                index=i,
                status="completed",
                x=[0.0],
                attempt=reference(attempt),
                started_monotonic=start + 0.1,
                completed_monotonic=start + 1.0,
                elapsed_seconds=1.0,
                supplementary_field_work=dict(boundary_A_calls=1, inner_A_calls=1, loop_B_calls=1),
            )
        )
    return run


def test_wall_clock_excludes_replay_and_accounts_all_attempts(tmp_path):
    run = clock_run(tmp_path)
    assert audit.search_clock(run)["elapsed_seconds"] == 10


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r["search_clock"].update(start_monotonic=101.0),
        lambda r: r["search_clock"].update(timeout_seconds=601),
        lambda r: r["search_clock"].update(check_interval=1.0),
        lambda r: r["search_clock"].update(termination_grace_seconds=6),
        lambda r: r["search_clock"].update(parent_stop_monotonic=800),
        lambda r: r["terminal"].update(nfev=1),
        lambda r: r["terminal"].update(reason="evaluation_budget"),
        lambda r: r.update(attempted_bundles=1),
        lambda r: r["rows"][0].update(completed_monotonic=701),
        lambda r: r["rows"][0]["supplementary_field_work"].update(loop_B_calls=0),
    ],
)
def test_missing_or_forged_work_cannot_pass_clock_audit(tmp_path, mutation):
    run = clock_run(tmp_path)
    mutation(run)
    with pytest.raises((ValueError, KeyError)):
        audit.search_clock(run)
