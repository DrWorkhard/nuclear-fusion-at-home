"""Recompute CoilStellaration field errors with this project's own checker (issue #75).

Preregistered in https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/75: ten
`tight` evaluation rows with two field periods and six coils per half-period, drawn with
numpy.random.default_rng(0) from that subset sorted by `requirements_id`. Each DESC coil
set (unique coils plus field-period and stellarator symmetry) and its ConStellaration
boundary are rebuilt; |B.n|/|B| is evaluated with the independent NumPy Biot-Savart sum
of `coupled_coil_audit`, on our 128 x 128 one-period boundary grid and, as a
reconstruction check, on the dataset's own DESC grid. Needs numpy, scipy and pyarrow in
a separate environment; only the parquet byte ranges holding the sampled rows are fetched.
"""

import argparse
import hashlib
import io
import json
import os
import shutil
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pyarrow.compute as pc
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fusion_baselines import coupled_coil_audit as audit  # noqa: E402
from fusion_baselines.boundary_control_metrics import boundary_metrics  # noqa: E402

COILS = "proxima-fusion/coilstellaration", "286a268c664938519af6ceacfb4ec8143f64e20e"
PLASMA = "proxima-fusion/constellaration", "8da71572eb63ce93e77ce89bec0d7c30b7eba89e"
EVAL = "results/eval-part-0.parquet", 16005157, (
    "5425524969d6ae7f844195e00bae0ec313228aadb27d905549791f6251695a37")
MEAN, MAX = "desc_metrics/normalized_field_error/mean", "desc_metrics/normalized_field_error/max"
MAX_BYTES, RESERVE = 3 * 10**9, 3 * 2**30
FETCHED = [0]


def need(condition, message):
    if not condition:
        raise SystemExit(f"stopped: {message}")


def url(source, path):
    return f"https://huggingface.co/datasets/{source[0]}/resolve/{source[1]}/{path}"


def open_url(address, headers):
    for attempt in range(5):
        try:
            return urllib.request.urlopen(urllib.request.Request(address, headers=headers),
                                          timeout=120)
        except urllib.error.HTTPError as error:
            if error.code not in (429, 500, 502, 503) or attempt == 4:
                raise
            time.sleep(30 * (attempt + 1))


def resolve(address):
    """One Hub request per file; byte ranges then go to the redirected storage URL."""
    response = open_url(address, {"Range": "bytes=0-0"})
    FETCHED[0] += len(response.read())
    return response.geturl()


def get(address, first=None, last=None):
    headers = {} if first is None else {"Range": f"bytes={first}-{last}"}
    data = open_url(address, headers).read()
    FETCHED[0] += len(data)
    need(FETCHED[0] <= MAX_BYTES, "3 GB download budget")
    need(first is None or len(data) == last - first + 1, "short range read")
    return data


class RangeFile(io.RawIOBase):
    """Seekable remote file for pyarrow, served from prefetched ranges where possible."""

    def __init__(self, address, size):
        self.address, self.size, self.pos, self.cache = address, size, 0, {}

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        self.pos = {0: offset, 1: self.pos + offset, 2: self.size + offset}[whence]
        return self.pos

    def prefetch(self, ranges):
        with ThreadPoolExecutor(8) as pool:
            blocks = pool.map(lambda r: get(self.address, r[0], r[0] + r[1] - 1), ranges)
            self.cache.update(zip((r[0] for r in ranges), blocks, strict=True))

    def read(self, n=-1):
        n = self.size - self.pos if n is None or n < 0 else min(n, self.size - self.pos)
        block = self.cache.get(self.pos)
        data = block[:n] if block is not None and len(block) >= n else (
            get(self.address, self.pos, self.pos + n - 1) if n > 0 else b"")
        self.pos += len(data)
        return data


