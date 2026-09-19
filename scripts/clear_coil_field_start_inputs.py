"""Source admission for field starts from the two immutable clear geometries.

No field or equilibrium evaluation. Positive geometry/resource gates and negative
historical decisions are bound separately; a scalar overall flag is insufficient.
"""

import importlib.util
import json
import subprocess
from pathlib import Path

import block_native_reference_inputs as block_inputs
import clear_coil_initialization_inputs as geometry_inputs
import numpy as np
from current_diagnostic_inputs import reference
from run_jac_scaled_study import require_committed

from fusion_baselines.clear_coil_field_audit import archived_target, physical_cases
from fusion_baselines.clear_coil_geometry_audit import cases as geometry_cases
from fusion_baselines.provenance import git_state, sha256_file

PROTOCOL = "docs/optimization/CLEAR_COIL_FIELD_START_PROTOCOL.md"
CODE = (
    "scripts/clear_coil_field_start_inputs.py",
    "scripts/run_clear_coil_field_start.py",
    "scripts/audit_clear_coil_field_start.py",
    "tests/test_clear_coil_field_start_inputs.py",
    "tests/test_clear_coil_field_start_workflow.py",
    "tests/test_clear_coil_field_start_audit.py",
)
GEOMETRY_AUDIT = "evidence/clear-coil-initialization-v1-audit.json"
GEOMETRY_HASH = "b068fd6a6c76e8b4aaf57341e5a2ae139be196f35defacc644f1d5c890c0ea49"
GEOMETRY_RUN_HASH = "5f3f5b86e3a80101491a70475fbbbdcdee6138754873463a1c63f0545b45a309"
BLOCK_AUDIT = "evidence/block-native-reference-v1-audit.json"
BLOCK_HASH = "5070d7df72e54edf4433df72af193f611c5605286895aebeb442d09d1e620f65"
BLOCK_RUN = "evidence/block-native-reference-v1-resource.json"
BLOCK_RUN_HASH = "8f6f37e90d2e76705727899753f369b242cb48c14a7fc2328f2beba6b511bece"
PRIMITIVES = "evidence/clear-coil-field-start-v1-primitives.json"
SEED_HASHES = {
    "n6-shape-d100mm": "90fe6f84395d319d45ac39fab832a2b3908f0d16d7638e971e2a4602a3ef65d1",
    "n8-shape-d100mm": "4f21695154190b15ea946212a5acc90c1d8d50827bec7292e247b009400bf859",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same(actual, expected):
    """JSON identity including bool/int/float distinctions, without coercion."""
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return set(actual) == set(expected) and all(same(actual[k], v) for k, v in expected.items())
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            same(a, b) for a, b in zip(actual, expected, strict=True)
        )
    return actual == expected


def checked(ref):
    require(
        isinstance(ref, dict)
        and set(ref) in ({"path", "sha256"}, {"path", "sha256", "bytes"})
        and type(ref.get("path")) is str
        and Path(ref["path"]).is_absolute()
        and type(ref.get("sha256")) is str
        and len(ref["sha256"]) == 64
        and all(c in "0123456789abcdef" for c in ref["sha256"]),
        "absolute complete immutable reference",
    )
    path = Path(ref["path"])
    require(sha256_file(path) == ref["sha256"], f"source bytes changed: {path}")
    if "bytes" in ref:
        require(
            type(ref["bytes"]) is int and path.stat().st_size == ref["bytes"],
            "exact reference byte count",
        )
    return path


