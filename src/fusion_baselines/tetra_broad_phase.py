"""Deterministic bounding-box hierarchy with an explicit all-pair partition ledger."""

import numpy as np


class TetraBroadPhase:
    def __init__(self, points, cells, *, leaf_size=16, relative_padding=1e-10):
        points, cells = np.asarray(points, dtype=float), np.asarray(cells)
        if (points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all()
                or cells.ndim != 2 or cells.shape[1] != 4 or len(cells) < 1
                or not np.issubdtype(cells.dtype, np.integer)
                or cells.min() < 0 or cells.max() >= len(points)):
            raise ValueError("finite3D points and valid tetrahedral connectivity required")
        if (type(leaf_size) is not int or leaf_size < 1 or not np.isfinite(relative_padding)
                or relative_padding < 0):
            raise ValueError("positive leaf size and nonnegative finite padding required")
        xyz = points[cells]
        self.lower, self.upper = xyz.min(axis=1), xyz.max(axis=1)
        self.centers = self.lower + 0.5 * (self.upper - self.lower)
        self.padding = (relative_padding * max(1, float(np.max(np.ptp(points, axis=0))))
                        + 64 * np.finfo(float).eps * max(1, float(np.max(abs(points)))))
        if not np.isfinite(self.centers).all() or not np.isfinite(self.padding):
            raise ValueError("finite representable bounding boxes required")
        self.indices = np.arange(len(cells), dtype=np.int64)
        self.nodes, self.events = [], []
        self.pairs_accounted = self.candidate_count = self.box_separated_pairs = 0
        self.finished = self.started = False

        def build(lo, hi):
            ids = self.indices[lo:hi]
            index = len(self.nodes)
            node = dict(lo=lo, hi=hi, lower=self.lower[ids].min(axis=0),
                        upper=self.upper[ids].max(axis=0), children=None)
            self.nodes.append(node)
            if hi - lo > leaf_size:
                axis = int(np.argmax(np.ptp(self.centers[ids], axis=0)))
                order = np.lexsort((ids, self.centers[ids, axis]))
                self.indices[lo:hi] = ids[order]
                mid = (lo + hi) // 2
                node["children"] = (build(lo, mid), build(mid, hi))
            return index

        build(0, len(cells))

    def candidates(self):
        """Yield small canonical pair arrays; consume fully before claiming coverage."""
        if self.started:
            raise ValueError("one traversal per immutable partition ledger")
        self.started = True
        stack = [(0, 0)]
        while stack:
            ia, ib = stack.pop()
            a, b = self.nodes[ia], self.nodes[ib]
            na, nb = a["hi"] - a["lo"], b["hi"] - b["lo"]
            count = na * (na - 1) // 2 if ia == ib else na * nb
            event = dict(a=ia, b=ib, pairs=count)
            gaps = np.maximum(b["lower"] - a["upper"], a["lower"] - b["upper"])
            axis = int(np.argmax(gaps))
            if ia != ib and gaps[axis] > self.padding:
                self.box_separated_pairs += count
                self.pairs_accounted += count
                event.update(kind="box_separated", axis=axis, gap=float(gaps[axis]))
            elif ia == ib and a["children"] is not None:
                left, right = a["children"]
                stack.extend(((right, right), (left, right), (left, left)))
                event["kind"] = "self_split"
            elif a["children"] is None and b["children"] is None:
                ai, bi = self.indices[a["lo"]:a["hi"]], self.indices[b["lo"]:b["hi"]]
                if ia == ib:
                    i, j = np.triu_indices(na, 1)
                    pairs = np.column_stack((ai[i], ai[j]))
                else:
                    pairs = np.column_stack((np.repeat(ai, nb), np.tile(bi, na)))
                pairs.sort(axis=1)
                if len(pairs):
                    i, j = pairs.T
                    pair_gaps = np.maximum(self.lower[j] - self.upper[i],
                                           self.lower[i] - self.upper[j]).max(axis=1)
                    keep = pair_gaps <= self.padding
                    candidates = pairs[keep]
                else:
                    candidates = pairs
                self.pairs_accounted += count
                self.box_separated_pairs += count - len(candidates)
                self.candidate_count += len(candidates)
                event.update(kind="leaf", candidates=len(candidates),
                             box_separated=count - len(candidates))
                self.events.append(event)
                if len(candidates):
                    yield candidates
                continue
            elif a["children"] is not None and (b["children"] is None or na >= nb):
                left, right = a["children"]
                stack.extend(((right, ib), (left, ib)))
                event["kind"] = "split_a"
            else:
                left, right = b["children"]
                stack.extend(((ia, right), (ia, left)))
                event["kind"] = "split_b"
            self.events.append(event)
        n = len(self.indices)
        if self.pairs_accounted != n * (n - 1) // 2:
            raise ValueError("all-pair partition incomplete")
        self.finished = True