def rows_by_id(source, path, size, id_column, value_column, wanted, positions=None):
    """Read only the row groups holding `wanted` ids.

    With `positions` (row numbers from an id_to_file_map listed in file order) the row
    group follows from the footer's row counts; otherwise all small id chunks are read.
    Every returned value is matched by its id in the row group actually read.
    """
    remote = RangeFile(resolve(url(source, path)), size)
    parquet = pq.ParquetFile(remote, pre_buffer=False)
    counts = [parquet.metadata.row_group(g).num_rows for g in range(parquet.num_row_groups)]
    if positions is not None:
        groups = {int(np.searchsorted(np.cumsum(counts), positions[key], side="right"))
                  for key in wanted}
    else:
        index = parquet.schema_arrow.get_field_index(id_column)
        ranges = []
        for group in range(parquet.num_row_groups):
            chunk = parquet.metadata.row_group(group).column(index)
            start = chunk.dictionary_page_offset if chunk.has_dictionary_page else (
                chunk.data_page_offset)
            ranges.append((start, chunk.total_compressed_size))
        remote.prefetch(ranges)
        groups = {group for group in range(parquet.num_row_groups) if wanted.intersection(
            parquet.read_row_group(group, columns=[id_column])[id_column].to_pylist())}
    found = {}
    for group in sorted(groups):
        table = parquet.read_row_group(group, columns=[id_column, value_column]).to_pydict()
        found.update((key, value) for key, value in zip(
            table[id_column], table[value_column], strict=True) if key in wanted)
    print(f"{path}: {len(found)}/{len(wanted)} rows from {len(groups)} row groups", flush=True)
    return found


def cached(folder, name, loader):
    path = folder / name
    if not path.exists():
        path.write_bytes(loader())
    return path.read_bytes()


def sample(eval_path):
    table = pq.read_table(eval_path)
    mask = pc.and_(pc.and_(pc.is_valid(table["desc_metrics_id"]),
                           pc.equal(table["boundary.n_field_periods"], 2)),
                   pc.and_(pc.equal(table["reqs/n_coils_per_half_period"], 6),
                           pc.equal(table["benchmark/stratification"], "tight")))
    subset = table.filter(mask).sort_by("requirements_id")
    chosen = np.random.default_rng(0).choice(subset.num_rows, size=10, replace=False)
    return subset.num_rows, [subset.slice(int(i), 1).to_pylist()[0] for i in chosen]


def physical_coils(document, nodes):
    """DESC [sin N..sin 1, const, cos 1..cos N] unique coils to all physical copies."""
    nfp, unique = int(document["n_field_periods"]), len(document["currents"])
    need(document["is_stellarator_symmetric"] and nfp == 2 and unique == 6, "coil class")
    desc = np.stack([np.asarray(document[f"coil_{axis}_n"], float) for axis in "xyz"], 1)
    order = (desc.shape[-1] - 1) // 2
    ours = np.empty_like(desc)
    ours[..., 0] = desc[..., order]
    ours[..., 1::2] = desc[..., order - 1::-1]
    ours[..., 2::2] = desc[..., order + 1:]
    angle = np.pi / nfp
    axis = np.array([np.cos(angle), np.sin(angle), 0.0])
    half_turn = 2 * np.outer(axis, axis) - np.eye(3)
    currents = np.asarray(document["currents"], float)
    coefficients = np.concatenate((ours, np.einsum("ij,cjk->cik", half_turn, ours)))
    currents = np.concatenate((currents, -currents))
    rotated, signed = [], []
    for period in range(nfp):
        c, s = np.cos(2 * np.pi * period / nfp), np.sin(2 * np.pi * period / nfp)
        rotation = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
        rotated.append(np.einsum("ij,cjk->cik", rotation, coefficients))
        signed.append(currents)
    curves = audit.fourier_curves(np.concatenate(rotated), nodes)
    return curves, np.concatenate(signed), ours


def boundary_document(document):
    r_cos, z_sin = np.asarray(document["r_cos"]), np.asarray(document["z_sin"])
    need(document.get("r_sin") is None and document.get("z_cos") is None, "symmetric boundary")
    ntor = (r_cos.shape[1] - 1) // 2
    rows = {key: [dict(m=m, n=j - ntor, value=float(values[m, j]))
                  for m in range(values.shape[0]) for j in range(values.shape[1])]
            for key, values in (("rbc", r_cos), ("zbs", z_sin))}
    return dict(lasym=False, nfp=int(document["n_field_periods"]), mpol=r_cos.shape[0],
                ntor=ntor, **rows)


