"""Non-mutating native-call accounting around unchanged field-Jacobian kernels."""

import numpy as np


def increment(counts, key):
    counts[key] = counts.get(key, 0) + 1


class CountedLocalField:
    """Retain each completed local Jacobian row even when a later point fails."""

    def __init__(self, field, counts):
        self.field, self.counts, self.rows = field, counts, []

    def __getattr__(self, name):
        return getattr(self.field, name)

    def B(self):
        increment(self.counts, "local_B_requests")
        value = self.field.B()
        increment(self.counts, "local_B_completed")
        return value

    def B_vjp(self, weights):
        increment(self.counts, "local_VJP_requests")
        derivative = self.field.B_vjp(weights)

        def apply(objective):
            row = derivative(objective)
            self.rows.append(np.asarray(row).copy())
            increment(self.counts, "local_VJP_completed")
            return row

        return apply


class CountedCurve:
    NAMES = {
        "gamma": "batch_position",
        "gammadash": "batch_tangent",
        "dgamma_by_dcoeff": "batch_position_derivative",
        "dgammadash_by_dcoeff": "batch_tangent_derivative",
    }

    def __init__(self, curve, counts):
        self.curve, self.counts = curve, counts

    def __getattr__(self, name):
        attribute = getattr(self.curve, name)
        if name not in self.NAMES:
            return attribute
        key = self.NAMES[name]

        def call(*args, **kwargs):
            increment(self.counts, key + "_requests")
            value = attribute(*args, **kwargs)
            increment(self.counts, key + "_completed")
            return value

        return call


class CountedCurrent:
    def __init__(self, current, counts):
        self.current, self.counts = current, counts

    def get_value(self):
        # In the fixed batched kernel, this call follows a completed projected_filament.
        increment(self.counts, "batch_coil_integrals_completed")
        increment(self.counts, "batch_current_value_requests")
        value = self.current.get_value()
        increment(self.counts, "batch_current_value_completed")
        return value

    def vjp(self, weights):
        increment(self.counts, "batch_current_VJP_requests")
        derivative = self.current.vjp(weights)

        def apply(objective):
            value = derivative(objective)
            increment(self.counts, "batch_current_VJP_completed")
            return value

        return apply


class CountedCoil:
    def __init__(self, coil, counts):
        self.curve = CountedCurve(coil.curve, counts)
        self.current = CountedCurrent(coil.current, counts)


class CountedBatchField:
    def __init__(self, field, counts):
        self.field = field
        self.coils = [CountedCoil(coil, counts) for coil in field.coils]

    def __getattr__(self, name):
        return getattr(self.field, name)
