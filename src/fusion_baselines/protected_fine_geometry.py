"""Fixed-candidate fine geometry composition; no magnetic/native calculations.

Source admission and acknowledged coarse selection belong to the caller. This
module preserves those supplied identities, hashes both source inputs, and uses
the frozen producer and independent mathematical checks without changing them.
Saved arrays use the separate, lossless mask codec and canonical numeric reader.
"""

import copy
import hashlib
import json
import re
from pathlib import Path

import numpy as np

from fusion_baselines import clear_coil_geometry_audit as geometry
from fusion_baselines import coil_perturbation_audit as mathematical
from fusion_baselines import coil_perturbation_direct_audit as direct
from fusion_baselines import coil_perturbation_samples as sampling
from fusion_baselines import protected_cell_contract as contract
from fusion_baselines import protected_fine_plan as plan
from fusion_baselines.protected_fine_geometry_codec import decode_geometry
from fusion_baselines.protected_run_snapshots import read_arrays
from fusion_baselines.protected_search_journal import _encode, _unique_object

TARGETS = ("reference", "selected")
SCOPE = dict.fromkeys(
    (
        "physical_admission",
        "absolute_field_geometry_pass",
        "fine_numerical_qualification",
        "resolved_fine_grid_improvement",
        "pareto_dominance",
        "realized_field_transfer",
        "step4_pass",
        "sota_advance",
        "ms1_reached",
    ),
    False,
)


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _same(actual, expected, message):
    _need(_encode(actual) == _encode(expected), message)


def _input(reference):
    contract._reference(reference)
    path = Path(reference["path"])
    _need(path.is_file() and not path.is_symlink(), "regular original surface input required")
    with path.open("rb") as stream:
        raw = stream.read(8 * 1024**2 + 1)
    _need(len(raw) <= 8 * 1024**2, "bounded original surface input required")
    _need(hashlib.sha256(raw).hexdigest() == reference["sha256"], "surface input bytes changed")
    value = json.loads(raw, object_pairs_hook=_unique_object)
    _encode(value)
    _need(type(value) is dict, "original Fourier surface object required")
    return value


def _context(context, archive):
    _need(
        type(context) is dict
        and set(context) == {"case", "original_context", "coarse", "selected"},
        "exact fine context required",
    )
    case, original, selected = (context[k] for k in ("case", "original_context", "selected"))
    plan.validate_case(case)
    contract.validate_context(original)
    _same(case, original["case"], "fine/original case identity")
    _need(
        type(selected) is dict and set(selected) == {"state", "snapshot", "arrays", "certificate"},
        "complete selected coarse bundle and certificate required",
    )
    x = plan._coordinates(case, selected["state"]["x"])
    contract.validate_bundle({k: selected[k] for k in ("state", "snapshot", "arrays")}, x, original)
    seed = original["seed"]
    targets = archive["archived_source"]["physics_sources"]["native_sources"]["cell_sources"][
        "targets"
    ]
    _same(targets, seed["sources"], "both original geometry target identities required")
    _need(type(targets) is dict and set(targets) == set(TARGETS), "both original targets required")
    proof = selected["certificate"]
    _need(
        type(proof) is dict
        and set(proof)
        == {
            "case",
            "phase",
            "operation_id",
            "x",
            "state_sha256",
            "original_seed",
            "geometry_report",
            "geometry_report_index",
            "result",
        },
        "complete selected cumulative certificate record required",
    )
    for key, expected in dict(
        case=case,
        x=x.tolist(),
        state_sha256=contract.coordinate_identity(original, x),
        original_seed=original["seed_reference"],
        geometry_report=original["geometry_audit_reference"],
        geometry_report_index=original["geometry_report_index"],
    ).items():
        _same(proof[key], expected, "selected certificate " + key)
    _need(
        type(proof["phase"]) is str
        and proof["phase"] in ("startup", "search-seed", "trial", "replay")
        and type(proof["operation_id"]) is str
        and re.fullmatch(
            re.escape(proof["phase"]) + r"/certificate/[0-9]{3}", proof["operation_id"]
        ),
        "original selected certificate operation identity",
    )
    _need(
        type(proof["result"]) is dict and proof["result"].get("certified") is True,
        "original selected coarse certificate must be positive",
    )
    return (
        copy.deepcopy(case),
        copy.deepcopy(original),
        x.reshape(np.shape(seed["base_coefficients"])),
        copy.deepcopy(targets),
        copy.deepcopy(proof["result"]),
    )


def _sum_work(first, second):
    return {
        kind: {key: first[kind][key] + second[kind][key] for key in first[kind]} for kind in first
    }


def expected_work(case):
    """Complete registered producer work, independently specified by the auditor."""
    plan.validate_case(case)
    total = sampling.empty_work()
    for level in plan.geometry_levels():
        total = _sum_work(total, direct.bounded_work(4 * case["nbase"], level["ncoil"]))
    return dict(
        surfaces=dict(attempted=2, completed=2),
        direct_grids=dict(attempted=4, completed=4),
        sampling=total,
    )