def ratio(points, normal, curves, currents):
    field, _ = audit.filament_field_and_potential(
        points.reshape(-1, 3), curves["positions"], curves["tangents"], currents)
    unit = (normal / np.linalg.norm(normal, axis=-1, keepdims=True)).reshape(-1, 3)
    return field, np.abs(np.sum(field * unit, axis=-1)) / np.linalg.norm(field, axis=-1)


def our_grid(boundary, curves, currents, shift):
    surface = audit.boundary(boundary, 128, 128, shift=shift)
    field, values = ratio(surface["points"], surface["normal"], curves, currents)
    metrics = boundary_metrics(field.reshape(128, 128, 3), surface["normal"])
    return dict(rms=metrics["normal_rms"], plain_mean=float(values.mean()),
                max=metrics["normal_max"])


def desc_grid(boundary, curves, currents):
    """DESC LinearGrid(M=80, N=80, NFP=2, sym=True): 81 midpoint theta in (0, pi) x 161."""
    theta, phi = np.meshgrid(2 * np.pi * (np.arange(81) + 0.5) / 162,
                             2 * np.pi * np.arange(161) / (161 * boundary["nfp"]),
                             indexing="ij")
    points, dtheta, dphi = audit._rz(boundary, theta, phi)
    _, values = ratio(points, np.cross(dphi, dtheta), curves, currents)
    return dict(mean=float(values.mean()), max=float(values.max()),
                min=float(values.min()), std=float(values.std()))


def relative(ours, theirs):
    return float(abs(ours / theirs - 1))


