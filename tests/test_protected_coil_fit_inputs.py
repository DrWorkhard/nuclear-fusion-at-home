"""Synthetic immutable-source admission controls; no native field or geometry work."""

import copy
import sys
from pathlib import Path

import numpy as np
import pytest

from fusion_baselines import clear_coil_geometry_audit as geometry
from fusion_baselines import coupled_coil_audit as physical

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import protected_coil_fit_inputs as binder  # noqa: E402


def ref(path, digest="a"):
    return dict(path=str(path), sha256=digest * 64)


def fixture():
    source = dict(
        matrix=binder.workflow.matrix(),
        repository=dict(commit="old"),
        nested=dict(repository=dict(commit="fixed numerical revision")),
    )
    cells = []
    for i, case in enumerate(source["matrix"]):
        nphysical = 4 * case["nbase"]
        states = []
        for descriptor in binder.direct.plan():
            grids = [
                dict(
                    level,
                    passed=True,
                    nphysical=nphysical,
                    coil_pairs_checked=nphysical * (nphysical - 1) // 2,
                    cp_distances_checked=2 * nphysical * level["ncoil"],
                )
                for level in binder.direct.levels()
            ]
            states.append(
                dict(
                    descriptor,
                    mathematical_pass=True,
                    exact_repeat=True,
                    certified=descriptor["radius"] < 0.03,
                    direct=grids,
                )
            )
        counts = dict(states=26, certificates=52, direct_grids=104, surfaces=2 if i == 0 else 0)
        cells.append(
            dict(
                case=case,
                status="completed",
                arithmetic_and_source_pass=True,
                qualification_pass=True,
                states=states,
                work=dict(
                    passed=True, work={k: dict(attempted=v, completed=v) for k, v in counts.items()}
                ),
            )
        )
    audit = dict(
        schema_version=1,
        kind="coil-perturbation-audit",
        status="completed",
        all_pass=True,
        arithmetic_and_source_pass=True,
        independent_audit_pass=True,
        qualification_pass=True,
        source=copy.deepcopy(source),
        cells=cells,
        independent_work=dict(
            certificate_recomputations=52,
            certificate_records_checked=104,
            direct_grids=208,
            surface_reconstructions=2,
        ),
        **binder.SCOPE,
    )
    run = dict(
        schema_version=1,
        kind="coil-perturbation",
        status="completed",
        producer_complete=True,
        source_unchanged=True,
        admission_status="pending-independent-audit",
        all_pass=False,
        independent_audit_pass=False,
        qualification_pass=False,
        source_before=copy.deepcopy(source),
        source_after=copy.deepcopy(source),
        matrix=copy.deepcopy(source["matrix"]),
        limits=binder.LIMITS.copy(),
        rows=[ref("/synthetic/n6"), ref("/synthetic/n8")],
        **binder.SCOPE,
    )
    current = copy.deepcopy(source)
    current["repository"] = dict(commit="later", dirty=True)
    return audit, run, current


