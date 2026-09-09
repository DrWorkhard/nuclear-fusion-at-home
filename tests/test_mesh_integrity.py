import numpy as np
import pytest

from fusion_baselines.mesh_integrity import audit_tetrahedra, boundary_topology


def _regular():
    return np.array(
        [[0, 0, 0], [1, 0, 0], [0.5, np.sqrt(3) / 2, 0], [0.5, np.sqrt(3) / 6, np.sqrt(2 / 3)]]
    )


def test_regular_quality_and_bad_cells():
    points = _regular()
    result = audit_tetrahedra(points, [[0, 1, 2, 3]], [1])
    assert result["mean_ratio_quality"]["min"] == pytest.approx(1)
    assert result["checks"]["positive_nondegenerate_tetrahedra"]
    assert not result["pass"]  # A single solid tetrahedron is not four closed coil rings.
    for cells in [[[1, 0, 2, 3]], [[0, 1, 2, 2]]]:
        result = audit_tetrahedra(points, cells, [1])
        assert not result["checks"]["positive_nondegenerate_tetrahedra"]
    result = audit_tetrahedra(points, [[0, 1, 2, 3]] * 2, [1, 1])
    assert result["duplicate_tetrahedra"] == 1
    for cells in [[[0, 1, 2, 4]], [[0, 1, 2, -1]], [[0.0, 1.0, 2.0, 3.0]]]:
        with pytest.raises(ValueError, match="integer and in range"):
            audit_tetrahedra(points, cells, [1])


def test_shared_face_orientation_and_nonmanifold_detection():
    good = boundary_topology(np.array([[0, 1, 2, 3], [0, 2, 1, 4]]))
    assert good["inconsistent_internal_face_orientations"] == 0
    assert good["boundary_edges_not_two_incident"] == 0
    # Both positive tetrahedra on the same side of face 012, with distinct apex IDs.
    points = np.vstack((_regular(), [_regular()[3] * 0.5]))
    bad = audit_tetrahedra(points, [[0, 1, 2, 3], [0, 1, 2, 4]], [1, 1])
    assert bad["checks"]["positive_nondegenerate_tetrahedra"]
    assert bad["per_physical_tag"]["1"]["inconsistent_internal_face_orientations"] == 1
    triple = boundary_topology(np.array([[0, 1, 2, 3], [0, 2, 1, 4], [0, 1, 2, 5]]))
    assert triple["nonmanifold_faces"] == 1


def test_analytic_periodic_ring_mesh():
    n = 24
    points = np.array(
        [
            [(2 + u) * np.cos(phi), (2 + u) * np.sin(phi), v]
            for phi in np.arange(n) * 2 * np.pi / n
            for u, v in [(-0.2, -0.2), (0.2, -0.2), (-0.2, 0.2), (0.2, 0.2)]
        ]
    )
    cells = []
    for i in range(n):
        a, b, c, d = np.arange(4) + 4 * i
        e, f, g, h = np.arange(4) + 4 * ((i + 1) % n)
        cells.extend(
            [[a, e, f, h], [a, f, b, h], [a, b, d, h], [a, d, c, h], [a, c, g, h], [a, g, e, h]]
        )
    cells = np.array(cells)
    xyz = points[cells]
    det = np.linalg.det(xyz[:, 1:] - xyz[:, :1])
    cells[det < 0, :2] = cells[det < 0, 1::-1]
    result = audit_tetrahedra(points, cells, np.ones(len(cells), dtype=int))
    assert result["checks"]["positive_nondegenerate_tetrahedra"]
    topology = result["per_physical_tag"]["1"]
    assert topology["closed_ring_screen_pass"]
    assert topology["boundary_euler_characteristic"] == 0
    assert topology["boundary_components"] == 1
