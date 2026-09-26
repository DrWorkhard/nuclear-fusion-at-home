"""Synthetic metadata contracts; no native imports, fields or curvature evaluation."""

import copy
import hashlib
import math
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fixed_field_probe_inputs as inputs  # noqa: E402


class Catalog:
    """Semantic fixtures after a mocked byte-reader; real I/O has separate tests."""

    def __init__(self, guard=lambda: None):
        self.guard = guard
        self.data = {}
        self.checked = {}

    def put(self, value):
        raw = inputs._encode(value)
        reference = dict(
            path=f"/synthetic/file-{len(self.data):04d}.json",
            bytes=len(raw),
            sha256=hashlib.sha256(raw).hexdigest(),
        )
        self.data[reference["path"]] = copy.deepcopy(value)
        return reference

    def read(self, reference, *, json_data=True):
        self.guard()
        value = copy.deepcopy(self.data[reference["path"]])
        self.checked[reference["path"]] = copy.deepcopy(reference)
        self.guard()
        return value if json_data else inputs._encode(value)

    def object(self, reference):
        return self.data[reference["path"]]


def pair_fixture(catalog, n):
    order = 5 if n == 6 else 7
    ci, pi, trial_index, iteration = (2, 10, 94, 17) if n == 6 else (4, 11, 50, 12)
    case = dict(
        label=f"reference-n{n}-N",
        method="N",
        nbase=n,
        order=order,
        seed_label=f"n{n}-shape-d100mm",
        target="reference",
    )
    names = inputs._names(n, order)
    seed_x = [0.0] * len(names)
    x = seed_x.copy()
    x[0] = 0.01
    candidate = x.copy()
    candidate[0] = x[0] + 0.001 * (-1.0)
    gradient = seed_x.copy()
    gradient[0] = 1.0
    direction = [-g for g in gradient]
    width = 2 * order + 1

    def coefficients(z):
        return [
            [z[(i * 3 + a) * width : (i * 3 + a + 1) * width] for a in range(3)] for i in range(n)
        ]

    physical = [
        dict(
            base_index=i % n,
            period=i // (2 * n),
            flip=bool(i // n % 2),
            matrix=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        )
        for i in range(4 * n)
    ]
    seed = dict(
        nbase=n,
        order=order,
        nfp=2,
        names=names,
        base_coefficients=coefficients(seed_x),
        parameter_orientation="alpha=-2*pi*t",
        physical=physical,
    )
    seed_ref = catalog.put(seed)
    geo_index = 3 if n == 6 else 9
    geometry_report = dict(geometry_pass=True)
    geometry_rows = [None] * 10
    geometry_rows[geo_index] = geometry_report
    geometry_ref = catalog.put(dict(sets=geometry_rows))
    target = dict(input=catalog.put(dict(phi=-0.03)), wout=catalog.put("synthetic wout bytes"))
    original = dict(
        case=case,
        seed=seed,
        seed_reference=seed_ref,
        target_sources=target,
        geometry_audit_reference=geometry_ref,
        geometry_report_index=geo_index,
        geometry_report=geometry_report,
        historical_seed_reference=catalog.put({}),
    )
    old_states, rows = [], []
    for index, label, role, coords, certified in (
        (ci, case["label"], "coarse-selection", x, True),
        (pi, f"rejected-n{n}", "curvature-only-rejection", candidate, False),
    ):
        gates = dict.fromkeys(inputs.GATES, True)
        gates["curvature"] = certified
        state_sha = inputs._state_hash(names, coords)
        proof = dict(
            case=case,
            original_seed=seed_ref,
            geometry_report=geometry_ref,
            geometry_report_index=geo_index,
            state_sha256=state_sha,
            x=coords,
            result=dict(gates=gates, calculation_complete=True, certified=certified),
        )
        proof_ref = catalog.put(proof)
        old = dict(
            label=label,
            role=role,
            case=case,
            old_certificate=proof_ref,
            old_gates=gates,
            state_sha256=state_sha,
            seed=seed_ref,
            geometry_report=geometry_ref,
            geometry_report_index=geo_index,
        )
        row = dict(
            label=label,
            manifest_index=index,
            role=role,
            case=case,
            names=names,
            x=coords,
            state_sha256=state_sha,
            old_certificate=proof_ref,
            old_gates=gates,
            original_seed=seed_ref,
            original_geometry_report=geometry_ref,
            original_geometry_report_index=geo_index,
            field_evaluated=certified,
            control_current_is_proposal_current=False,
        )
        old_states.append(old)
        rows.append(row)
    snapshot = dict(
        names=names,
        base_coefficients=coefficients(x),
        scale=1.0,
        physical=[dict(p, current=100000.0) for p in physical],
    )
    snapshot_ref = catalog.put(snapshot)
    state = dict(x=x, gradient=gradient, value=1.0, metrics={})
    bundle = dict(
        state=state,
        snapshot=snapshot_ref,
        arrays=catalog.put("NPZ placeholder"),
        certificate=rows[0]["old_certificate"],
    )
    bundle_ref = catalog.put(bundle)
    context = dict(
        case=case,
        original_context=original,
        coarse=dict(selected_bundle=bundle_ref),
        selected=dict(state=state, snapshot=snapshot),
    )
    context_ref = catalog.put(context)
    for row, old in zip(rows, old_states, strict=True):
        row.update(
            context=context_ref,
            control_bundle=bundle_ref,
            control_snapshot=snapshot_ref,
            control_scale=1.0,
            control_physical_currents=[100000.0] * (4 * n),
            field_bundle=bundle_ref if row["field_evaluated"] else None,
        )
        old["context"] = context_ref
    previous = dict(
        index=trial_index - 1,
        iteration=iteration - 1,
        accepted=True,
        x=x,
        counters_after=dict(accepted=iteration),
        evaluation=state,
        certificate=dict(certificate_reference=rows[0]["old_certificate"]),
    )
    trial = dict(
        index=trial_index,
        iteration=iteration,
        backtrack=0,
        parent_index=trial_index - 1,
        accepted=False,
        x=candidate,
        counters_before=dict(accepted=iteration),
        evaluation=None,
        current_pass=None,
        armijo_pass=None,
        reason="geometry-rejected",
        certificate=dict(certificate_reference=rows[1]["old_certificate"]),
        alpha=0.001,
        direction=direction,
        directional_derivative=-1.0,
        armijo_rhs=1.0 - 1e-7,
    )
    trials = [None] * (trial_index + 1)
    trials[-2:] = [previous, trial]
    search_ref = catalog.put(
        dict(
            trials=trials,
            selected_index=trial_index - 1,
            accepted_indices=[trial_index - 1],
            selected=state,
        )
    )
    pair = dict(
        case=case,
        control_manifest_index=ci,
        proposal_manifest_index=pi,
        search_report=search_ref,
        predecessor_trial_index=trial_index - 1,
        proposal_trial_index=trial_index,
        predecessor=previous,
        proposal=trial,
        predecessor_objective=1.0,
        predecessor_gradient=gradient,
        direction=direction,
        alpha=0.001,
        armijo_constant=1e-4,
        saved_directional_derivative=-1.0,
        armijo_rhs=1.0 - 1e-7,
        predecessor_bundle=bundle_ref,
        predecessor_snapshot=snapshot_ref,
    )
    return rows, old_states, pair, dict(seed=seed_ref, target=target)


def geometry_fixture(catalog, row, physical):
    state = dict(index=row["manifest_index"], label=row["label"], complete=True)
    binding = dict(study_state_index=row["manifest_index"])
    producers = []
    for phase in ("producer", "audit"):
        references = []
        for i, mapping in enumerate(physical):
            result = dict(curvature_pass=True, audit_pass=True)
            envelope = dict(
                index=i,
                physical=mapping,
                state_sha256=row["state_sha256"],
                phase=phase,
                result=result,
                producer_report=None if phase == "producer" else producers[i],
                interval_arithmetic=False,
                field_pass=False,
                physical_admission=False,
                step4_pass=False,
            )
            references.append(catalog.put(envelope))
        index = dict(
            complete=True,
            curvature_pass=True,
            local_geometry_pass=True,
            old_certificate_matched=True,
            state_sha256=row["state_sha256"],
            old_gates=row["old_gates"],
            label=row["label"],
            phase=phase,
            curves=[
                dict(index=i, reference=ref, curvature_pass=True)
                for i, ref in enumerate(references)
            ],
        )
        index_ref = catalog.put(index)
        config_ref = catalog.put(dict(index=row["manifest_index"], phase=phase))
        parent_ref = catalog.put(
            dict(
                complete=True,
                returned_validated=True,
                returncode=0,
                error=None,
                phase=phase,
                config=config_ref,
                returned=dict(index=index_ref, complete=True),
                prefix=references,
            )
        )
        binding[phase] = dict(
            parent=parent_ref, config=config_ref, index=index_ref, curves=references
        )
        state[phase] = parent_ref
        if phase == "producer":
            producers = references
    row["geometry"] = binding
    return state


@pytest.fixture
def fixture(monkeypatch):
    catalog = Catalog()
    rows, originals, pairs, seeds, targets = [], [None] * 12, [], {}, None
    for n in (6, 8):
        selected, old, pair, source = pair_fixture(catalog, n)
        rows.extend(selected)
        pairs.append(pair)
        for row, original in zip(selected, old, strict=True):
            originals[row["manifest_index"]] = original
        seeds[f"n{n}-shape-d100mm"] = dict(snapshot=source["seed"])
        if targets is None:
            targets = source["target"]
        else:
            for row in selected:
                context = catalog.object(row["context"])
                context["original_context"]["target_sources"] = targets
    study_states, evidence_states = [None] * 12, [None] * 12
    for row in rows:
        seed = catalog.object(row["original_seed"])
        study_states[row["manifest_index"]] = geometry_fixture(catalog, row, seed["physical"])
        evidence_states[row["manifest_index"]] = dict(
            index=row["manifest_index"],
            label=row["label"],
            state_sha256=row["state_sha256"],
            complete=True,
            new_local_geometry_pass=True,
            phases={
                phase: dict(
                    complete=True,
                    curvature_pass=True,
                    local_geometry_pass=True,
                    counts=dict(curves=len(seed["physical"])),
                )
                for phase in ("producer", "audit")
            },
        )
    study_ref = catalog.put(
        dict(
            states=study_states,
            complete=True,
            source_unchanged=True,
            source_before=dict(old_head="historical"),
            source_after=dict(old_head="historical"),
        )
    )
    execution_ref = catalog.put(dict(exit_code=0, explicit_return=dict(returned_index=study_ref)))
    reviews = dict(
        main_saved_review=catalog.put(dict(status="scoped-pass")),
        independent_review=catalog.put(dict(review_pass=True)),
    )
    geometry_ref = catalog.put(
        dict(
            status="completed",
            geometry_component_pass=True,
            states=evidence_states,
            references=dict(study=study_ref, execution=execution_ref, **reviews),
        )
    )
    sources = dict(seeds=seeds, targets=dict(reference=targets))
    native = dict(cell_sources=sources)
    archived = dict(physics_sources=dict(native_sources=native), repository=dict(commit="old"))
    source_ref = catalog.put(archived)
    archive = dict(
        source_before=source_ref,
        source_after=source_ref,
        evidence=catalog.put({}),
        native_inputs_canonical_sha256=hashlib.sha256(inputs._encode(native)).hexdigest(),
        cell_inputs_canonical_sha256=hashlib.sha256(inputs._encode(sources)).hexdigest(),
    )
    manifest = dict(
        states=rows,
        pairs=pairs,
        geometry_evidence=geometry_ref,
        geometry_study=study_ref,
        geometry_execution=execution_ref,
        geometry_reviews=reviews,
        original_manifest=catalog.put(dict(states=originals)),
        archived_coarse=archive,
    )
    monkeypatch.setattr(
        inputs, "_registration", lambda root, reader: ({"synthetic": True}, copy.deepcopy(manifest))
    )

    def reader(guard):
        catalog.guard = guard
        return catalog

    monkeypatch.setattr(inputs, "_Reader", reader)
    return catalog, manifest


def test_synthetic_whole_metadata_intake(fixture):
    catalog, manifest = fixture
    result = inputs.intake()
    assert [s["row"]["manifest_index"] for s in result["states"]] == [2, 10, 4, 11]
    assert sum(len(s["seed"]["physical"]) for s in result["states"]) == 112
    assert result["current_admission"] is None
    assert all(p["immediate_predecessor"] and p["exact_proposal_bits"] for p in result["pairs"])
    assert all(result[k] is False for k in inputs.SCOPE)
    result["states"][0]["seed"]["physical"][0]["base_index"] = 99
    assert catalog.object(manifest["states"][0]["original_seed"])["physical"][0]["base_index"] == 0


@pytest.mark.parametrize(
    "mutation",
    [
        "names",
        "state-hash",
        "inactive-sign",
        "seed-class-bool",
        "matrix-bool",
        "physical-count",
        "old-gate-type",
        "old-seven-fail",
        "old-certificate-seed",
        "old-certificate-incomplete",
        "original-seed",
        "target",
        "snapshot-coordinates",
        "snapshot-matrix",
        "control-current",
        "invented-proposal-field",
        "case",
        "original-report",
        "old-curvature",
    ],
)
def test_state_negatives(fixture, mutation):
    catalog, manifest = fixture
    row = manifest["states"][0]
    seed = catalog.object(row["original_seed"])
    proof = catalog.object(row["old_certificate"])
    context = catalog.object(row["context"])
    snapshot = catalog.object(row["control_snapshot"])
    if mutation == "names":
        row["names"][0] = "wrong"
    elif mutation == "state-hash":
        row["state_sha256"] = "0" * 64
    elif mutation == "inactive-sign":
        row["x"][5] = -0.0
    elif mutation == "seed-class-bool":
        seed["nbase"] = True
    elif mutation == "matrix-bool":
        seed["physical"][0]["matrix"][0][0] = True
    elif mutation == "physical-count":
        seed["physical"].pop()
    elif mutation == "old-gate-type":
        proof["result"]["gates"]["regularity"] = 1
    elif mutation == "old-seven-fail":
        proof["result"]["gates"]["regularity"] = False
    elif mutation == "old-certificate-seed":
        proof["original_seed"] = row["old_certificate"]
    elif mutation == "old-certificate-incomplete":
        proof["result"]["calculation_complete"] = False
    elif mutation == "original-seed":
        context["original_context"]["seed"]["base_coefficients"][0][0][0] = 1.0
    elif mutation == "target":
        context["original_context"]["target_sources"] = {}
    elif mutation == "snapshot-coordinates":
        snapshot["base_coefficients"][0][0][0] = 2.0
    elif mutation == "snapshot-matrix":
        snapshot["physical"][0]["matrix"][0][0] = -1.0
    elif mutation == "control-current":
        row["control_physical_currents"][0] = 0.0
    elif mutation == "invented-proposal-field":
        manifest["states"][1]["field_bundle"] = row["control_bundle"]
    elif mutation == "case":
        row["case"]["method"] = "V"
    elif mutation == "original-report":
        context["original_context"]["geometry_report"] = {}
    elif mutation == "old-curvature":
        proof["result"]["gates"]["curvature"] = False
    with pytest.raises(ValueError):
        inputs.intake()


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-copy",
        "parent-false",
        "return-bool",
        "wrong-config",
        "wrong-return",
        "prefix",
        "matrix",
        "copy-state",
        "copy-index",
        "audit-negative",
        "audit-producer",
        "scope",
        "index-negative",
        "evidence-negative",
        "evidence-copy-count",
        "study-source",
        "execution",
    ],
)
def test_geometry_chain_negatives(fixture, mutation):
    catalog, manifest = fixture
    row = manifest["states"][0]
    link = row["geometry"]["audit"]
    parent = catalog.object(link["parent"])
    index = catalog.object(link["index"])
    copy_ = catalog.object(link["curves"][0])
    evidence = catalog.object(manifest["geometry_evidence"])
    if mutation == "missing-copy":
        link["curves"].pop()
    elif mutation == "parent-false":
        parent["returned_validated"] = False
    elif mutation == "return-bool":
        parent["returncode"] = False
    elif mutation == "wrong-config":
        catalog.object(link["config"])["index"] = 4
    elif mutation == "wrong-return":
        parent["returned"]["index"] = link["parent"]
    elif mutation == "prefix":
        parent["prefix"].reverse()
    elif mutation == "matrix":
        copy_["physical"]["matrix"][0][0] = -1.0
    elif mutation == "copy-state":
        copy_["state_sha256"] = "0" * 64
    elif mutation == "copy-index":
        copy_["index"] = True
    elif mutation == "audit-negative":
        copy_["result"]["audit_pass"] = False
    elif mutation == "audit-producer":
        copy_["producer_report"] = link["curves"][0]
    elif mutation == "scope":
        copy_["interval_arithmetic"] = True
    elif mutation == "index-negative":
        index["old_certificate_matched"] = False
    elif mutation == "evidence-negative":
        evidence["states"][2]["new_local_geometry_pass"] = False
    elif mutation == "evidence-copy-count":
        evidence["states"][2]["phases"]["audit"]["counts"]["curves"] = 23
    elif mutation == "study-source":
        catalog.object(manifest["geometry_study"])["source_after"] = {}
    elif mutation == "execution":
        catalog.object(manifest["geometry_execution"])["exit_code"] = True
    with pytest.raises(ValueError):
        inputs.intake()