def evaluate(row, coil_text, boundary_text, nodes, refine):
    curves, currents, unique = physical_coils(json.loads(coil_text), nodes)
    boundary = boundary_document(json.loads(boundary_text))
    lengths = audit.fourier_curves(unique, 4096)["tangents"]
    lengths = np.linalg.norm(lengths, axis=-1).mean(axis=1)
    reference = desc_grid(boundary, curves, currents)
    result = dict(
        requirements_id=row["requirements_id"], desc_coilset_id=row["desc_coilset_id"],
        boundary_id=row["constellaration_boundary_id"],
        dataset=dict(mean=row[MEAN], max=row[MAX],
                     min=row["desc_metrics/normalized_field_error/min"],
                     std=row["desc_metrics/normalized_field_error/std"],
                     coil_length_mean=row["desc_metrics/coil_lengths/mean"],
                     coil_length_max=row["desc_metrics/coil_lengths/max"]),
        desc_grid=reference, coil_length_mean=float(lengths.mean()),
        coil_length_max=float(lengths.max()),
        ours=our_grid(boundary, curves, currents, False),
        ours_shift_half=our_grid(boundary, curves, currents, True))
    result["reconstruction"] = dict(
        mean=relative(reference["mean"], row[MEAN]), max=relative(reference["max"], row[MAX]),
        coil_length_mean=relative(result["coil_length_mean"], row[
            "desc_metrics/coil_lengths/mean"]))
    result["mapping_deviation"] = relative(result["ours"]["plain_mean"], row[MEAN])
    if refine:
        fine, fine_currents, _ = physical_coils(json.loads(coil_text), 2 * nodes)
        result["ours_double_coil_nodes"] = our_grid(boundary, fine, fine_currents, False)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--coil-nodes", type=int, default=512)
    args = parser.parse_args()
    need(all(os.environ.get(k) == "1" for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                                                "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS")),
         "one-thread execution required")
    inputs = args.output / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    need(shutil.disk_usage(args.output).free >= RESERVE, "3 GiB disk reserve")
    started = time.monotonic()
    eval_bytes = cached(inputs, "eval-part-0.parquet", lambda: get(url(COILS, EVAL[0])))
    need(hashlib.sha256(eval_bytes).hexdigest() == EVAL[2], "eval split hash")
    subset_size, rows = sample(inputs / "eval-part-0.parquet")
    coil_ids = {row["desc_coilset_id"] for row in rows}
    plasma_ids = {row["constellaration_boundary_id"] for row in rows}
    coil_text, boundary_text = {}, {}
    for key in coil_ids:
        if (inputs / f"coilset-{key}.json").exists():
            coil_text[key] = (inputs / f"coilset-{key}.json").read_text(encoding="utf-8")
    for key in plasma_ids:
        if (inputs / f"boundary-{key}.json").exists():
            boundary_text[key] = (inputs / f"boundary-{key}.json").read_text(encoding="utf-8")
    if coil_ids - coil_text.keys():
        index = pq.read_table(io.BytesIO(cached(inputs, "coilsets-id_to_file_map.parquet",
                                                lambda: get(url(COILS, "coilsets/"
                                                                "id_to_file_map.parquet")))))
        parts, positions, seen = {}, {}, {}
        for key, path in zip(index["id"].to_pylist(), index["path"].to_pylist(), strict=True):
            if key in coil_ids - coil_text.keys():
                parts.setdefault(path, set()).add(key)
                positions[key] = seen.get(path, 0)
            seen[path] = seen.get(path, 0) + 1
        sizes = json.loads(get(f"https://huggingface.co/api/datasets/{COILS[0]}/tree/"
                               f"{COILS[1]}/coilsets"))
        sizes = {row["path"]: row["size"] for row in sizes}
        for path, keys in sorted(parts.items()):
            coil_text.update(rows_by_id(COILS, path, sizes[path], "id", "json", keys, positions))
    if plasma_ids - boundary_text.keys():
        files = json.loads(get(f"https://huggingface.co/api/datasets/{PLASMA[0]}/tree/"
                               f"{PLASMA[1]}/data"))
        for row in files:
            missing = plasma_ids - boundary_text.keys()
            if missing:
                boundary_text.update(rows_by_id(PLASMA, row["path"], row["size"],
                                                "plasma_config_id", "boundary.json", missing))
    need(coil_ids <= coil_text.keys() and plasma_ids <= boundary_text.keys(), "all inputs found")
    for prefix, texts in (("coilset", coil_text), ("boundary", boundary_text)):
        for key, text in texts.items():
            (inputs / f"{prefix}-{key}.json").write_text(text, encoding="utf-8")
    report = dict(issue=75, coilstellaration_revision=COILS[1], constellaration_revision=PLASMA[1],
                  eval_sha256=EVAL[2], subset_size=subset_size, coil_nodes=args.coil_nodes,
                  numpy=np.__version__, sampled=[row["requirements_id"] for row in rows],
                  input_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sorted(inputs.iterdir())}, cases=[])
    for number, row in enumerate(rows):
        case = evaluate(row, coil_text[row["desc_coilset_id"]],
                        boundary_text[row["constellaration_boundary_id"]],
                        args.coil_nodes, refine=number == 0)
        report["cases"].append(case)
        print(json.dumps(dict(case=number, id=case["requirements_id"], ours=case["ours"],
                              reconstruction=case["reconstruction"])), flush=True)
        if number == 0:
            need(case["reconstruction"]["mean"] <= 0.01 and case["reconstruction"]["max"] <= 0.01,
                 "reconstruction differs from the dataset by more than 1% on the first case")
    ranked = sorted(report["cases"], key=lambda case: case["dataset"]["mean"])
    middle = [case["mapping_deviation"] for case in ranked[4:6]]
    mapping = all(value <= 0.05 for value in middle)
    above = all(case["ours"]["rms"] > 1e-3 for case in report["cases"])
    report.update(
        mapping_middle_deviations=middle, mapping_pass=mapping, all_rms_above_1e_3=above,
        outcome=("does not reach our limit under our own metric" if mapping and above else
                 "record the measured spread" if mapping else "mapping problem, no conclusion"),
        downloaded_bytes=FETCHED[0], seconds=time.monotonic() - started)
    (args.output / "report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("cases", "input_sha256")}))


if __name__ == "__main__":
    main()