def seed_fixture(case=None):
    case = binder.matrix()[0] if case is None else case
    nbase, order = case["nbase"], case["order"]
    sources = {
        target: {
            key: ref(f"/synthetic/{target}-{key}", str(i))
            for i, key in enumerate(("input", "wout"), 1)
        }
        for target in ("reference", "selected")
    }
    coefficients = np.zeros((nbase, 3, 2 * order + 1))
    coefficients[:, 0, 0], coefficients[:, 0, 2], coefficients[:, 2, 1] = 1.0, 0.25, -0.25
    seed = dict(
        schema_version=1,
        kind="geometry-only",
        nfp=2,
        nbase=nbase,
        order=order,
        names=physical.parameter_names(nbase, order),
        base_coefficients=coefficients.tolist(),
        physical=geometry.physical_rows(nbase),
        case=next(c for c in geometry.cases() if c["label"] == case["seed_label"]),
        sources=sources,
        parameter_orientation="alpha=-2*pi*t",
    )
    copies = copy.deepcopy(seed["physical"])
    for row in copies:
        row["current"] = 100000.0 * (-1 if row["flip"] else 1)
    snapshot = dict(
        schema_version=1,
        nfp=2,
        nbase=nbase,
        order=order,
        method=case["method"],
        names=seed["names"].copy(),
        base_coefficients=coefficients.tolist(),
        physical=copies,
        scale=1.0,
        unit_flux=0.25,
        seed_unit_flux=0.25,
        target_flux=0.25,
        B2_scale=2.0,
        construction=binder.CONSTRUCTION.copy(),
        initialization_work=dict(seed_A_calls=1, seed_A_points=256),
        seed_geometry=copy.deepcopy(seed),
        sources=copy.deepcopy(sources[case["target"]]),
    )
    row = dict(
        status="completed",
        kind="qualification",
        index=0,
        label="seed",
        method=case["method"],
        model_id=f"qualification-{case['method']}",
        operation_id=f"qualification-{case['method']}-00",
        J=0.1,
        x=coefficients.ravel().tolist(),
        gradient=np.ones(coefficients.size).tolist(),
        metrics=dict(
            J=0.1,
            frozen_scale=False,
            B2_scale=2.0,
            scale=1.0,
            target_flux=0.25,
            unit_flux=0.25,
            current=100000.0,
        ),
    )
    source = dict(
        targets=copy.deepcopy(sources),
        normalization={target: dict(B2_scale=2.0, archives=[]) for target in sources},
        target_archives={target: {} for target in sources},
    )
    return row, snapshot, copy.deepcopy(case), seed, source


def test_exact_eight_cells_and_fresh_returned_matrix():
    expected = [
        f"{target}-n{n}-{m}"
        for target in ("reference", "selected")
        for n in (6, 8)
        for m in ("N", "V")
    ]
    assert [row["label"] for row in binder.matrix()] == expected
    assert binder.matrix() == binder.fields.cases()
    changed = binder.matrix()
    changed[0]["method"] = "V"
    assert binder.matrix()[0]["method"] == "N"


def test_complete_synthetic_admission_retains_larger_negatives_without_mutation():
    values = fixture()
    before = copy.deepcopy(values)
    binder.perturbation_gate(*values)
    assert values == before
    assert any(not s["certified"] for c in values[0]["cells"] for s in c["states"])


@pytest.mark.parametrize("document", [0, 1])
@pytest.mark.parametrize("key", list(binder.SCOPE))
def test_every_predecessor_scope_flag_and_zero_is_typed_and_preserved(document, key):
    values = fixture()
    original = values[document][key]
    values[document][key] = False if type(original) is int else 0
    with pytest.raises(ValueError):
        binder.perturbation_gate(*values)


@pytest.mark.parametrize(
    "document,key,value",
    [
        (0, "schema_version", True),
        (0, "kind", "invented"),
        (0, "status", "pending"),
        (0, "all_pass", False),
        (0, "arithmetic_and_source_pass", 1),
        (0, "independent_audit_pass", False),
        (0, "qualification_pass", False),
        (1, "schema_version", 1.0),
        (1, "kind", "invented"),
        (1, "status", "pending"),
        (1, "producer_complete", False),
        (1, "source_unchanged", 1),
        (1, "admission_status", "accepted"),
        (1, "all_pass", True),
        (1, "independent_audit_pass", True),
        (1, "qualification_pass", True),
    ],
)
def test_each_named_overall_gate_is_required(document, key, value):
    values = fixture()
    values[document][key] = value
    with pytest.raises(ValueError):
        binder.perturbation_gate(*values)