@pytest.mark.parametrize(
    "mutation",
    [
        "parent",
        "trial-index",
        "iteration",
        "accepted",
        "fields",
        "direction",
        "slope",
        "alpha",
        "rhs",
        "gradient",
        "proposal-bits",
        "inactive-sign",
        "certificate",
        "case",
        "pair-index",
        "selected",
        "counter",
        "armijo-constant",
        "saved-objective",
    ],
)
def test_armijo_negatives(fixture, mutation):
    catalog, manifest = fixture
    pair = manifest["pairs"][0]
    search = catalog.object(pair["search_report"])
    trial = search["trials"][94]
    previous = search["trials"][93]
    if mutation == "parent":
        trial["parent_index"] = 92
    elif mutation == "trial-index":
        trial["index"] = 93
    elif mutation == "iteration":
        trial["iteration"] = 16
    elif mutation == "accepted":
        trial["accepted"] = True
    elif mutation == "fields":
        trial["evaluation"] = {}
    elif mutation == "direction":
        trial["direction"][0] = -0.5
    elif mutation == "slope":
        trial["directional_derivative"] = -2.0
    elif mutation == "alpha":
        trial["alpha"] = 0.002
    elif mutation == "rhs":
        trial["armijo_rhs"] = math.nextafter(trial["armijo_rhs"], math.inf)
    elif mutation == "gradient":
        previous["evaluation"]["gradient"][0] = 2.0
    elif mutation == "proposal-bits":
        trial["x"][0] = math.nextafter(trial["x"][0], math.inf)
    elif mutation == "inactive-sign":
        trial["x"][5] = -0.0
    elif mutation == "certificate":
        trial["certificate"]["certificate_reference"] = {}
    elif mutation == "case":
        pair["case"]["method"] = "V"
    elif mutation == "pair-index":
        pair["proposal_manifest_index"] = 11
    elif mutation == "selected":
        search["selected_index"] = 92
    elif mutation == "counter":
        trial["counters_before"]["accepted"] = 0
    elif mutation == "armijo-constant":
        pair["armijo_constant"] = 0.001
    elif mutation == "saved-objective":
        pair["predecessor_objective"] = math.nextafter(1.0, math.inf)
    # Keep the duplicated frozen trial record coherent so later arithmetic gates
    # are exercised, not only rejection of a mismatched embedded record.
    pair["proposal"] = copy.deepcopy(trial)
    pair["predecessor"] = copy.deepcopy(previous)
    with pytest.raises(ValueError):
        inputs.intake()


