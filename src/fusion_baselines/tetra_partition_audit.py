"""Independent box-tree certificate audit; never calls the production traversal."""

import numpy as np


def audit_partition(points, cells, indices, nodes, events, padding, *, visit=None):
    points, cells, indices = np.asarray(points), np.asarray(cells), np.asarray(indices)
    if (points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all()
            or cells.ndim != 2 or cells.shape[1] != 4 or not len(cells)
            or not np.issubdtype(cells.dtype, np.integer) or cells.min() < 0
            or cells.max() >= len(points) or indices.shape != (len(cells),)
            or not np.issubdtype(indices.dtype, np.integer)
            or not np.array_equal(np.sort(indices), np.arange(len(cells)))):
        raise ValueError("valid original mesh and complete element permutation required")
    expected_pad = (1e-10 * max(1, float(np.max(points.max(axis=0)-points.min(axis=0))))
                    + 64*np.finfo(float).eps * max(1, float(abs(points).max())))
    if padding != expected_pad or not nodes:
        raise ValueError("fixed original-geometry padding and nonempty tree required")
    seen, stack = set(), [0]
    lower, upper = np.min(points[cells], axis=1), np.max(points[cells], axis=1)
    while stack:
        i = stack.pop()
        if type(i) is not int or i in seen or i < 0 or i >= len(nodes):
            raise ValueError("tree nodes must form one acyclic partition")
        seen.add(i)
        node = nodes[i]
        lo, hi = node["lo"], node["hi"]
        if type(lo) is not int or type(hi) is not int or not 0 <= lo < hi <= len(cells):
            raise ValueError("valid contiguous node span required")
        ids = indices[lo:hi]
        if (not np.array_equal(node["lower"], lower[ids].min(axis=0))
                or not np.array_equal(node["upper"], upper[ids].max(axis=0))):
            raise ValueError("node bounds must enclose exactly its original vertices")
        children = node["children"]
        if children is None:
            if hi-lo > 16:
                raise ValueError("registered maximum leaf size16 required")
        else:
            if (len(children) != 2 or any(type(c) is not int or c < 0 or c >= len(nodes)
                                         for c in children)):
                raise ValueError("two valid children required")
            a, b = [nodes[c] for c in children]
            if (a["lo"], a["hi"], b["lo"], b["hi"]) != (lo, (lo+hi)//2, (lo+hi)//2, hi):
                raise ValueError("children must exactly partition the parent span")
            stack.extend(children)
    if len(seen) != len(nodes) or (nodes[0]["lo"], nodes[0]["hi"]) != (0, len(cells)):
        raise ValueError("one complete root partition required")

    # A set of unresolved disjoint pair-subsets, not a reconstruction of producer stack order.
    pending = {(0, 0)}
    covered = separated = candidate_count = 0
    for event in events:
        ia, ib = event["a"], event["b"]
        key = tuple(sorted((ia, ib)))
        if key not in pending:
            raise ValueError("duplicate, unreachable or already resolved pair event")
        pending.remove(key)
        a, b = nodes[ia], nodes[ib]
        na, nb = a["hi"]-a["lo"], b["hi"]-b["lo"]
        count = na*(na-1)//2 if ia == ib else na*nb
        if event["pairs"] != count:
            raise ValueError("event pair cardinality mismatch")
        if ia != ib and not (a["hi"] <= b["lo"] or b["hi"] <= a["lo"]):
            raise ValueError("distinct pair nodes must be disjoint")
        kind = event["kind"]
        if kind == "box_separated":
            axis = event["axis"]
            if ia == ib or axis not in (0, 1, 2):
                raise ValueError("distinct nodes and coordinate witness required")
            gap = max(b["lower"][axis]-a["upper"][axis], a["lower"][axis]-b["upper"][axis])
            if not gap > padding or gap != event["gap"]:
                raise ValueError("strict original-vertex box gap required")
            separated += count
            covered += count
        elif kind == "leaf":
            if a["children"] is not None or b["children"] is not None:
                raise ValueError("exhaustive leaf event must contain leaves")
            candidates = []
            for ii in range(a["lo"], a["hi"]):
                for jj in range(b["lo"], b["hi"]):
                    if ia == ib and ii >= jj:
                        continue
                    i, j = int(indices[ii]), int(indices[jj])
                    gap = max(max(lower[j, k]-upper[i, k], lower[i, k]-upper[j, k])
                              for k in range(3))
                    if gap <= padding:
                        candidates.append((min(i, j), max(i, j)))
            if (event["candidates"] != len(candidates)
                    or event["box_separated"] != count-len(candidates)):
                raise ValueError("exhaustive original-vertex leaf candidates mismatch")
            separated += count-len(candidates)
            candidate_count += len(candidates)
            covered += count
            if visit is not None and candidates:
                visit(np.asarray(candidates, dtype=np.int64))
        else:
            if kind == "self_split" and ia == ib and a["children"] is not None:
                left, right = a["children"]
                parts = [(left, left), (left, right), (right, right)]
            elif kind == "split_a" and ia != ib and a["children"] is not None:
                parts = [(child, ib) for child in a["children"]]
            elif kind == "split_b" and ia != ib and b["children"] is not None:
                parts = [(ia, child) for child in b["children"]]
            else:
                raise ValueError("invalid disjoint-pair subdivision")
            for part in parts:
                canonical = tuple(sorted(part))
                if canonical in pending:
                    raise ValueError("overlapping frontier partitions")
                pending.add(canonical)
    total = len(cells)*(len(cells)-1)//2
    remaining = sum((nodes[a]["hi"]-nodes[a]["lo"])*(nodes[b]["hi"]-nodes[b]["lo"])
                    if a != b else (nodes[a]["hi"]-nodes[a]["lo"])*(
                        nodes[a]["hi"]-nodes[a]["lo"]-1)//2 for a, b in pending)
    if covered+remaining != total or separated+candidate_count != covered:
        raise ValueError("full pair-partition accounting mismatch")
    return dict(complete=not pending, total_pairs=total, covered_pairs=covered,
                remaining_pairs=remaining, candidate_count=candidate_count,
                box_separated_pairs=separated, nodes=len(nodes), events=len(events))
