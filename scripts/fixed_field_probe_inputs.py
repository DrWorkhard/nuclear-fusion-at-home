"""Strict, field-free intake for the registered four-state diagnostic.

Default intake imports only the standard library. Native admission lazily reuses
the already qualified archive/environment checker; it does not authorize a run.
Old source identities remain historical and are never rewritten to current HEAD.
"""

import copy
import hashlib
import json
import math
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRATION = "evidence/fixed-field-probe-registration-v1.json"
PROTOCOL = "docs/optimization/FIXED_FIELD_PROBE_PROTOCOL.md"
INPUTS = "evidence/fixed-field-probe-inputs-v1.json"
PINS = {
    REGISTRATION: "17d22988b1025ecb0959ed97dd08cb23974e4872c4d6aa5a9cf437a533b078f7",
    PROTOCOL: "fbcfc9200f15450bde796c3dc5f8a4f2e4e53ff70db3044e6ee05fdeb11dc298",
    INPUTS: "4997daf18d1ec5d94e1e6fd73f74e2a9ca8a83d269986241fdf64fb80c456699",
}
INDICES = (2, 10, 4, 11)
LABELS = ("reference-n6-N", "rejected-n6", "reference-n8-N", "rejected-n8")
GATES = {
    "regularity",
    "projection",
    "length",
    "curvature",
    "direct_plasma",
    "analytic_plasma",
    "direct_coil",
    "analytic_coil",
}
SCOPE = dict(
    execution_allowed=False,
    physical_admission=False,
    step4_pass=False,
    ms1_reached=False,
    sota_advance=False,
)
JSON_BYTES, FILE_BYTES = 8 * 1024**2, 64 * 1024**2


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _encode(value):
    return (
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        )
        + "\n"
    ).encode("utf-8")


def _same(actual, expected, message):
    _need(_encode(actual) == _encode(expected), message)