@pytest.mark.parametrize(
    "mutation",
    [
        "audit-source",
        "run-before",
        "run-after",
        "current-nested",
        "current-missing",
        "source-matrix",
        "run-matrix",
        "row-count",
        "cell-count",
        "cell-order",
        "limits",
        "limits-bool",
    ],
)
def test_sources_and_complete_ordered_execution_cannot_change(mutation):
    audit, run, current = values = fixture()
    if mutation == "audit-source":
        audit["source"] = None
    elif mutation in ("run-before", "run-after"):
        run[f"source_{mutation.split('-')[1]}"]["nested"]["repository"]["commit"] = "changed"
    elif mutation == "current-nested":
        current["nested"]["repository"]["commit"] = "changed"
    elif mutation == "current-missing":
        current.pop("nested")
    elif mutation == "source-matrix":
        for document in (audit["source"], run["source_before"], run["source_after"], current):
            document["matrix"].reverse()
    elif mutation == "run-matrix":
        run["matrix"].reverse()
    elif mutation == "row-count":
        run["rows"].pop()
    elif mutation == "cell-count":
        audit["cells"].pop()
    elif mutation == "cell-order":
        audit["cells"].reverse()
    elif mutation == "limits":
        run["limits"]["wall_seconds"] = 3600.0
    else:
        run["limits"]["parent_poll_seconds"] = False
    with pytest.raises(ValueError):
        binder.perturbation_gate(*values)


@pytest.mark.parametrize("cell", [0, 1])
@pytest.mark.parametrize(
    "mutation",
    [
        "status",
        "arithmetic",
        "qualification",
        "case",
        "work-pass",
        "work-count",
        "state-count",
        "state-order",
        "state-type",
    ],
)
def test_each_cell_requires_its_own_scope_and_complete_states(cell, mutation):
    values = fixture()
    row = values[0]["cells"][cell]
    if mutation == "status":
        row["status"] = "failed"
    elif mutation == "arithmetic":
        row["arithmetic_and_source_pass"] = False
    elif mutation == "qualification":
        row["qualification_pass"] = 1
    elif mutation == "case":
        row["case"]["geometry_report_index"] = 0
    elif mutation == "work-pass":
        row["work"]["passed"] = False
    elif mutation == "work-count":
        row["work"]["work"]["certificates"]["completed"] = 51
    elif mutation == "state-count":
        row["states"].pop()
    elif mutation == "state-order":
        row["states"].reverse()
    else:
        row["states"][0]["index"] = False
    with pytest.raises(ValueError):
        binder.perturbation_gate(*values)


@pytest.mark.parametrize("cell", [0, 1])
@pytest.mark.parametrize("index", range(26))
def test_all_52_state_mathematical_passes_are_required(cell, index):
    values = fixture()
    values[0]["cells"][cell]["states"][index]["mathematical_pass"] = False
    with pytest.raises(ValueError):
        binder.perturbation_gate(*values)


@pytest.mark.parametrize("index", [0, 1, 2, 9, 10, 17, 18, 25])
def test_each_seed_and_smallest_probe_must_be_certified(index):
    values = fixture()
    values[0]["cells"][0]["states"][index]["certified"] = False
    with pytest.raises(ValueError):
        binder.perturbation_gate(*values)


@pytest.mark.parametrize(
    "mutation",
    [
        "repeat",
        "certified-type",
        "grid-count",
        "grid-order",
        "grid-pass",
        "physical-copies",
        "pair-count",
        "cp-count",
    ],
)
def test_state_repeats_and_every_direct_grid_contract(mutation):
    values = fixture()
    row = values[0]["cells"][1]["states"][4]
    if mutation == "repeat":
        row["exact_repeat"] = False
    elif mutation == "certified-type":
        row["certified"] = 1
    elif mutation == "grid-count":
        row["direct"].pop()
    elif mutation == "grid-order":
        row["direct"].reverse()
    else:
        key = {
            "grid-pass": "passed",
            "physical-copies": "nphysical",
            "pair-count": "coil_pairs_checked",
            "cp-count": "cp_distances_checked",
        }[mutation]
        row["direct"][2][key] = False
    with pytest.raises(ValueError):
        binder.perturbation_gate(*values)


