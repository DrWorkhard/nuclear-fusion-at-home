"""Read-only, dependency-free export of existing normalized fitter records."""

import hashlib
import math
import os
import re
from pathlib import Path

from fusion_public.data import canonical, loads, require

FORMAT = "fusion-coil-trajectory-v1"
TRIAL = re.compile(r"trial-(\d+)(-attempt)?\.json$")
ROLES = {"startup-seed", "probe", "startup-repeat", "search"}
UNITS = dict(normal_rms="1", normal_max="1", lengths="m", kappa_max="1/m",
             coil_distance="m", surface_distance="m", current="A", unit_flux="Wb",
             scale="1", min_b="T", area_mean_b="T", parameter_mean_b="T", area_bn_rms="T")


def _vector(value, count):
    require(isinstance(value, list) and len(value) == count, "named vector length mismatch")
    require(all(type(x) in (int, float) and math.isfinite(x) for x in value),
            "finite numeric coordinates required")
    return value


def _sources(values):
    """Keep exact identities without making original machine paths artifact locations."""
    return [dict(label=path.replace("\\", "/").rsplit("/", 1)[-1], sha256=digest,
                 original_path_sha256=hashlib.sha256(path.encode("utf-8")).hexdigest())
            for path, digest in sorted(values.items())]


def export(run, output, artifact_base=None, max_bytes=64*1024**2):
    """Export a closed run; retain a .partial file on failure and never overwrite."""
    run, output = Path(run), Path(output)
    require(type(max_bytes) is int and 0 < max_bytes <= 256*1024**2, "output cap in (0,256MiB]")
    require(not output.exists() and not output.is_symlink(), "fresh output required")
    sources, size = {}, 0

    def read(name, optional=False):
        path = run/name
        if optional and not path.exists() and not path.is_symlink():
            return None
        require(path.is_file() and not path.is_symlink(), "regular source file required")
        with path.open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        value = loads(raw)
        require(isinstance(value, dict), "object record required")
        digest = hashlib.sha256(raw).hexdigest()
        require(name not in sources or sources[name]["sha256"] == digest,
                "source changed during export")
        sources[name] = dict(sha256=digest,
                             uri=None if artifact_base is None
                             else artifact_base.rstrip("/")+"/"+name)
        return value

    seed, inputs = read("seed.json"), read("inputs.json")
    require(type(seed.get("nbase")) is int and seed["nbase"] == 6
            and type(seed.get("order")) is int and seed["order"] in (5, 8)
            and type(seed.get("nfp")) is int and seed["nfp"] == 2, "six/order5 or order8 nfp2 seed")
    require(inputs.get("kind") == "normalized-coil-fit", "normalized fitter inputs required")
    order = seed["order"]
    names = [f"coil[{i}]/{axis}{kind}({mode})" for i in range(6) for axis in "xyz"
             for kind, mode in [("c", 0)]+[(k, m) for m in range(1, order+1) for k in "sc"]]
    require(seed.get("names") == names, "canonical named coordinates required")
    coefficients = seed.get("base_coefficients", [])
    require(len(coefficients) == 6 and all(len(row) == 3 for row in coefficients)
            and all(len(axis) == 2*order+1 for row in coefficients for axis in row),
            "seed coefficient shape mismatch")
    _vector([x for row in coefficients for axis in row for x in axis], len(names))
    search, result = read("search.json", True), read("result.json", True)
    paths = sorted(p.name for p in run.iterdir() if TRIAL.fullmatch(p.name))
    for name in paths:
        read(name)  # Bind trajectory identity to every attempt and terminal file.
    provenance = inputs.get("provenance", {})
    repository, host = provenance.get("repository", {}), provenance.get("host", {})
    # A content identity, not an assertion that repeats of the same seed are independent runs.
    run_id = hashlib.sha256(canonical({k: v["sha256"] for k, v in sources.items()})).hexdigest()
    selected = None if search is None else search.get("selected")
    if selected is not None:
        require(type(selected.get("index")) is int, "selected integer index required")
    if search is not None and result is not None:
        require(result.get("search") == search, "result/search identity mismatch")
    header = dict(format=FORMAT, type="run", run_id=run_id, trajectory_id=run_id,
                  parent_seed_sha256=sources["seed.json"]["sha256"], task_id=None,
                  coefficient_names=names, coefficient_unit="m", order=order,
                  conventions=dict(nfp=seed.get("nfp"), parameter="t in [0,1)",
                                   cartesian_axes=["x", "y", "z"],
                                   physical_copies=seed.get("physical")),
                  target={k: seed.get(k) for k in ("target_id", "target_flux", "B2_scale")},
                  target_units=dict(target_flux="Wb", B2_scale="T^2"),
                  portable_target=inputs.get("portable_target"),
                  producer={k: repository.get(k) for k in ("commit", "dirty", "branch")},
                  environment={k: host.get(k) for k in ("python", "platform", "machine")},
                  source_hashes=_sources(inputs.get("sources_before", {})),
                  solver_options=inputs.get("solver_options"),
                  budgets={k: inputs.get(k) for k in ("search_seconds", "check_seconds")},
                  constraints=None, objective_weights=None,
                  search_summary=None if search is None else {
                      k: search.get(k) for k in ("status", "startup_pass", "startup_s", "search_s",
                                                "bundles_attempted", "bundles_completed")},
                  metric_units=UNITS, search_resolution=None,
                  missing="null means not recorded; no accepted-iterate history",
                  physical_admission=False)
    grouped = {}
    for name in paths:
        match = TRIAL.fullmatch(name)
        index, attempt = int(match[1]), bool(match[2])
        require(attempt not in grouped.setdefault(index, {}), "duplicate trial index")
        grouped[index][attempt] = name
    require(grouped, "at least one trial required")
    counts = dict(completed=0, failed=0, incomplete=0)
    partial = output.with_name(output.name+".partial")
    with partial.open("xb") as stream:
        def write(row):
            nonlocal size
            payload = canonical(row)+b"\n"
            require(size+len(payload) <= max_bytes, "export output ceiling; partial retained")
            stream.write(payload)
            size += len(payload)

        write(header)
        for index, files in sorted(grouped.items()):
            attempt = read(files[True]) if True in files else None
            terminal = read(files[False]) if False in files else None
            row = terminal if terminal is not None else attempt
            require(type(row.get("index")) is int and row["index"] == index, "trial index mismatch")
            require(row.get("role") in ROLES, "known evaluation role required")
            x = _vector(row.get("x"), len(names))
            if attempt is not None:
                require(attempt.get("status") == "attempted", "attempt status mismatch")
                require(all(attempt.get(k) == row.get(k) for k in ("index", "role", "x")),
                        "attempt/terminal identity mismatch")
            status = row.get("status")
            require(status in ("attempted", "completed", "failed"), "known trial status required")
            require(terminal is None or status != "attempted", "terminal status required")
            state = "incomplete" if terminal is None else status
            counts[state] += 1
            gradient = row.get("gradient")
            if status == "completed":
                _vector(gradient, len(names))
                require(type(row.get("value")) in (int, float), "completed objective required")
                require(isinstance(row.get("metrics"), dict), "completed metrics required")
            if selected is not None and selected.get("index") == index:
                require(status == "completed" and all(selected.get(k) == row.get(k)
                        for k in ("x", "role", "value", "gradient", "metrics")),
                        "selected candidate must match completed terminal record")
            metrics = row.get("metrics")
            scale = None if metrics is None else metrics.get("scale")
            identity = hashlib.sha256(canonical(dict(seed_sha256=header["parent_seed_sha256"],
                                      names=names, x=x,
                                      target=header["target"], scale=scale))).hexdigest()
            write(dict(format=FORMAT, type="evaluation", run_id=run_id, index=index,
                       candidate_id=identity, role=row["role"], evaluation_status=state,
                       solver_step_status="unknown", elapsed_s=None, coefficients=x,
                       gradient=gradient, objective=row.get("value"), metrics=metrics,
                       error=row.get("error"), rejection_value=row.get("rejected_value"),
                       selected=None if search is None else
                       selected is not None and selected.get("index") == index,
                       verification_status="not_evaluated", physical_admission=False))
        if selected is not None:
            require(selected.get("index") in grouped, "selected trial missing")
        # Final checks are not coarse search labels; attach only to the selected trial.
        if result is not None:
            write(dict(format=FORMAT, type="verification", run_id=run_id,
                       selected_index=None if selected is None else selected["index"],
                       recorded={k: result.get(k) for k in (
                           "completed", "error", "deadline_met", "step4_pass", "fine", "geometry",
                           "interior", "interior_refinements", "native_counts", "elapsed_s")},
                       evaluator={k: result.get("provenance", {}).get("repository", {}).get(k)
                                  for k in ("commit", "dirty")},
                       source_hashes=_sources(result.get("sources_after", {})),
                       physical_admission=result.get("physical_admission")))
        for name in sources:
            read(name)  # Bounded reread; rejects changed bytes or replaced symlinks.
        require(paths == sorted(p.name for p in run.iterdir() if TRIAL.fullmatch(p.name)),
                "trial inventory changed during export")
        write(dict(format=FORMAT, type="export_complete", run_id=run_id, counts=counts,
                   artifacts=sources, physical_admission=False))
    os.link(partial, output)  # Exclusive publication also protects against a racing writer.
    partial.unlink()
    return dict(run_id=run_id, counts=counts, bytes=size)