def test_original_search_objective_not_almost_equal_bundle(fixture):
    catalog, manifest = fixture
    row = manifest["states"][0]
    bundle = catalog.object(row["control_bundle"])
    bundle["state"]["value"] = math.nextafter(1.0, math.inf)
    context = catalog.object(row["context"])
    context["selected"]["state"]["value"] = bundle["state"]["value"]
    result = inputs.intake()
    assert result["pairs"][0]["original_search_objective"] == 1.0
    assert result["states"][0]["control_bundle"]["state"]["value"] != 1.0


def test_additive_native_admission_is_lazy_private_and_guarded(fixture, monkeypatch):
    catalog, manifest = fixture
    calls = []
    archived = catalog.object(manifest["archived_coarse"]["source_before"])
    current = dict(
        archived_source=archived,
        current_provenance=dict(commit="new"),
        fine_execution_authorized=False,
        physical_admission=False,
        step4_pass=False,
        **{
            k: manifest["archived_coarse"][k] for k in ("source_before", "source_after", "evidence")
        },
    )

    def archive(root):
        calls.append("archive")
        return current

    monkeypatch.setattr(inputs, "_archive", archive)
    inputs.intake(guard=lambda: calls.append("guard"))
    assert "archive" not in calls
    result = inputs.intake(guard=lambda: calls.append("guard"), native_admission=True)
    i = calls.index("archive")
    assert calls[i - 1 : i + 2] == ["guard", "archive", "guard"]
    assert result["archived_source"]["repository"]["commit"] == "old"
    assert result["current_admission"]["current_provenance"]["commit"] == "new"
    result["current_admission"]["current_provenance"]["commit"] = "changed"
    assert current["current_provenance"]["commit"] == "new"