@pytest.mark.parametrize(
    "key",
    [
        "certificate_recomputations",
        "certificate_records_checked",
        "direct_grids",
        "surface_reconstructions",
    ],
)
def test_every_independent_work_total_required(key):
    values = fixture()
    values[0]["independent_work"].pop(key)
    with pytest.raises(ValueError):
        binder.perturbation_gate(*values)


@pytest.mark.parametrize("cell", [0, 1])
@pytest.mark.parametrize("level", range(4))
def test_each_class_and_grid_requires_its_individual_pass(cell, level):
    values = fixture()
    values[0]["cells"][cell]["states"][25]["direct"][level]["passed"] = False
    with pytest.raises(ValueError):
        binder.perturbation_gate(*values)


@pytest.mark.parametrize("location", ["audit", "run", "current", "cell", "state", "grid", "work"])
def test_malformed_nested_records_fail_closed(location):
    values = list(fixture())
    if location in ("audit", "run", "current"):
        values[("audit", "run", "current").index(location)] = None
    elif location == "cell":
        values[0]["cells"][0] = None
    elif location == "state":
        values[0]["cells"][0]["states"][0] = None
    elif location == "grid":
        values[0]["cells"][0]["states"][0]["direct"][0] = None
    else:
        values[0]["cells"][0]["work"] = None
    with pytest.raises(ValueError):
        binder.perturbation_gate(*values)


@pytest.mark.parametrize("case", binder.matrix(), ids=lambda c: c["label"])
def test_eight_complete_canonical_seed_bundles_have_no_side_effect(case):
    values = seed_fixture(case)
    before = copy.deepcopy(values)
    binder.seed_bundle_gate(*values)
    assert values == before


@pytest.mark.parametrize("invalid", [True, np.array(1.), np.array([1.]), [1.], float("nan"),
                                     float("inf")])
def test_seed_unit_flux_requires_exact_finite_scalar_type(invalid):
    values = seed_fixture()
    row, snapshot = values[:2]
    for key in ("unit_flux", "target_flux"):
        snapshot[key] = row["metrics"][key] = 1.0
    row["metrics"]["flux"] = 1.0
    snapshot["seed_unit_flux"] = invalid
    with pytest.raises(ValueError):
        binder.seed_bundle_gate(*values)


@pytest.mark.parametrize(
    "mutation",
    [
        "status",
        "method",
        "index-bool",
        "label",
        "operation",
        "gradient-missing",
        "gradient-bool",
        "gradient-nan",
        "x",
        "signed-zero",
        "names",
        "source",
        "seed-geometry",
        "construction",
        "normalization",
        "initialization",
        "objective-bool",
        "metric-objective",
        "metric-frozen",
        "metric-current",
        "unit-flux",
        "case",
    ],
)
def test_relabelled_or_changed_original_seed_is_rejected(mutation):
    row, snapshot, case, seed, source = values = seed_fixture()
    if mutation in ("status", "method", "label"):
        row[mutation] = "wrong"
    elif mutation == "index-bool":
        row["index"] = False
    elif mutation == "operation":
        row["operation_id"] = "qualification-N-09"
    elif mutation == "gradient-missing":
        row["gradient"].pop()
    elif mutation == "gradient-bool":
        row["gradient"] = [True] * len(row["gradient"])
    elif mutation == "gradient-nan":
        row["gradient"][1] = float("nan")
    elif mutation == "x":
        row["x"][0] += 1e-12
    elif mutation == "signed-zero":
        row["x"][1] = -0.0
    elif mutation == "names":
        snapshot["names"].reverse()
    elif mutation == "source":
        snapshot["sources"]["input"]["sha256"] = "e" * 64
    elif mutation == "seed-geometry":
        snapshot["seed_geometry"]["base_coefficients"][0][0][0] += 1e-3
    elif mutation == "construction":
        snapshot["construction"]["ncoil"] = 512
    elif mutation == "normalization":
        source["normalization"]["reference"]["B2_scale"] = 3.0
    elif mutation == "initialization":
        snapshot["initialization_work"]["seed_A_calls"] = True
    elif mutation == "objective-bool":
        row["J"] = True
    elif mutation == "metric-objective":
        row["metrics"]["J"] += 0.1
    elif mutation == "metric-frozen":
        row["metrics"]["frozen_scale"] = 0
    elif mutation == "metric-current":
        row["metrics"]["current"] = 500001.0
    elif mutation == "unit-flux":
        snapshot["seed_unit_flux"] = 0.3
    else:
        case["nbase"] = 6.0
    with pytest.raises(ValueError):
        binder.seed_bundle_gate(*values)


