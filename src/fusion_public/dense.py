"""Dense boundary and flux diagnostics from committed data; not part of the bound evaluator.

Rebuilds the native 64x64 one-period target-boundary grid and the phi=0 flux loop
from the committed reference input, whose SHA-256 the starter records as its parent.
The normal metric is current-scale invariant. The separate dense_interior module
uses the bundled target packets for full interior target-surface diagnostics.
"""

import math

from .data import ROOT, load, require, sha
from .field import field, physical_curves

INPUT = ROOT / "evidence" / "plasma-design-v2" / "reference-input-401.json"


def load_input(case):
    raw = INPUT.read_bytes()
    require(sha(raw) == case["provenance"]["parent_sha256"]["equilibrium_input"],
            "Reference input differs from the starter's recorded parent")
    document = load(INPUT)
    require((document["nfp"], document["mpol"], document["ntor"]) == (2, 5, 10),
            "Registered nfp2 reference boundary required")
    return document


def _modes(rows):
    return [(row["m"], row["n"], row["value"]) for row in rows if row["value"] != 0]


def boundary_grid(document, nphi=64, ntheta=64):
    """simsopt SurfaceRZFourier convention, one field period, offset 0, area weights."""
    nfp, rbc, zbs = document["nfp"], _modes(document["rbc"]), _modes(document["zbs"])
    points, normals, areas = [], [], []
    for j in range(nphi):
        phi = 2 * math.pi * j / (nphi * nfp)
        cphi, sphi = math.cos(phi), math.sin(phi)
        for i in range(ntheta):
            theta = 2 * math.pi * i / ntheta
            r = z = rt = zt = rp = zp = 0.0
            for m, n, value in rbc:
                angle = m*theta - nfp*n*phi
                r += value*math.cos(angle)
                rt -= value*m*math.sin(angle)
                rp += value*nfp*n*math.sin(angle)
            for m, n, value in zbs:
                angle = m*theta - nfp*n*phi
                z += value*math.sin(angle)
                zt += value*m*math.cos(angle)
                zp -= value*nfp*n*math.cos(angle)
            # Derivatives with respect to normalized (turn) coordinates.
            dt = [2*math.pi*rt*cphi, 2*math.pi*rt*sphi, 2*math.pi*zt]
            dp = [2*math.pi*(rp*cphi - r*sphi), 2*math.pi*(rp*sphi + r*cphi), 2*math.pi*zp]
            normal = [dp[1]*dt[2] - dp[2]*dt[1], dp[2]*dt[0] - dp[0]*dt[2],
                      dp[0]*dt[1] - dp[1]*dt[0]]
            size = math.sqrt(sum(x*x for x in normal))
            require(size > 0, "Regular target surface required")
            points.append([r*cphi, r*sphi, z])
            normals.append([x/size for x in normal])
            areas.append(size)
    total = sum(areas)
    return points, normals, [a/total for a in areas]


def flux_loop(document, count=256):
    """Exact phi=0 boundary section; tangent is d(position)/dt with t=theta/(2pi)."""
    points, tangents = [], []
    for j in range(count):
        theta = 2 * math.pi * j / count
        r = sum(v*math.cos(m*theta) for m, _, v in _modes(document["rbc"]))
        z = sum(v*math.sin(m*theta) for m, _, v in _modes(document["zbs"]))
        rt = -sum(2*math.pi*m*v*math.sin(m*theta) for m, _, v in _modes(document["rbc"]))
        zt = sum(2*math.pi*m*v*math.cos(m*theta) for m, _, v in _modes(document["zbs"]))
        points.append([r, 0.0, z])
        tangents.append([rt, 0.0, zt])
    return points, tangents


def flux_scale(candidate, case, document, count=256):
    """Uniform current factor that restores the target toroidal flux |phiedge|."""
    points, tangents = flux_loop(document)
    potential = field(points, physical_curves(candidate, case, count))["A_Tm"]
    flux = sum(sum(a*t for a, t in zip(av, tv, strict=True))
               for av, tv in zip(potential, tangents, strict=True))
    flux /= len(points)
    require(flux != 0, "Nonzero loop flux required")
    return abs(document["phiedge"]) / abs(flux)


def dense_boundary(candidate, case, count=256):
    """Dense relative normal field on the full native grid (about 20 s at 256 nodes)."""
    document = load_input(case)
    points, normals, weights = boundary_grid(document)
    magnetic = field(points, physical_curves(candidate, case, count))["B_T"]
    errors = []
    for b, n in zip(magnetic, normals, strict=True):
        norm = math.sqrt(sum(x*x for x in b))
        require(norm > 0, "Zero boundary field has undefined relative normal error")
        errors.append(sum(x*y for x, y in zip(b, n, strict=True)) / norm)
    scale = flux_scale(candidate, case, document, count)
    return dict(
        ncoil=count, grid_points=len(points),
        dense_normal_rms=math.sqrt(sum(w*e*e for w, e in zip(weights, errors, strict=True))),
        dense_normal_max=max(abs(e) for e in errors),
        flux_scale=scale,
        flux_normalized_current_A=scale*max(abs(c["current"]) for c in case["physical"]),
        physical_admission=False,
        interpretation="Dense boundary diagnostic only; use dense-interior for "
        "target-surface errors",
    )
