"""Stored period actions and physical metadata; no hidden well censoring."""

import json

import netCDF4
import numpy as np
from current_diagnostic_inputs import reference

from fusion_baselines.plasma_design import PITCHES, SURFACES, period_actions
from fusion_baselines.provenance import write_json_atomic
from fusion_baselines.qi_resolution import boundary_errors
from fusion_baselines.vmec_trace import trace_geometry


def measure(wout, folder, *, surfaces=SURFACES, pitches=PITCHES, nphi=801, nalpha=16, offset=0):
    folder.mkdir(parents=True, exist_ok=False)
    record = dict(
        wout=reference(wout),
        surfaces=list(surfaces),
        pitches=list(pitches),
        resolution=[nphi, nalpha, 2],
        offset=offset,
        traces=[],
        cells=[],
        errors=[],
        status="running",
    )
    try:
        for s in surfaces:
            try:
                trace = trace_geometry(wout, s, nphi, nalpha, 2, alpha_offset=offset)
            except Exception as exc:
                record["errors"].append(dict(s=s, error=f"{type(exc).__name__}: {exc}"))
                write_json_atomic(folder / "measurement.json", record)
                continue
            path = folder / f"s{s}.npz"
            with path.open("xb") as stream:
                np.savez_compressed(stream, **trace)
            record["traces"].append(dict(s=s, arrays=reference(path)))
            for q in pitches:
                try:
                    record["cells"].append(dict(s=s, q=q, **period_actions(trace, q)))
                except Exception as exc:
                    record["errors"].append(dict(s=s, q=q, error=f"{type(exc).__name__}: {exc}"))
            write_json_atomic(folder / "measurement.json", record)
        if record["errors"]:
            raise ValueError(
                "incomplete action domain; all requested cells attempted and failures retained"
            )
        record.update(
            status="completed", score=float(np.mean([c["score"] for c in record["cells"]]))
        )
    except Exception as exc:
        record.update(status="error", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        write_json_atomic(folder / "measurement.json", record)
    return record


def metadata(wout, input_path):
    with netCDF4.Dataset(wout) as ds:
        nfp, ns = int(ds["nfp"][...]), int(ds["ns"][...])
        grid = (np.arange(ns - 1) + 0.5) / (ns - 1)
        iota = np.interp(SURFACES, grid, ds["iotas"][1:])
        volume = float(ds["volume_p"][...])
        edge = float(ds["phi"][-1])
        effective = json.loads(input_path.read_text())
        errors = boundary_errors(ds, effective)
        if (
            nfp != 2
            or not np.isfinite(iota).all()
            or not np.isfinite(volume)
            or volume <= 0
            or abs(edge - effective["phiedge"]) > 1e-14
            or max(errors.values()) > 1e-12
        ):
            raise ValueError("physical input/output gate failed")
    return dict(
        volume=volume, iota=iota.tolist(), boundary_errors=errors, edge_flux=edge, nfp=nfp, ns=ns
    )


def geometry_guard(current, reference_state):
    return bool(
        abs(current["volume"] / reference_state["volume"] - 1) <= 0.01
        and np.max(abs(np.asarray(current["iota"]) - reference_state["iota"])) <= 0.02
    )