def test_native_admission_cannot_rewrite_archived_head(fixture, monkeypatch):
    catalog, manifest = fixture
    archived = copy.deepcopy(catalog.object(manifest["archived_coarse"]["source_before"]))
    archived["repository"]["commit"] = "current"
    monkeypatch.setattr(inputs, "_archive", lambda root: dict(archived_source=archived))
    with pytest.raises(ValueError, match="preserves original"):
        inputs.intake(native_admission=True)


@pytest.mark.parametrize("when", [1, 30, 150, 500])
def test_guard_failure_cannot_return_context(fixture, when):
    count = 0

    def guard():
        nonlocal count
        count += 1
        if count == when:
            raise TimeoutError("test deadline")

    with pytest.raises(TimeoutError):
        inputs.intake(guard=guard)


def test_guard_failure_immediately_after_native_admission(fixture, monkeypatch):
    active = False

    def archive(root):
        nonlocal active
        active = True
        return {}

    def guard():
        if active:
            raise TimeoutError("post-admission")

    monkeypatch.setattr(inputs, "_archive", archive)
    with pytest.raises(TimeoutError, match="post-admission"):
        inputs.intake(guard=guard, native_admission=True)


@pytest.mark.parametrize("bad", [None, 1, "yes", []])
def test_native_admission_exact_bool(bad):
    with pytest.raises(ValueError):
        inputs.intake(native_admission=bad)