class FineGeometry:
    """Four ordered grids with private fixed inputs and fail-stop resource guards.

    ``sample`` returns fresh, unencoded raw arrays; the caller publishes them
    with encode_geometry before recording its own completed operation. Work
    counts describe sampling, not durable publication or independent acceptance.
    """

    def __init__(self, context, archive, guard):
        _need(callable(guard), "synchronous geometry guard required")
        self._guard = guard
        self._failed = False
        self._busy = True
        self._index = 0
        self._work = dict(
            surfaces=dict(attempted=0, completed=0), direct_grids=dict(attempted=0, completed=0)
        )
        self._sampler = None
        try:
            self._check()
            self._case, original, self._coefficients, targets, _ = _context(context, archive)
            points = {}
            for target in TARGETS:
                self._check()
                data = _input(targets[target]["input"])
                self._work["surfaces"]["attempted"] += 1
                points[target] = sampling.surface_points(data, 256, 256)
                self._check()
                _need(points[target].shape == (256**2, 3), "complete full-torus surface required")
                self._work["surfaces"]["completed"] += 1
            self._sampler = sampling.Sampler(original["seed"], points, check=self._check)
            self._check()
        except BaseException:
            self._failed = True
            raise
        finally:
            self._busy = False

    @property
    def failed(self):
        return self._failed

    def _healthy(self):
        if self._failed:
            raise RuntimeError("fine geometry failed; preserve evidence and do not retry")

    def _check(self):
        self._healthy()
        try:
            self._guard()
            self._healthy()
        except BaseException:
            self._failed = True
            raise

    def work(self):
        return dict(
            copy.deepcopy(self._work),
            sampling=(self._sampler.work() if self._sampler is not None else sampling.empty_work()),
        )

    def sample(self, coefficients, level):
        entered = False
        try:
            self._healthy()
            _need(not self._busy, "reentrant fine geometry sampling forbidden")
            self._busy = entered = True
            _need(self._index < 4, "all registered geometry grids already sampled")
            plan.validate_geometry_level(level)
            _same(level, plan.geometry_levels()[self._index], "exact next fine geometry grid")
            value = np.asarray(coefficients)
            _need(
                value.dtype == np.dtype(np.float64)
                and value.shape == self._coefficients.shape
                and value.tobytes() == self._coefficients.tobytes(),
                "fixed full selected geometry coordinate bits required",
            )
            self._check()
            self._work["direct_grids"]["attempted"] += 1
            before = self._sampler.work()
            raw = self._sampler.sample(self._coefficients.copy(), copy.deepcopy(level))
            self._check()
            expected = _sum_work(
                before, direct.bounded_work(4 * self._case["nbase"], level["ncoil"])
            )
            _same(self._sampler.work(), expected, "exact complete per-grid geometry sampling work")
            self._work["direct_grids"]["completed"] += 1
            self._index += 1
            return {key: value.copy(order="C") for key, value in raw.items()}
        except BaseException:
            self._failed = True
            raise
        finally:
            if entered:
                self._busy = False


def audit_geometry(context, archive, records, guard):
    """Independently reconstruct four explicitly supplied canonical saved grids.

    Each row is exactly {level, arrays, codec, sampling_work}. ``arrays`` is the
    canonical immutable NPZ reference and ``codec`` the inline mask descriptor.
    No producer sampling, source recapture, file discovery or field evaluation.
    Successful reconstruction and geometric qualification remain separate from
    full field/geometry acceptance. Caller supplies guarded, admitted context.
    """
    _need(callable(guard), "synchronous independent geometry guard required")
    guard()
    case, original, coefficients, targets, recorded_certificate = _context(context, archive)
    _need(type(records) is list and len(records) == 4, "all four saved geometry grids required")
    records = copy.deepcopy(records)
    certificate = mathematical.audit_certificate(
        original["seed"], original["geometry_report"], coefficients, recorded_certificate
    )
    guard()
    surfaces = {}
    for target in TARGETS:
        surfaces[target] = geometry.surface(_input(targets[target]["input"]), 256, 256, 0)["points"]
        _need(surfaces[target].shape == (256, 256, 3), "independent complete full-torus surface")
        guard()
    rows = []
    for record, level in zip(records, plan.geometry_levels(), strict=True):
        _need(
            type(record) is dict and set(record) == {"level", "arrays", "codec", "sampling_work"},
            "exact saved fine geometry record required",
        )
        _same(record["level"], level, "ordered saved fine geometry level")
        _same(
            record["sampling_work"],
            direct.bounded_work(4 * case["nbase"], level["ncoil"]),
            "exact recorded per-grid geometry sampling work",
        )
        guard()
        raw = decode_geometry(read_arrays(record["arrays"]), record["codec"], case, level)
        result = direct.audit_samples(
            original["seed"], coefficients, certificate, level, raw, surfaces
        )
        guard()
        sampled_pass = bool(
            raw["curvature_available"].all()
            and np.all(raw["lengths"] <= 3.5)
            and np.all(raw["curvature"] <= 12)
            and np.all(raw["pair_distances"] >= 0.06)
            and all(np.all(raw[f"cp_{target}_distances"] >= 0.08) for target in TARGETS)
        )
        rows.append(
            dict(level=copy.deepcopy(level), independent=result, sampled_geometry_pass=sampled_pass)
        )
    return dict(
        schema_version=1,
        kind="protected-fine-independent-geometry",
        case=case,
        geometry_consistency=True,
        continuous_geometry_pass=certificate["certified"],
        sampled_geometry_pass=all(row["sampled_geometry_pass"] for row in rows),
        certificate=certificate,
        grids=rows,
        producer_work=expected_work(case),
        independent_work=dict(
            certificate_recomputations=1, surface_reconstructions=2, direct_grids=4
        ),
        field_calls=0,
        gradient_calls=0,
        equilibrium_solves=0,
        **SCOPE,
    )
