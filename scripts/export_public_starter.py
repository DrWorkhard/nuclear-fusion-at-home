"""Export a small, path-free derivative of already audited arrays; no field work.

Maintainer-only, requires the historical local artifacts and NumPy. Public users
never need this script, those artifacts, or the numerical research environment.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CASE = "clear-coil-samples-v1"
RUN = "evidence/clear-coil-field-start-v1-run.json"
RUN_SHA = "e4949a9be9518c9acaa727c3f6de238703028e9baca16bf89ec15bb145cb9714"
AUDIT = "evidence/clear-coil-field-start-v1-audit.json"
AUDIT_SHA = "e6fa7cda853cc2576f9660501043fc6f8c0d7121c1ce0a819df47544fd262fd8"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(ref):
    path = Path(ref["path"])
    if digest(path) != ref["sha256"]:
        raise ValueError("Changed historical input")
    return json.loads(path.read_text())


def export(output):
    output.mkdir(parents=True, exist_ok=False)
    run = read(dict(path=ROOT / RUN, sha256=RUN_SHA))
    audit = read(dict(path=ROOT / AUDIT, sha256=AUDIT_SHA))
    if audit["startup_pass"] is not True or audit["physical_seed_pass"] is not False:
        raise ValueError("Original numerical pass and physical failure required")
    cell = read(run["rows"][0])
    if cell["case"]["label"] != "reference-n6":
        raise ValueError("Fixed first reference-n6 cell required")
    worker = read(cell["worker"])
    row_ref = worker["qualification"]["N"][0]
    row = read(row_ref)
    snapshot = read(row["snapshot"])
    for source in snapshot["sources"].values():
        if digest(source["path"]) != source["sha256"]:
            raise ValueError("Changed historical equilibrium source")
    if digest(row["arrays"]["path"]) != row["arrays"]["sha256"]:
        raise ValueError("Changed archived arrays")
    with np.load(row["arrays"]["path"], allow_pickle=False) as archive:
        raw = {k: archive[k] for k in archive.files}
    candidate = dict(
        schema_version=1, case_id=CASE,
        coefficient_unit="m", parameter_names=snapshot["names"],
        base_coefficients=snapshot["base_coefficients"],
    )
    groups = {}
    for prefix in ("boundary", "inner", "loop"):
        size = len(raw[prefix + "_points"])
        indices = np.array([k * (size - 1) // 63 for k in range(64)])
        values = dict(
            original_count=size, indices=indices.tolist(),
            points_m=raw[prefix + "_points"][indices].tolist(),
            native_B_T=raw[prefix + "_B"][indices].tolist(),
            native_A_Tm=raw[prefix + "_A"][indices].tolist(),
        )
        if prefix == "boundary":
            values["unit_normals"] = raw["boundary_normals"][indices].tolist()
            values["weights"] = raw["boundary_weights"][indices].tolist()
        if prefix == "inner":
            values["target_B_T"] = raw["inner_target"][indices].tolist()
        groups[prefix] = values
    parents = dict(
        audited_run=RUN_SHA, independent_audit=AUDIT_SHA,
        seed_bundle=row_ref["sha256"], snapshot=row["snapshot"]["sha256"],
        raw_arrays=row["arrays"]["sha256"],
        equilibrium_input=snapshot["sources"]["input"]["sha256"],
        equilibrium_output=snapshot["sources"]["wout"]["sha256"],
    )
    packet = dict(
        schema_version=1, case_id=CASE, seed=candidate,
        nbase=6, order=5, nfp=2, physical=snapshot["physical"],
        B2_scale_T2=snapshot["B2_scale"], groups=groups,
        provenance=dict(
            historical_revision="3334f1e", historical_case="reference-n6",
            parent_sha256=parents, selection="floor(k*(N-1)/63), k=0..63, per group",
            derived_export=True, original_files_modified=False,
            source_dataset="https://doi.org/10.5281/zenodo.7220257",
            attribution="Goodman et al., Constructing precisely quasi-isodynamic magnetic fields",
            dataset_license="CC-BY-4.0",
            changes="Project n6/M5 coil construction; local401 vacuum solve; field sampling/subset",
        ),
    )
    for name, value in (("case.json", packet), ("candidate.json", candidate)):
        text = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        (output / name).write_text(text)
    manifest = dict(
        schema_version=1, case_id=CASE,
        files={name: digest(output / name) for name in ("case.json", "candidate.json")},
        description="Real n6/M5 seed: fixed-current sampled filament fields, not design admission",
    )
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True)+"\n")
    print(json.dumps(dict(output=str(output), files=manifest["files"], parent_sha256=parents)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    export(parser.parse_args().output.resolve())