def file_ref(path, raw):
    path.write_bytes(raw)
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


@pytest.mark.parametrize(
    "mutation",
    [
        "digest",
        "size",
        "bool-size",
        "extra",
        "relative",
        "uppercase",
        "missing",
        "empty",
        "duplicate",
        "nonfinite",
        "invalid-json",
        "symlink",
        "too-large",
    ],
)
def test_bounded_reader_negatives(tmp_path, monkeypatch, mutation):
    raw = b'{"x":1}'
    if mutation == "empty":
        raw = b""
    elif mutation == "duplicate":
        raw = b'{"x":1,"x":2}'
    elif mutation == "nonfinite":
        raw = b'{"x":NaN}'
    elif mutation == "invalid-json":
        raw = b"["
    ref = file_ref(tmp_path / "data.json", raw)
    if mutation == "digest":
        ref["sha256"] = "0" * 64
    elif mutation == "size":
        ref["bytes"] += 1
    elif mutation == "bool-size":
        ref["bytes"] = True
    elif mutation == "extra":
        ref["unexpected"] = 1
    elif mutation == "relative":
        ref["path"] = "data.json"
    elif mutation == "uppercase":
        ref["sha256"] = ref["sha256"].upper()
    elif mutation == "missing":
        ref["path"] = str(tmp_path / "missing.json")
    elif mutation == "symlink":
        link = tmp_path / "link.json"
        link.symlink_to(tmp_path / "data.json")
        ref["path"] = str(link)
    elif mutation == "too-large":
        monkeypatch.setattr(inputs, "JSON_BYTES", 3)
    with pytest.raises(ValueError):
        inputs._Reader(lambda: None).read(ref)


