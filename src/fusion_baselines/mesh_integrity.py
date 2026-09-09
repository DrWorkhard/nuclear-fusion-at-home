"""Intrinsic tetrahedral mesh screens; deliberately not a spatial collision test."""

import numpy as np

EDGES = np.array([[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3]])
FACES = np.array([[1, 2, 3], [0, 3, 2], [0, 1, 3], [0, 2, 1]])


def _connected_components(edges):
    vertices, inverse = np.unique(edges, return_inverse=True)
    parent = np.arange(len(vertices))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for a, b in inverse.reshape(-1, 2):
        a, b = find(a), find(b)
        if a != b:
            parent[a] = b
    return len({find(i) for i in range(len(vertices))})


def boundary_topology(cells):
    faces = cells[:, FACES].reshape(-1, 3)
    inversions = np.sum(
        np.stack(
            [
                faces[:, 0] > faces[:, 1],
                faces[:, 0] > faces[:, 2],
                faces[:, 1] > faces[:, 2],
            ]
        ),
        axis=0,
    )
    parity = 1 - 2 * (inversions % 2)
    unique, inverse, count = np.unique(
        np.sort(faces, axis=1), axis=0, return_inverse=True, return_counts=True
    )
    orientation_sum = np.bincount(inverse, weights=parity)
    bad_orientation = int(np.count_nonzero((count == 2) & (orientation_sum != 0)))
    boundary = unique[count == 1]
    if len(boundary):
        edges, edge_counts = np.unique(
            np.sort(boundary[:, [[0, 1], [1, 2], [0, 2]]].reshape(-1, 2), axis=1),
            axis=0,
            return_counts=True,
        )
        vertex_count = len(np.unique(boundary))
        edge_count = len(edges)
        bad_edges = int(np.count_nonzero(edge_counts != 2))
        components = _connected_components(edges)
    else:
        vertex_count = edge_count = components = 0
        bad_edges = 0
    nonmanifold_faces = int(np.count_nonzero(count > 2))
    euler = vertex_count - edge_count + len(boundary)
    return {
        "nonmanifold_faces": nonmanifold_faces,
        "inconsistent_internal_face_orientations": bad_orientation,
        "boundary_triangles": len(boundary),
        "boundary_vertices": vertex_count,
        "boundary_edges": edge_count,
        "boundary_edges_not_two_incident": bad_edges,
        "boundary_components": components,
        "boundary_euler_characteristic": euler,
        "closed_ring_screen_pass": nonmanifold_faces == 0
        and bad_orientation == 0
        and bad_edges == 0
        and components == 1
        and euler == 0,
    }


def audit_tetrahedra(points, cells, tags):
    points, cells, tags = np.asarray(points, dtype=float), np.asarray(cells), np.asarray(tags)
    if points.ndim != 2 or points.shape[1] != 3 or not np.all(np.isfinite(points)):
        raise ValueError("expected finite 3D points")
    if cells.ndim != 2 or cells.shape[1] != 4 or len(cells) == 0:
        raise ValueError("expected nonempty tetrahedral connectivity")
    if (
        not np.issubdtype(cells.dtype, np.integer)
        or np.any(cells < 0)
        or np.any(cells >= len(points))
    ):
        raise ValueError("connectivity must be integer and in range")
    if tags.shape != (len(cells),) or not np.issubdtype(tags.dtype, np.integer):
        raise ValueError("one integer physical tag required per tetrahedron")
    sorted_cells = np.sort(cells, axis=1)
    repeated = int(np.count_nonzero(np.any(np.diff(sorted_cells, axis=1) == 0, axis=1)))
    duplicates = len(cells) - len(np.unique(sorted_cells, axis=0))
    xyz = points[cells]
    determinant = np.linalg.det(
        np.stack(
            [
                xyz[:, 1] - xyz[:, 0],
                xyz[:, 2] - xyz[:, 0],
                xyz[:, 3] - xyz[:, 0],
            ],
            axis=2,
        )
    )
    squared_edges = np.sum((xyz[:, EDGES[:, 1]] - xyz[:, EDGES[:, 0]]) ** 2, axis=(1, 2))
    quality = np.divide(
        12 * (np.abs(determinant) / 2) ** (2 / 3),
        squared_edges,
        out=np.zeros(len(cells)),
        where=squared_edges > 0,
    )
    span = float(np.max(np.ptp(points, axis=0)))
    tolerance = 1e-12 * span**3
    per_tag = {str(int(tag)): boundary_topology(cells[tags == tag]) for tag in np.unique(tags)}
    checks = {
        "distinct_tetra_vertices": repeated == 0,
        "no_duplicate_tetrahedra": duplicates == 0,
        "positive_nondegenerate_tetrahedra": bool(np.all(determinant > tolerance)),
        "minimum_mean_ratio_at_least_0_10": bool(np.min(quality) >= 0.1),
        "four_positive_physical_tags": len(per_tag) == 4 and bool(np.all(tags > 0)),
        "every_boundary_passes_closed_ring_screen": all(
            value["closed_ring_screen_pass"] for value in per_tag.values()
        ),
    }
    return {
        "points": len(points),
        "tetrahedra": len(cells),
        "repeated_vertex_tetrahedra": repeated,
        "duplicate_tetrahedra": duplicates,
        "minimum_signed_determinant": float(determinant.min()),
        "signed_determinant_tolerance": tolerance,
        "nonpositive_or_near_degenerate_tetrahedra": int(
            np.count_nonzero(determinant <= tolerance)
        ),
        "mean_ratio_quality": dict(
            zip(
                ["min", "p01", "median"], np.quantile(quality, [0, 0.01, 0.5]).tolist(), strict=True
            )
        ),
        "per_physical_tag": per_tag,
        "checks": checks,
        "pass": all(checks.values()),
        "spatial_nonoverlap_certified": False,
        "mechanical_validity_certified": False,
    }