def bind_tree(value, seen=None, expanded=None, *, expand_json=True):
    """Bind raw graphs transitively; existing source binders own historical ancestry.

    Every embedded source reference is still hashed. Opening arbitrary historical
    source reports would incorrectly require older code versions at today's paths.
    Only the current raw evidence graphs are recursively opened here.
    """
    seen = {} if seen is None else seen
    expanded = set() if expanded is None else expanded
    if isinstance(value, dict):
        if "path" in value and "sha256" in value:
            path = checked(value)
            old = seen.get(str(path))
            require(old is None or old == value["sha256"], "conflicting reference aliases")
            seen[str(path)] = value["sha256"]
            if expand_json and path.suffix == ".json" and str(path) not in expanded:
                expanded.add(str(path))
                bind_tree(json.loads(path.read_text()), seen, expanded, expand_json=True)
        else:
            for key, child in value.items():
                bind_tree(
                    child,
                    seen,
                    expanded,
                    expand_json=(
                        expand_json and key not in ("source", "source_before", "source_after")
                    ),
                )
    elif isinstance(value, list):
        for child in value:
            bind_tree(child, seen, expanded, expand_json=expand_json)
    return seen


def read(ref):
    return json.loads(checked(ref).read_text())


def historical(root, name, commit, digest=None):
    path = root / name
    require_committed(root, path)
    ref = reference(path)
    require(digest is None or ref["sha256"] == digest, "fixed historical evidence hash")
    previous = subprocess.check_output(["git", "show", f"{commit}:{name}"], cwd=root)
    require(path.read_bytes() == previous, "fixed historical evidence bytes")
    return ref


def geometry_gate(audit, run, source):
    required = (
        "all_pass",
        "all_twelve_sets_checked",
        "arithmetic_and_source_pass",
        "both_classes_pass",
        "geometry_pass",
    )
    require(
        audit.get("status") == "completed"
        and audit.get("phase") == "geometry_initialization"
        and all(audit.get(k) is True for k in required)
        and same(audit.get("source"), source)
        and same(run.get("source"), source)
        and run.get("status") == "completed"
        and run.get("geometry_pass") is False
        and run.get("selected") is None
        and len(audit.get("sets", [])) == len(run.get("sets", [])) == 12
        and run.get("attempted_lps") == 168
        and type(run.get("attempted_lps")) is int
        and audit.get("work", {}).get("attempted_lps") == 168
        and audit["work"].get("original_lps") == audit["work"].get("repeated_lps") == 84,
        "complete independently accepted12-set/168-LP geometry prerequisite",
    )
    for record in (audit, run, audit["work"]):
        for key in ("field_calls", "gradient_calls", "equilibrium_solves"):
            require(type(record.get(key)) is int and record[key] == 0, "geometry-only work")
        for key in ("field_pass", "transfer_pass", "step4_pass"):
            require(record.get(key) is False, "no magnetic admission from geometry")
    require(
        same(audit.get("selected"), dict(n6="n6-shape-d100mm", n8="n8-shape-d100mm"))
        and len(audit.get("surface_checks", [])) == 6
        and all(r.get("passed") is True for r in audit["surface_checks"]),
        "both preselected shaped100mm classes and six checked surfaces",
    )
    selected = {}
    for i, (report, row, case) in enumerate(
        zip(audit["sets"], run["sets"], geometry_cases(), strict=True)
    ):
        require(
            same(report.get("case"), case)
            and same(row.get("case"), case)
            and report.get("geometry_pass") is True
            and report.get("available_geometry") is True
            and len(report.get("coils", [])) == case["nbase"]
            and len(report.get("distances", [])) == 6
            and np.isfinite(report.get("analytic_coil_lower", np.nan))
            and report["analytic_coil_lower"] >= 0.06,
            "individual ordered geometry admission and coil separation",
        )
        for j, coil in enumerate(report["coils"]):
            require(
                type(coil.get("base_index")) is int
                and coil["base_index"] == j
                and coil.get("available_geometry") is True
                and coil.get("exact_repeat") is True
                and len(coil.get("lp_certificates", [])) == 2
                and all(
                    c.get("solved") is True and c.get("passed") is True
                    for c in coil["lp_certificates"]
                )
                and all(
                    coil.get("export_transfer", {}).get(k) is True
                    for k in (
                        "support_pass",
                        "length_pass",
                        "curvature_pass",
                        "plasma_pass",
                        "controlled_projection_self_disjoint",
                    )
                ),
                "individual LP/repeat/export/continuous geometry gates",
            )
        require(
            all(
                all(
                    d.get(k) is True
                    for k in (
                        "coil_pass",
                        "plasma_pass",
                        "sampled_length_pass",
                        "sampled_curvature_pass",
                    )
                )
                for d in report["distances"]
            ),
            "every independent direct geometry grid required",
        )
        if case["label"] in audit["selected"].values():
            ref = row.get("snapshot", {})
            require(ref.get("sha256") == SEED_HASHES[case["label"]], "exact selected seed hash")
            selected[case["label"]] = dict(case=case, snapshot=ref, geometry_report_index=i)
    require(set(selected) == set(SEED_HASHES), "two exact selected geometry snapshots")
    return selected


