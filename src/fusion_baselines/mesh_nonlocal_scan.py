"""Bounded streaming narrow phase with immutable witnesses and explicit partial coverage."""

import gzip
import json
import time
from pathlib import Path

import numpy as np

from fusion_baselines.provenance import sha256_file, write_json_atomic
from fusion_baselines.tetra_broad_phase import TetraBroadPhase
from fusion_baselines.tetra_nonoverlap import interior_witness, separation_witness


def reference(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path))


def scan(points, cells, tags, directory, *, max_seconds=1200, max_sat_pairs=2000000):
    directory = Path(directory)
    if directory.exists():
        raise FileExistsError("new immutable mesh scan directory required")
    if (not np.isfinite(max_seconds) or max_seconds <= 0 or type(max_sat_pairs) is not int
            or max_sat_pairs < 1):
        raise ValueError("positive fixed work/time caps required")
    tags = np.asarray(tags)
    if tags.shape != (len(cells),) or not np.issubdtype(tags.dtype, np.integer):
        raise ValueError("one integer physical tag per tetrahedron required")
    directory.mkdir(parents=True)
    started, tree, last_save = time.monotonic(), None, 0.
    report = dict(status="running", complete=False, nonlocal_screen_pass=False,
                  processed_candidates=0, shared_vertex_pairs=0, sat_calls=0, lp_calls=0,
                  separated_pairs=0, positive_interior_pairs=0, unresolved_pairs=0,
                  narrow_errors=0, positive_within_tag=0, positive_between_tags=0,
                  caps=dict(seconds=max_seconds, sat_pairs=max_sat_pairs),
                  mechanical_validity_certified=False, directed_interval_certificate=False)
    witness_path = directory / "witnesses.jsonl.gz"

    def checkpoint():
        report["elapsed_seconds"] = time.monotonic()-started
        if tree is not None:
            report["broad_phase"] = dict(
                finished=tree.finished, pairs_accounted=tree.pairs_accounted,
                candidates_delivered=tree.candidate_count,
                box_separated_pairs=tree.box_separated_pairs, nodes=len(tree.nodes),
                events=len(tree.events), total_pairs=len(cells)*(len(cells)-1)//2)
        write_json_atomic(directory / "summary.json", report)

    try:
        tree = TetraBroadPhase(points, cells, leaf_size=16)
        with gzip.open(witness_path, "xt", encoding="utf-8") as stream:
            stop = False
            for batch in tree.candidates():
                for i, j in batch:
                    if time.monotonic()-started >= max_seconds:
                        report.update(status="time_cap", stop_reason="registered_time_cap")
                        stop = True
                        break
                    if np.any(cells[i, :, None] == cells[j, None, :]):
                        report["shared_vertex_pairs"] += 1
                        report["processed_candidates"] += 1
                        continue
                    if report["sat_calls"] >= max_sat_pairs:
                        report.update(status="pair_cap", stop_reason="registered_sat_pair_cap")
                        stop = True
                        break
                    row = dict(pair=[int(i), int(j)])
                    report["sat_calls"] += 1
                    try:
                        first, second = points[cells[i]], points[cells[j]]
                        w = separation_witness(first, second)
                        row["separation"] = w
                        if w["status"] == "separated":
                            report["separated_pairs"] += 1
                        else:
                            report["lp_calls"] += 1
                            inside = interior_witness(first, second)
                            row["interior"] = inside
                            if inside["status"] == "positive_interior_witness":
                                report["positive_interior_pairs"] += 1
                                key = "positive_within_tag" if tags[i] == tags[j] else (
                                    "positive_between_tags")
                                report[key] += 1
                            else:
                                report["unresolved_pairs"] += 1
                    except Exception as error:
                        report["narrow_errors"] += 1
                        row["error"] = f"{type(error).__name__}: {error}"
                        report.update(status="error", error=row["error"])
                        stop = True
                    stream.write(json.dumps(row, allow_nan=False, separators=(",", ":"))+"\n")
                    report["processed_candidates"] += 1
                    if stop:
                        break
                if time.monotonic()-last_save >= 2:
                    stream.flush()
                    checkpoint()
                    last_save = time.monotonic()
                if stop:
                    break
        if time.monotonic()-started >= max_seconds and report["status"] == "running":
            report.update(status="time_cap", stop_reason="registered_time_cap")
        complete = (tree.finished and report["processed_candidates"] == tree.candidate_count
                    and report["status"] == "running")
        if complete:
            report.update(status="completed", complete=True, nonlocal_screen_pass=not any(
                report[k] for k in ("positive_interior_pairs", "unresolved_pairs",
                                    "narrow_errors")))
    except Exception as error:
        report.update(status="error", complete=False, nonlocal_screen_pass=False,
                      error=f"{type(error).__name__}: {error}")
    finally:
        if tree is not None:
            path = directory / "partition.json.gz"
            with gzip.open(path, "xt", encoding="utf-8") as stream:
                json.dump(dict(indices=tree.indices.tolist(), nodes=tree.nodes, events=tree.events,
                               padding=tree.padding), stream, allow_nan=False,
                          default=lambda value: value.tolist(), separators=(",", ":"))
            report["partition"] = reference(path)
        if witness_path.exists():
            report["witnesses"] = reference(witness_path)
        if report["status"] == "completed" and time.monotonic()-started >= max_seconds:
            report.update(status="time_cap", stop_reason="registered_time_cap",
                          complete=False, nonlocal_screen_pass=False)
        checkpoint()
    return report
