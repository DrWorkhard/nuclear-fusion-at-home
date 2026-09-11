"""Budgeted objective/inequality bundles with explicit, feasibility-first selection."""

import hashlib
import time

import numpy as np

from fusion_baselines.budgeted_oracle import BudgetExhausted


def candidate_key(values, tolerance):
    values = np.asarray(values, dtype=float)
    if (
        values.ndim != 1
        or len(values) < 2
        or not np.all(np.isfinite(values))
        or not np.isfinite(tolerance)
        or tolerance < 0
    ):
        raise ValueError("finite objective/inequalities and nonnegative tolerance required")
    violation = max(0.0, -float(np.min(values[1:])))
    return (
        0 if violation <= tolerance else 1,
        0.0 if violation <= tolerance else violation,
        float(values[0]),
    )


class InequalityOracle:
    def __init__(self, backend, limit, dimension, constraint_count, tolerance=1e-8):
        if any(type(n) is not int or n < 1 for n in (limit, dimension, constraint_count)):
            raise ValueError("positive integer limits/dimensions required")
        candidate_key([0, 0], tolerance)
        self.backend, self.limit, self.dimension = backend, limit, dimension
        self.constraint_count, self.tolerance = constraint_count, tolerance
        self.requests = self.cache_hits = self.denied = 0
        self.records = []
        self.best = self._cache_key = self._cache = None

    def evaluate(self, x):
        self.requests += 1
        x = np.asarray(x, dtype=np.float64).copy()
        key = (x.shape, x.tobytes())
        if key == self._cache_key:
            self.cache_hits += 1
            return tuple(a.copy() for a in self._cache)
        if len(self.records) >= self.limit:
            self.denied += 1
            raise BudgetExhausted("complete inequality bundle cap exhausted")
        record = {
            "attempt": len(self.records) + 1,
            "x_sha256": hashlib.sha256(x.tobytes()).hexdigest(),
            "status": "running",
        }
        self.records.append(record)
        self._cache_key = self._cache = None
        started = time.monotonic()
        try:
            if x.shape != (self.dimension,) or not np.all(np.isfinite(x)):
                raise ValueError("invalid physical proposal")
            values, jacobian, metrics = self.backend(x)
            values, jacobian = np.asarray(values, dtype=float), np.asarray(jacobian, dtype=float)
            if (
                values.shape != (1 + self.constraint_count,)
                or jacobian.shape != (len(values), self.dimension)
                or not np.all(np.isfinite(values))
                or not np.all(np.isfinite(jacobian))
            ):
                raise ValueError("invalid objective/constraint Jacobian bundle")
            selection = candidate_key(values, self.tolerance)
            violation = max(0.0, -float(np.min(values[1:])))
            record.update(
                status="completed",
                values=values.tolist(),
                objective=float(values[0]),
                maximum_violation=violation,
                construction_screen_pass=selection[0] == 0,
                selection_key=list(selection),
            )
            self._cache_key, self._cache = key, (values.copy(), jacobian.copy())
            if self.best is None or selection < tuple(self.best["selection_key"]):
                self.best = {**record, "x": x.copy(), "values": values.copy(), "metrics": metrics}
            return values.copy(), jacobian.copy()
        except Exception as error:
            record.update(status="error", error=f"{type(error).__name__}: {error}")
            raise
        finally:
            record["elapsed_seconds"] = time.monotonic() - started

    def counters(self):
        return {
            "limit": self.limit,
            "attempts": len(self.records),
            "requests": self.requests,
            "cache_hits": self.cache_hits,
            "denied": self.denied,
            "failed_attempts": sum(r["status"] == "error" for r in self.records),
        }