def block_gate(audit, run, binding):
    require(
        audit.get("status") == "completed"
        and audit.get("arithmetic_and_source_pass") is True
        and audit.get("bounded_reference_pass") is True
        and audit.get("all_pass") is True
        and audit.get("legacy_all_pass") is False
        and audit.get("legacy_sparse_pass") is True
        and same(audit.get("source"), run.get("source_before"))
        and same(run.get("source_before"), run.get("source_after"))
        and same(
            {k: v for k, v in binding.items() if k != "repository"},
            {k: v for k, v in audit["source"].items() if k != "repository"},
        )
        and run.get("producer_checks_pass") is True
        and run.get("bounded_reference_pass") is False,
        "positive separate bounded reference with unchanged numerical sources and old negative",
    )
    require(
        len(audit.get("workers", [])) == 4
        and [w.get("case") for w in audit["workers"]] == block_inputs.matrix()
        and all(
            all(
                w.get(k) is True
                for k in (
                    "passed",
                    "mathematical_pass",
                    "resource_pass",
                    "changed_copies_pass",
                )
            )
            and w.get("state_count") == 13
            and w.get("kernels", {}).get("passed") is True
            and w.get("repetitions") == [True, True, True]
            and len(w.get("finite_differences", [])) == 8
            and all(d.get("passed") is True for d in w["finite_differences"])
            for w in audit["workers"]
        ),
        "all four independently accepted bounded workers and their individual gates",
    )
    require(
        audit.get("compared_quantities") == 336
        and len(audit.get("comparisons", [])) == 8
        and all(
            p.get("passed") is True
            and len(p.get("comparisons", [])) == 42
            and all(c.get("passed") is True for c in p["comparisons"])
            for p in audit["comparisons"]
        ),
        "all336 comparisons to both unchanged backends",
    )
    old = audit.get("legacy_workers", [])
    require(
        len(old) == 8
        and [w.get("case") for w in old] == block_inputs.legacy.matrix()
        and all(w.get("mathematical_pass") is True for w in old)
        and {w["case"]["label"] for w in old if w.get("resource_pass") is not True}
        == block_inputs.DENSE_FAILURES
        and all(w.get("passed") is True for w in old if w["case"]["backend"] == "sparse")
        and len(audit.get("legacy_pairs", [])) == 4
        and all(p.get("passed") is True for p in audit["legacy_pairs"]),
        "all old mathematics and Sparse passes, exact three retained Dense failures",
    )
    for key in ("field_calls", "target_data_reads", "equilibrium_solves"):
        require(type(audit.get(key)) is int and audit[key] == 0, "synthetic resource-only work")
    for key in (
        "startup_pass",
        "physical_seed_pass",
        "search_allowed",
        "transfer_pass",
        "step4_pass",
    ):
        require(audit.get(key) is False, "resource result not magnetic admission")


