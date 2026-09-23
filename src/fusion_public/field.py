"""Scalar SI filament evaluator, deliberately independent of native libraries.

This small reference implementation prioritizes inspectability, not speed. It
uses the legacy benchmark convention mu0/(4*pi)=1e-7 and t in [0,1]. It does not
check continuous geometry or solve an equilibrium.
"""

import math

from .data import require, vector


def curve(coefficients, count):
    require(type(count) is int and 16 <= count <= 512, "16..512 quadrature nodes required")
    require(len(coefficients) == 3, "Three Fourier axes required")
    width = len(coefficients[0])
    require(width >= 3 and width % 2 == 1, "Odd nonconstant Fourier width required")
    coefficients = [vector(axis, width) for axis in coefficients]
    samples = []
    for j in range(count):
        p = [axis[0] for axis in coefficients]
        v = [0.0, 0.0, 0.0]
        for mode in range(1, (width + 1) // 2):
            omega = 2 * math.pi * mode
            sine, cosine = math.sin(omega * j / count), math.cos(omega * j / count)
            for axis in range(3):
                s, c = coefficients[axis][2*mode-1:2*mode+1]
                p[axis] += s * sine + c * cosine
                v[axis] += omega * (s * cosine - c * sine)
        require(sum(x*x for x in v) > 0, "Stationary filament quadrature node")
        samples.append((p, v))
    return samples


def physical_curves(candidate, case, count):
    result = []
    for row in case["physical"]:
        base = candidate["base_coefficients"][row["base_index"]]
        # Historical serialization uses row vectors: x_physical = x_base @ Q.
        transformed = [
            [sum(row["matrix"][j][i] * base[j][k] for j in range(3)) for k in range(11)]
            for i in range(3)
        ]
        result.append((curve(transformed, count), row["current"]))
    return result


def field(points, coils):
    magnetic, potential = [], []
    for point in points:
        x, y, z = vector(point)
        b, a = [0.0]*3, [0.0]*3
        for samples, current in coils:
            factor = 1e-7 * current / len(samples)
            sb, sa = [0.0]*3, [0.0]*3
            for (px, py, pz), (vx, vy, vz) in samples:
                dx, dy, dz = x-px, y-py, z-pz
                rr = dx*dx + dy*dy + dz*dz
                require(rr > 1e-24, "Field point too close to a filament quadrature node")
                inverse = 1 / math.sqrt(rr)
                cubed = inverse / rr
                sb[0] += (vy*dz-vz*dy)*cubed
                sb[1] += (vz*dx-vx*dz)*cubed
                sb[2] += (vx*dy-vy*dx)*cubed
                sa[0] += vx*inverse
                sa[1] += vy*inverse
                sa[2] += vz*inverse
            for axis in range(3):
                b[axis] += factor*sb[axis]
                a[axis] += factor*sa[axis]
        require(all(math.isfinite(v) for v in b+a), "Nonfinite field result")
        magnetic.append(b)
        potential.append(a)
    return {"B_T": magnetic, "A_Tm": potential}


def metrics(fields, case):
    boundary = case["groups"]["boundary"]
    weights = boundary["weights"]
    errors = []
    for b, n in zip(fields["boundary"]["B_T"], boundary["unit_normals"], strict=True):
        norm = math.sqrt(sum(x*x for x in b))
        require(norm > 0, "Zero boundary field has undefined relative normal error")
        errors.append(sum(x*y for x, y in zip(b, n, strict=True))/norm)
    target = case["groups"]["inner"]["target_B_T"]
    residual = sum(
        sum((a-b)**2 for a, b in zip(actual, wanted, strict=True))
        for actual, wanted in zip(fields["inner"]["B_T"], target, strict=True)
    ) / len(target) / case["B2_scale_T2"]
    return dict(
        sampled_normal_rms=math.sqrt(sum(w*e*e for w, e in zip(weights, errors, strict=True))
                                     / sum(weights)),
        sampled_normal_max=max(abs(e) for e in errors),
        sampled_inner_vector_rms=math.sqrt(residual),
        max_abs_current_A=max(abs(c["current"]) for c in case["physical"]),
    )


def relative_error(actual, reference):
    require(len(actual) == len(reference) > 0, "Matching nonempty vector arrays")
    denominator = max(abs(x) for row in reference for x in row)
    require(denominator > 0, "Nonzero reference denominator required")
    return max(abs(a-b) for aa, bb in zip(actual, reference, strict=True)
               for a, b in zip(aa, bb, strict=True)) / denominator