def test_reader_roundtrip_copy_bits_and_guards(tmp_path):
    count = []
    ref = file_ref(tmp_path / "data.json", b'{"x":[-0.0,1.0]}')
    reader = inputs._Reader(lambda: count.append(1))
    result = reader.read(ref)
    assert inputs._bits(result["x"]) == inputs._bits([-0.0, 1.0])
    result["x"][0] = 2.0
    assert reader.read(ref)["x"][0] == 0.0 and len(count) == 4
    assert len(reader.checked) == 1


def test_reader_detects_same_path_with_rewritten_reference(tmp_path):
    path = tmp_path / "data.json"
    first = file_ref(path, b"{}")
    reader = inputs._Reader(lambda: None)
    reader.read(first)
    second = file_ref(path, b'{"x":1}')
    with pytest.raises(ValueError, match="during intake"):
        reader.read(second)


def test_registration_exact_pins_and_all_294_reads(tmp_path, monkeypatch):
    catalog = Catalog()
    refs = [catalog.put(dict(i=i)) for i in range(294)]
    manifest = dict(
        schema_version=1,
        kind="local-curvature-field-probe-fixed-inputs",
        selection_only=True,
        execution_allowed=False,
        states=[
            dict(manifest_index=i, label=label)
            for i, label in zip(inputs.INDICES, inputs.LABELS, strict=True)
        ],
        checked_references=refs,
    )
    protocol = catalog.put("protocol")
    mr = catalog.put(manifest)
    for reference, path in ((protocol, inputs.PROTOCOL), (mr, inputs.INPUTS)):
        catalog.data[str(tmp_path / path)] = catalog.data.pop(reference["path"])
        reference["path"] = str(tmp_path / path)
    registration = dict(
        schema_version=1,
        kind="fixed-field-probe-registration",
        status="registered-for-implementation",
        execution_allowed=False,
        references=dict(protocol=protocol, inputs=mr),
    )
    reg = catalog.put(registration)
    catalog.data[str(tmp_path / inputs.REGISTRATION)] = catalog.data.pop(reg["path"])
    monkeypatch.setattr(
        inputs,
        "PINS",
        {
            inputs.REGISTRATION: reg["sha256"],
            inputs.INPUTS: mr["sha256"],
            inputs.PROTOCOL: protocol["sha256"],
        },
    )
    _, result = inputs._registration(tmp_path, catalog)
    assert len(result["checked_references"]) == 294
    assert all(r["path"] in catalog.checked for r in refs)
    for mutation in ("count", "duplicate", "order", "schema", "protocol"):
        changed = copy.deepcopy(manifest)
        catalog.data[mr["path"]] = changed
        if mutation == "count":
            changed["checked_references"].pop()
        elif mutation == "duplicate":
            changed["checked_references"][-1] = refs[0]
        elif mutation == "order":
            changed["states"].reverse()
        elif mutation == "schema":
            changed["schema_version"] = True
        elif mutation == "protocol":
            catalog.data[str(tmp_path / inputs.REGISTRATION)]["references"]["protocol"][
                "sha256"
            ] = "0" * 64
        with pytest.raises(ValueError):
            inputs._registration(tmp_path, catalog)