def _unique(pairs):
    result = {}
    for key, value in pairs:
        _need(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def _bits(values):
    _need(
        type(values) is list and all(type(x) is float and math.isfinite(x) for x in values),
        "finite binary64 list",
    )
    return struct.pack("<" + "d" * len(values), *values)


def _flatten(coefficients):
    return [x for coil in coefficients for axis in coil for x in axis]


def _names(nbase, order):
    modes = ["c(0)"] + [f"{part}({m})" for m in range(1, order + 1) for part in ("s", "c")]
    return [f"coil[{i}]/{axis}{mode}" for i in range(nbase) for axis in "xyz" for mode in modes]


def _state_hash(names, x):
    _bits(x)
    return hashlib.sha256(_encode(dict(schema_version=1, names=names, x=x))).hexdigest()


class _Reader:
    """Bounded direct-file identities only, not a generic graph traversal."""

    def __init__(self, guard):
        self.guard, self.checked = guard, {}

    def read(self, reference, *, json_data=True):
        self.guard()
        _need(
            type(reference) is dict
            and set(reference) in ({"path", "sha256"}, {"path", "sha256", "bytes"}),
            "exact reference schema",
        )
        _need(
            type(reference["path"]) is str
            and type(reference["sha256"]) is str
            and re.fullmatch(r"[0-9a-f]{64}", reference["sha256"]),
            "reference types/hash",
        )
        path = Path(reference["path"])
        _need(
            path.is_absolute() and not path.is_symlink() and path.is_file(),
            "absolute regular nonsymlink reference",
        )
        limit = JSON_BYTES if json_data else FILE_BYTES
        if "bytes" in reference:
            _need(
                type(reference["bytes"]) is int and 0 < reference["bytes"] <= limit,
                "bounded reference byte count",
            )
        with path.open("rb") as stream:
            raw = stream.read(limit + 1)
        _need(0 < len(raw) <= limit, "bounded nonempty referenced file")
        digest = hashlib.sha256(raw).hexdigest()
        _need(digest == reference["sha256"], "reference digest changed")
        _need("bytes" not in reference or len(raw) == reference["bytes"], "reference size changed")
        actual = dict(path=str(path), sha256=digest, bytes=len(raw))
        if str(path) in self.checked:
            _same(actual, self.checked[str(path)], "reference changed during intake")
        self.checked[str(path)] = actual
        self.guard()
        if not json_data:
            return raw
        value = json.loads(raw, object_pairs_hook=_unique)
        _encode(value)
        return value


def _registration(root, reader):
    reference = dict(path=str(root / REGISTRATION), sha256=PINS[REGISTRATION])
    registration = reader.read(reference)
    _need(
        type(registration.get("schema_version")) is int
        and registration["schema_version"] == 1
        and registration["kind"] == "fixed-field-probe-registration"
        and registration["status"] == "registered-for-implementation"
        and registration["execution_allowed"] is False,
        "fixed implementation registration",
    )
    for key, path in (("protocol", PROTOCOL), ("inputs", INPUTS)):
        registered = registration["references"][key]
        _need(
            registered["path"] == str(root / path) and registered["sha256"] == PINS[path],
            "pinned registration link",
        )
    for reference in registration["references"].values():
        reader.read(reference, json_data=False)
    manifest = reader.read(registration["references"]["inputs"])
    _need(
        type(manifest["schema_version"]) is int
        and manifest["schema_version"] == 1
        and manifest["kind"] == "local-curvature-field-probe-fixed-inputs"
        and manifest["selection_only"] is True
        and manifest["execution_allowed"] is False,
        "fixed selection-only manifest",
    )
    _same([s["manifest_index"] for s in manifest["states"]], list(INDICES), "four fixed indices")
    _same([s["label"] for s in manifest["states"]], list(LABELS), "four fixed labels")
    references = manifest["checked_references"]
    _need(
        type(references) is list
        and len(references) == 294
        and len({r["path"] for r in references}) == 294,
        "294 unique selector references",
    )
    for reference in references:
        reader.read(reference, json_data=False)
    return registration, manifest


def _geometry(row, old, seed, study, reader):
    """Bind recorded independent successes and every physical copy; no new bounds."""
    index = row["manifest_index"]
    saved = study["states"][index]
    _need(
        saved["index"] == index and saved["label"] == row["label"] and saved["complete"] is True,
        "completed fixed geometry state",
    )
    _same(row["geometry"]["study_state_index"], index, "geometry state index")
    producers = []
    for phase in ("producer", "audit"):
        link = row["geometry"][phase]
        _same(link["parent"], saved[phase], "study phase parent reference")
        parent = reader.read(link["parent"])
        _need(
            parent["complete"] is True
            and parent["returned_validated"] is True
            and type(parent["returncode"]) is int
            and parent["returncode"] == 0
            and parent["error"] is None
            and parent["phase"] == phase,
            "successful phase parent",
        )
        _same(parent["config"], link["config"], "geometry configuration reference")
        config = reader.read(link["config"])
        _same(config["index"], index, "phase configuration index")
        _same(config["phase"], phase, "phase configuration phase")
        _same(parent["returned"]["index"], link["index"], "explicit returned phase index")
        _need(parent["returned"]["complete"] is True, "complete returned phase")
        result = reader.read(link["index"])
        for flag in (
            "complete",
            "curvature_pass",
            "local_geometry_pass",
            "old_certificate_matched",
        ):
            _need(result[flag] is True, "successful saved geometry: " + flag)
        _same(result["state_sha256"], row["state_sha256"], "geometry named state")
        _same(result["old_gates"], old["old_gates"], "geometry unchanged old gates")
        _same(result["label"], row["label"], "geometry state label")
        _same(result["phase"], phase, "geometry phase label")
        _need(
            len(result["curves"]) == len(link["curves"]) == len(seed["physical"]),
            "complete physical geometry coverage",
        )
        _same(parent["prefix"], link["curves"], "complete acknowledged curve prefix")
        for i, (curve, reference, physical) in enumerate(
            zip(result["curves"], link["curves"], seed["physical"], strict=True)
        ):
            reader.guard()
            _same(curve["reference"], reference, "exact geometry copy reference")
            _same(curve["index"], i, "ordered geometry copy index")
            _need(curve["curvature_pass"] is True, "passing index copy")
            envelope = reader.read(reference)
            _same(envelope["index"], i, "ordered curve envelope")
            _same(envelope["physical"], physical, "actual original physical matrix")
            _same(envelope["state_sha256"], row["state_sha256"], "copy named state")
            _same(envelope["phase"], phase, "copy phase")
            _need(envelope["result"]["curvature_pass"] is True, "saved curvature pass")
            for flag in ("interval_arithmetic", "field_pass", "physical_admission", "step4_pass"):
                _need(envelope[flag] is False, "geometry-only scope")
            if phase == "producer":
                _need(envelope["producer_report"] is None, "original producer copy")
                producers.append(reference)
            else:
                _need(envelope["result"]["audit_pass"] is True, "independent saved audit")
                _same(envelope["producer_report"], producers[i], "audit exact producer binding")


def _state(row, old, sources, study, reader):
    case = row["case"]
    n, order = case["nbase"], case["order"]
    _need(type(n) is type(order) is int and (n, order) in ((6, 5), (8, 7)), "registered class")
    _same(
        case,
        dict(
            label=f"reference-n{n}-N",
            method="N",
            nbase=n,
            order=order,
            seed_label=f"n{n}-shape-d100mm",
            target="reference",
        ),
        "exact reference N case",
    )
    for key in ("label", "role", "case", "old_certificate", "old_gates", "state_sha256", "context"):
        _same(row[key], old[key], "original manifest state: " + key)
    for new, previous in (
        ("original_seed", "seed"),
        ("original_geometry_report", "geometry_report"),
        ("original_geometry_report_index", "geometry_report_index"),
    ):
        _same(row[new], old[previous], "original state source: " + new)
    seed = reader.read(row["original_seed"])
    names = _names(n, order)
    _same(seed["names"], names, "original canonical names")
    _same(row["names"], names, "frozen canonical names")
    _same(seed["nbase"], n, "seed class")
    _same(seed["order"], order, "seed order")
    _same(seed["nfp"], 2, "seed field periods")
    _same(seed["parameter_orientation"], "alpha=-2*pi*t", "original orientation")
    coefficients = seed["base_coefficients"]
    _need(
        len(coefficients) == n
        and all(len(c) == 3 and all(len(a) == 2 * order + 1 for a in c) for c in coefficients),
        "full seed coefficient shape",
    )
    seed_x = _flatten(coefficients)
    _bits(seed_x)
    _need(
        len(row["x"]) == len(names) and _state_hash(names, row["x"]) == row["state_sha256"],
        "complete named state hash",
    )
    for k, x in enumerate(row["x"]):
        if k % (2 * order + 1) >= 5:
            _need(_bits([x]) == _bits([seed_x[k]]), "unchanged inactive coefficient bits")
    _need(len(seed["physical"]) == 4 * n, "all physical copies")
    for i, physical in enumerate(seed["physical"]):
        _need(set(physical) == {"base_index", "period", "flip", "matrix"}, "physical copy schema")
        _same(
            [physical["base_index"], physical["period"], physical["flip"]],
            [i % n, i // (2 * n), bool(i // n % 2)],
            "physical copy mapping",
        )
        matrix = physical["matrix"]
        _need(
            type(matrix) is list
            and len(matrix) == 3
            and all(type(r) is list and len(r) == 3 for r in matrix),
            "physical matrix shape",
        )
        _bits([x for r in matrix for x in r])
    proof = reader.read(row["old_certificate"])
    for key, value in dict(
        case=case,
        original_seed=row["original_seed"],
        geometry_report=row["original_geometry_report"],
        geometry_report_index=row["original_geometry_report_index"],
        state_sha256=row["state_sha256"],
        x=row["x"],
    ).items():
        _same(proof[key], value, "old certificate: " + key)
    gates = proof["result"]["gates"]
    _need(
        type(gates) is dict
        and set(gates) == GATES
        and all(type(v) is bool for v in gates.values()),
        "exact eight old geometry gates",
    )
    _same(gates, row["old_gates"], "retained original gates")
    _need(all(v for k, v in gates.items() if k != "curvature"), "seven original gates")
    control = row["manifest_index"] in (2, 4)
    _need(
        gates["curvature"] is control and row["field_evaluated"] is control,
        "original control/proposal distinction",
    )
    _need(
        proof["result"]["calculation_complete"] is True and proof["result"]["certified"] is control,
        "completed retained old certificate",
    )
    context = reader.read(row["context"])
    original = context["original_context"]
    _same(context["case"], case, "context case")
    _same(original["case"], case, "original case")
    _same(original["seed"], seed, "original seed instead of candidate")
    _same(original["seed_reference"], row["original_seed"], "original seed reference")
    _same(sources["seeds"][case["seed_label"]]["snapshot"], row["original_seed"], "archived seed")
    _same(original["target_sources"], sources["targets"]["reference"], "archived reference target")
    input_data = reader.read(original["target_sources"]["input"])
    reader.read(original["target_sources"]["wout"], json_data=False)
    _same(
        original["geometry_audit_reference"],
        row["original_geometry_report"],
        "old report reference",
    )
    _same(original["geometry_report_index"], 3 if n == 6 else 9, "old geometry report index")
    geometry = reader.read(row["original_geometry_report"])
    _same(
        geometry["sets"][original["geometry_report_index"]],
        original["geometry_report"],
        "original geometry report row",
    )
    _need(original["geometry_report"]["geometry_pass"] is True, "original admitted geometry")
    bundle = reader.read(row["control_bundle"])
    snapshot = reader.read(row["control_snapshot"])
    _same(bundle["snapshot"], row["control_snapshot"], "control snapshot reference")
    _same(row["control_bundle"], context["coarse"]["selected_bundle"], "saved control bundle")
    _same(bundle["state"], context["selected"]["state"], "saved control state")
    _same(snapshot, context["selected"]["snapshot"], "saved control snapshot")
    _same(snapshot["names"], names, "control names")
    _need(
        _bits(_flatten(snapshot["base_coefficients"])) == _bits(bundle["state"]["x"]),
        "control snapshot coordinate bits",
    )
    _same(
        [{k: v for k, v in p.items() if k != "current"} for p in snapshot["physical"]],
        seed["physical"],
        "control actual physical matrices",
    )
    _same(row["control_scale"], snapshot["scale"], "historical control scale")
    _same(
        row["control_physical_currents"],
        [p["current"] for p in snapshot["physical"]],
        "historical control currents",
    )
    _need(row["control_current_is_proposal_current"] is False, "no invented proposal current")
    _same(row["field_bundle"], row["control_bundle"] if control else None, "observed fields only")
    if control:
        _same(bundle["state"]["x"], row["x"], "control state bits")
        _same(bundle["certificate"], row["old_certificate"], "control certificate")
    reader.read(bundle["arrays"], json_data=False)
    _geometry(row, old, seed, study, reader)
    return dict(
        row=row,
        case=case,
        seed=seed,
        x=row["x"],
        names=names,
        input_data=input_data,
        original_context=original,
        control_bundle=bundle,
        control_snapshot=snapshot,
        control_bundle_reference=row["control_bundle"],
        control_snapshot_reference=row["control_snapshot"],
        source_references=dict(
            seed=row["original_seed"],
            geometry=row["original_geometry_report"],
            target=original["target_sources"],
            historical_seed=original["historical_seed_reference"],
        ),
    )


def _armijo(pair, control, proposal, reader):
    """Reconstruct registered P, displacement normalization and exact saved search RHS."""
    search = reader.read(pair["search_report"])
    _same(pair["case"], control["case"], "Armijo case")
    _same(proposal["case"], control["case"], "paired proposal case")
    _same(
        [pair["control_manifest_index"], pair["proposal_manifest_index"]],
        [control["row"]["manifest_index"], proposal["row"]["manifest_index"]],
        "Armijo manifest pair",
    )
    j = 94 if control["case"]["nbase"] == 6 else 50
    previous, trial = search["trials"][j - 1 : j + 1]
    _same(pair["predecessor_trial_index"], j - 1, "fixed predecessor trial")
    _same(pair["proposal_trial_index"], j, "fixed proposed trial")
    _same(pair["predecessor"], previous, "complete original predecessor record")
    _same(pair["proposal"], trial, "complete original proposal record")
    _same(
        [previous["index"], trial["index"], trial["parent_index"]],
        [j - 1, j, j - 1],
        "immediate saved predecessor",
    )
    _need(
        previous["accepted"] is True
        and trial["accepted"] is False
        and trial["evaluation"] is None
        and trial["current_pass"] is None
        and trial["armijo_pass"] is None
        and trial["reason"] == "geometry-rejected",
        "unevaluated original rejected proposal",
    )
    _same(
        [trial["iteration"], trial["backtrack"]],
        [17 if j == 94 else 12, 0],
        "fixed rejected iteration",
    )
    _same(previous["iteration"] + 1, trial["iteration"], "next saved iteration")
    _same(previous["counters_after"], trial["counters_before"], "adjacent saved counters")
    _same(search["selected_index"], j - 1, "saved selected predecessor")
    _same(search["accepted_indices"][-1], j - 1, "last accepted saved predecessor")
    _same(previous["x"], control["x"], "predecessor coordinates")
    _same(trial["x"], proposal["x"], "proposal coordinates")
    for saved, context in ((previous, control), (trial, proposal)):
        _same(
            saved["certificate"]["certificate_reference"],
            context["row"]["old_certificate"],
            "original trial certificate binding",
        )
    original = previous["evaluation"]
    _same(original, search["selected"], "saved original search scalar/vector")
    _same(original["x"], control["control_bundle"]["state"]["x"], "bundle/search coordinates")
    _same(
        original["gradient"],
        control["control_bundle"]["state"]["gradient"],
        "bundle/search gradient",
    )
    gradient, direction = original["gradient"], trial["direction"]
    _bits(gradient)
    _bits(direction)
    _need(len(gradient) == len(direction) == len(control["names"]), "full Armijo vectors")
    width = 2 * control["case"]["order"] + 1
    modes = [0 if k % width == 0 else (k % width + 1) // 2 for k in range(len(gradient))]
    raw = [
        -g / (1 + m * m) ** 2 if m <= 2 else -0.0 * g for g, m in zip(gradient, modes, strict=True)
    ]
    axes = [
        abs(raw[k]) + sum(math.hypot(raw[k + m], raw[k + m + 1]) for m in range(1, width, 2))
        for k in range(0, len(raw), width)
    ]
    bound = max(
        math.hypot(math.hypot(*axes[k : k + 2]), axes[k + 2]) for k in range(0, len(axes), 3)
    )
    _need(math.isfinite(bound) and bound > 0, "finite descending displacement normalization")
    for actual, value, mode in zip(direction, raw, modes, strict=True):
        _need(
            math.isclose(actual, value / bound, rel_tol=5e-12, abs_tol=1e-12)
            and (mode <= 2 or actual == 0),
            "registered preconditioned direction",
        )
    slope = math.fsum(g * d for g, d in zip(gradient, direction, strict=True))
    saved_slope = trial["directional_derivative"]
    _need(
        type(saved_slope) is float
        and math.isfinite(saved_slope)
        and saved_slope < 0
        and math.isclose(slope, saved_slope, rel_tol=5e-12, abs_tol=1e-12),
        "saved directional slope",
    )
    _same(trial["alpha"], 0.001, "first registered backtracking step")
    seed_x = _flatten(control["seed"]["base_coefficients"])
    expected = [
        x + trial["alpha"] * d if m <= 2 else seed_x[k]
        for k, (x, d, m) in enumerate(zip(original["x"], direction, modes, strict=True))
    ]
    _need(_bits(expected) == _bits(proposal["x"]), "exact active/inactive proposal update")
    rhs = original["value"] + 1e-4 * trial["alpha"] * saved_slope
    _need(_bits([rhs]) == _bits([trial["armijo_rhs"]]), "exact original search Armijo RHS")
    for key, value in dict(
        predecessor_objective=original["value"],
        predecessor_gradient=gradient,
        direction=direction,
        alpha=trial["alpha"],
        armijo_constant=1e-4,
        saved_directional_derivative=saved_slope,
        armijo_rhs=trial["armijo_rhs"],
        predecessor_bundle=control["control_bundle_reference"],
        predecessor_snapshot=control["control_snapshot_reference"],
    ).items():
        _same(pair[key], value, "frozen Armijo context: " + key)
    return dict(
        case=control["case"],
        original=pair,
        original_search_objective=original["value"],
        saved_armijo_rhs=trial["armijo_rhs"],
        reconstructed_slope=slope,
        reconstructed_rhs=rhs,
        exact_proposal_bits=True,
        immediate_predecessor=True,
    )


def _archive(root):
    from protected_fine_inputs import archive

    return archive(root)


def intake(root=ROOT, *, guard=lambda: None, native_admission=False):
    """Return private JSON-only states and separately recorded optional current admission.

    The caller owns clean-commit/qualification/execution gates and phase clocks.
    Any malformed file, source drift or guard failure prevents a successful return.
    """
    _need(type(native_admission) is bool and callable(guard), "typed intake options")
    root = Path(root).resolve()
    reader = _Reader(guard)
    try:
        registration, manifest = _registration(root, reader)
        geometry = reader.read(manifest["geometry_evidence"])
        _need(
            geometry["status"] == "completed" and geometry["geometry_component_pass"] is True,
            "completed geometry evidence",
        )
        _same(geometry["references"]["study"], manifest["geometry_study"], "geometry study source")
        _same(
            geometry["references"]["execution"],
            manifest["geometry_execution"],
            "geometry execution",
        )
        study = reader.read(manifest["geometry_study"])
        execution = reader.read(manifest["geometry_execution"])
        _need(
            type(execution["exit_code"]) is int
            and execution["exit_code"] == 0
            and study["complete"] is True
            and study["source_unchanged"] is True,
            "explicit complete unchanged geometry study",
        )
        _same(
            execution["explicit_return"]["returned_index"],
            manifest["geometry_study"],
            "explicit study return",
        )
        _same(study["source_before"], study["source_after"], "stable geometry sources")
        for key, reference in manifest["geometry_reviews"].items():
            _same(geometry["references"][key], reference, "geometry review reference")
            review = reader.read(reference)
            _need(
                review.get("status") == "scoped-pass"
                if key == "main_saved_review"
                else review.get("review_pass") is True,
                "successful retained geometry review",
            )
        original_manifest = reader.read(manifest["original_manifest"])
        for row in manifest["states"]:
            result = geometry["states"][row["manifest_index"]]
            for key in ("label", "state_sha256"):
                _same(result[key], row[key], "geometry result evidence state: " + key)
            _same(result["index"], row["manifest_index"], "geometry result evidence index")
            _need(
                result["complete"] is True and result["new_local_geometry_pass"] is True,
                "successful result evidence state",
            )
            for phase in ("producer", "audit"):
                recorded = result["phases"][phase]
                _need(
                    recorded["complete"] is True
                    and recorded["curvature_pass"] is True
                    and recorded["local_geometry_pass"] is True,
                    "successful geometry evidence phase",
                )
                _same(
                    recorded["counts"]["curves"],
                    4 * row["case"]["nbase"],
                    "geometry evidence copy count",
                )
        archived = reader.read(manifest["archived_coarse"]["source_before"])
        _same(
            archived,
            reader.read(manifest["archived_coarse"]["source_after"]),
            "archived source unchanged",
        )
        native = archived["physics_sources"]["native_sources"]
        sources = native["cell_sources"]
        for key, value in (("native_inputs", native), ("cell_inputs", sources)):
            _same(
                hashlib.sha256(_encode(value)).hexdigest(),
                manifest["archived_coarse"][key + "_canonical_sha256"],
                "archived canonical input hash",
            )
        states = [
            _state(row, original_manifest["states"][index], sources, study, reader)
            for row, index in zip(manifest["states"], INDICES, strict=True)
        ]
        _need(len(manifest["pairs"]) == 2, "two fixed pair contexts")
        pairs = [
            _armijo(pair, states[2 * i], states[2 * i + 1], reader)
            for i, pair in enumerate(manifest["pairs"])
        ]
        current = None
        if native_admission:
            guard()
            current = _archive(root)
            guard()
            _same(current["archived_source"], archived, "fresh admission preserves original source")
            for key in ("source_before", "source_after", "evidence"):
                _same(
                    current[key],
                    manifest["archived_coarse"][key],
                    "fresh admission archived " + key,
                )
            _need(
                current["fine_execution_authorized"] is False
                and current["physical_admission"] is False
                and current["step4_pass"] is False,
                "additive admission, not execution permission",
            )
        for reference in list(reader.checked.values()):
            reader.read(reference, json_data=False)
        guard()
        return copy.deepcopy(
            dict(
                schema_version=1,
                kind="fixed-field-probe-input-contexts",
                registration=registration,
                manifest=manifest,
                states=states,
                pairs=pairs,
                archived_source=archived,
                cell_sources=sources,
                current_admission=current,
                metadata_identity=dict(
                    references=sorted(reader.checked.values(), key=lambda r: r["path"]),
                    registered_checked_references=294,
                    physical_copies=112,
                    numerical_recomputations=0,
                ),
                **SCOPE,
            )
        )
    except (KeyError, IndexError, TypeError, OverflowError, RecursionError) as exc:
        raise ValueError("malformed fixed-field-probe metadata: " + type(exc).__name__) from exc