def wire_prerequisites(root, monkeypatch):
    audit, run, current = fixture()
    documents, reads, graphs, checked, historical = {}, [], [], [], []
    current.update(
        geometry=dict(
            audit=ref(root / "original-geometry-audit.json"),
            run=ref(root / "original-geometry-run.json"),
        ),
        seeds={},
    )
    startup_run_ref = ref(root / "startup-run.json")
    current["startup"] = dict(run=startup_run_ref, audit=ref(root / "startup-audit.json"))
    startup_run = dict(rows=[])
    for physical_case in binder.fields.physical_cases():
        worker_ref = ref(root / f"{physical_case['label']}-worker.json")
        result_ref = ref(root / f"{physical_case['label']}-result.json")
        result = dict(case=copy.deepcopy(physical_case), status="completed", worker=worker_ref)
        worker = dict(case=copy.deepcopy(physical_case), status="completed", qualification={})
        for method in ("N", "V"):
            case = next(
                c
                for c in binder.matrix()
                if c["target"] == physical_case["target"]
                and c["nbase"] == physical_case["nbase"]
                and c["method"] == method
            )
            row, snapshot, _, seed, field_source = seed_fixture(case)
            seed_ref = ref(root / f"{case['seed_label']}.json")
            current["seeds"][case["seed_label"]] = dict(
                snapshot=seed_ref, geometry_report_index=3 if case["nbase"] == 6 else 9
            )
            documents[seed_ref["path"]] = seed
            row_ref = ref(root / f"{case['label']}-bundle.json")
            row["snapshot"] = ref(root / f"{case['label']}-snapshot.json")
            row["arrays"] = ref(root / f"{case['label']}.npz")
            worker["qualification"][method] = [row_ref] * 10
            documents[row_ref["path"]] = row
            documents[row["snapshot"]["path"]] = snapshot
            current["startup"]["source"] = field_source
        documents[worker_ref["path"]], documents[result_ref["path"]] = worker, result
        startup_run["rows"].append(result_ref)
    audit_ref = ref(root / binder.PERTURBATION_AUDIT)
    run_ref = dict(path=str(root / "perturbation-run.json"), sha256=binder.PERTURBATION_RUN_HASH)
    audit["run"] = run_ref
    original = copy.deepcopy(current)
    original["repository"] = dict(commit="original-run")
    audit["source"] = copy.deepcopy(original)
    run["source_before"], run["source_after"] = copy.deepcopy(original), copy.deepcopy(original)
    documents.update(
        {audit_ref["path"]: audit, run_ref["path"]: run, startup_run_ref["path"]: startup_run}
    )
    monkeypatch.setattr(binder.workflow, "sources", lambda p: copy.deepcopy(current))

    def fake_historical(*args):
        historical.append(args)
        return copy.deepcopy(audit_ref)

    def fake_read(reference):
        reads.append(reference)
        return copy.deepcopy(documents[reference["path"]])

    monkeypatch.setattr(binder.previous, "historical", fake_historical)
    monkeypatch.setattr(binder.previous, "bind_tree", lambda v: graphs.append(copy.deepcopy(v)))
    monkeypatch.setattr(binder, "read", fake_read)
    monkeypatch.setattr(binder, "checked", lambda r: checked.append(copy.deepcopy(r)))
    return dict(
        documents=documents,
        audit=audit,
        run=run,
        current=current,
        reads=reads,
        graphs=graphs,
        checked=checked,
        historical=historical,
    )