def test_default_module_import_is_standard_library_only():
    path = Path(inputs.__file__).resolve()
    code = f"""import importlib.util,sys
for name in ("numpy","scipy","simsopt","simsoptpp","protected_fine_inputs",
             "fusion_baselines.local_curvature","fusion_baselines.coil_perturbation"):
    sys.modules[name]=None
spec=importlib.util.spec_from_file_location("pure_probe_inputs",{str(path)!r})
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
assert "protected_fine_inputs" in sys.modules and sys.modules["protected_fine_inputs"] is None
"""
    subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, timeout=10)


def test_direction_keeps_original_search_tolerance(fixture):
    catalog, manifest = fixture
    contexts = inputs.intake()["states"]
    pair = copy.deepcopy(manifest["pairs"][0])
    trial = catalog.object(pair["search_report"])["trials"][94]
    # Coherent coordinates/slope/RHS cannot excuse exceeding the original
    # direction audit tolerance (5e-12 relative OR 1e-12 absolute).
    trial["direction"][0] *= 1 + 1e-10
    trial["x"][0] = contexts[0]["x"][0] + trial["alpha"] * trial["direction"][0]
    contexts[1]["x"] = trial["x"]
    trial["directional_derivative"] = trial["direction"][0]
    trial["armijo_rhs"] = 1.0 + 1e-4 * trial["alpha"] * trial["directional_derivative"]
    pair["proposal"] = copy.deepcopy(trial)
    pair["direction"] = trial["direction"]
    pair["saved_directional_derivative"] = trial["directional_derivative"]
    pair["armijo_rhs"] = trial["armijo_rhs"]
    with pytest.raises(ValueError, match="preconditioned direction"):
        inputs._armijo(pair, contexts[0], contexts[1], catalog)