def prerequisites(root):
    """Read-only predecessor checks, also callable before new workflow code exists."""
    root = Path(root).resolve()
    geometry_ref = historical(root, GEOMETRY_AUDIT, "323cfdd", GEOMETRY_HASH)
    geometry_audit = read(geometry_ref)
    geometry_run_ref = geometry_audit["run"]
    require(geometry_run_ref["sha256"] == GEOMETRY_RUN_HASH, "original geometric run identity")
    geometry_run = read(geometry_run_ref)
    geometry_source = geometry_inputs.sources(root)
    seeds = geometry_gate(geometry_audit, geometry_run, geometry_source)
    bind_tree(geometry_audit)
    bind_tree(geometry_run)
    for label, seed in seeds.items():
        snapshot = read(seed["snapshot"])
        require(
            same(snapshot["sources"], geometry_source["targets"])
            and same(snapshot["case"], seed["case"])
            and snapshot["case"]["label"] == label,
            "original currentless snapshot and exact targets",
        )
    block_ref = historical(root, BLOCK_AUDIT, "1b6f6b1", BLOCK_HASH)
    block_run_copy = historical(root, BLOCK_RUN, "1b6f6b1", BLOCK_RUN_HASH)
    block_audit, block_run = read(block_ref), read(block_run_copy)
    require(
        checked(block_audit["run"]).read_bytes() == checked(block_run_copy).read_bytes(),
        "byte-identical original bounded-reference run",
    )
    block_source = block_inputs.sources(root)
    block_gate(block_audit, block_run, block_source)
    bind_tree(block_audit)
    bind_tree(block_run)
    primitive_ref = historical(root, PRIMITIVES, "a5a007c")
    primitives = read(primitive_ref)
    require(
        same(
            {k: primitives.get(k) for k in ("tests", "failures", "errors", "skipped")},
            dict(tests=1335, failures=0, errors=0, skipped=0),
        ),
        "original full field-primitives qualification",
    )
    primitive_sources = []
    for row in primitives["sources"]:
        ref = reference(root / row["path"])
        require(ref["sha256"] == row["sha256"], "qualified field-primitives bytes unchanged")
        primitive_sources.append(ref)
    primitive_junit = dict(primitives["junit"], path=str(root / primitives["junit"]["path"]))
    checked(primitive_junit)
    pilot = geometry_source["pilot"]
    normalization = {}
    for label in ("reference", "selected"):
        archives = [r for r in pilot["target_archives"][label]["fields"] if r["n"] == 64]
        loaded = []
        for row in archives:
            with np.load(checked(row["arrays"]), allow_pickle=False) as data:
                loaded.append(
                    dict(
                        s=row["s"], n=row["n"], arrays={key: data[key].copy() for key in data.files}
                    )
                )
        scale = archived_target(loaded, 64)["B2_scale"]
        normalization[label] = dict(B2_scale=scale, archives=archives)
    # Bind installed native Python implementations as well as the old checkout;
    # this is a narrow explicit source check, not a universal transitive ABI proof.
    spec = importlib.util.find_spec("simsopt")
    require(spec is not None and spec.origin is not None, "installed native package required")
    installed = Path(spec.origin).parent
    native = []
    for ref in pilot["native"]:
        path = checked(ref)
        if path.suffix == ".py":
            relative = path.relative_to(root / "external/simsopt/src/simsopt")
            active = installed / relative
            require(
                active.read_bytes() == path.read_bytes(), "installed native Python source differs"
            )
            native.append(reference(active))
    return dict(
        geometry=dict(
            run=geometry_run_ref,
            audit=geometry_ref,
            source=geometry_source,
            selected=geometry_audit["selected"],
        ),
        bounded_reference=dict(
            run=block_audit["run"], audit=block_ref, source=block_run["source_before"]
        ),
        primitives_qualification=primitive_ref,
        primitives_junit=primitive_junit,
        primitive_sources=primitive_sources,
        targets=pilot["targets"],
        target_archives=pilot["target_archives"],
        seeds=seeds,
        normalization=normalization,
        native_installed=native,
        matrix=physical_cases(),
    )


def sources(root):
    root = Path(root).resolve()
    bound = prerequisites(root)
    for name in (PROTOCOL, *CODE):
        require_committed(root, root / name)
    return dict(
        **bound,
        protocol=reference(root / PROTOCOL),
        code=[reference(root / name) for name in CODE],
        repository=git_state(root),
    )