def test_prerequisites_bind_full_original_graphs_and_expose_all_eight_seeds(tmp_path, monkeypatch):
    wired = wire_prerequisites(tmp_path, monkeypatch)
    result = binder.prerequisites(tmp_path)
    assert wired["historical"] == [
        (
            tmp_path,
            binder.PERTURBATION_AUDIT,
            binder.PERTURBATION_REVISION,
            binder.PERTURBATION_HASH,
        )
    ]
    assert wired["graphs"] == [wired["run"], wired["audit"]]
    assert len(wired["checked"]) == 8
    assert list(result["startup_seed_bundles"]) == [c["label"] for c in binder.matrix()]
    for case in binder.matrix():
        bound = result["startup_seed_bundles"][case["label"]]
        assert set(bound) == {"operation", "snapshot", "arrays"}
        assert case["label"] in bound["operation"]["path"]
        assert case["label"] in bound["snapshot"]["path"]
    assert result["geometry"] == wired["current"]["geometry"]
    result["perturbation"]["source"]["repository"]["commit"] = "modified"
    assert wired["current"]["repository"]["commit"] == "later"


@pytest.mark.parametrize(
    "mutation",
    [
        "run-hash",
        "graph",
        "missing-reference",
        "arrays",
        "worker-cell",
        "qualification-count",
        "seed-coordinates",
    ],
)
def test_missing_changed_or_mislabelled_historical_records_block_admission(
    tmp_path, monkeypatch, mutation
):
    wired = wire_prerequisites(tmp_path, monkeypatch)
    if mutation == "run-hash":
        wired["audit"]["run"]["sha256"] = "0" * 64
    elif mutation == "graph":

        def fail(value):
            raise ValueError("changed raw checkpoint graph")

        monkeypatch.setattr(binder.previous, "bind_tree", fail)
    elif mutation == "missing-reference":
        wired["documents"].pop(str(tmp_path / "reference-n6-worker.json"))
    elif mutation == "arrays":

        def fail(reference):
            raise ValueError("changed arrays")

        monkeypatch.setattr(binder, "checked", fail)
    elif mutation == "worker-cell":
        wired["documents"][str(tmp_path / "reference-n6-worker.json")]["case"]["nbase"] = 8
    elif mutation == "qualification-count":
        wired["documents"][str(tmp_path / "reference-n6-worker.json")]["qualification"]["V"].pop()
    else:
        wired["documents"][str(tmp_path / "reference-n6-N-bundle.json")]["x"][0] += 1e-5
    with pytest.raises((ValueError, KeyError)):
        binder.prerequisites(tmp_path)


def test_sources_require_new_protocol_and_both_owned_files_committed(tmp_path, monkeypatch):
    committed, bound = [], dict(matrix=binder.matrix(), marker="historical prerequisites")
    monkeypatch.setattr(binder, "prerequisites", lambda root: copy.deepcopy(bound))
    monkeypatch.setattr(
        binder, "require_committed", lambda root, path: committed.append((root, path))
    )
    monkeypatch.setattr(binder, "reference", lambda p: ref(p))
    monkeypatch.setattr(binder, "git_state", lambda root: dict(commit="implementation"))
    result = binder.sources(tmp_path)
    assert committed == [(tmp_path, tmp_path / name) for name in (binder.PROTOCOL, *binder.CODE)]
    assert result["protocol"] == ref(tmp_path / binder.PROTOCOL)
    assert result["code"] == [ref(tmp_path / name) for name in binder.CODE]
    assert result["marker"] == bound["marker"]


def test_uncommitted_component_prevents_sources_but_not_historical_preflight(tmp_path, monkeypatch):
    monkeypatch.setattr(binder, "prerequisites", lambda root: {})

    def fail(*args):
        raise ValueError("uncommitted component")

    monkeypatch.setattr(binder, "require_committed", fail)
    assert binder.prerequisites(tmp_path) == {}
    with pytest.raises(ValueError, match="uncommitted"):
        binder.sources(tmp_path)
