"""Exact common-bundle accounting, separate from any optimizer's iteration counters."""

import hashlib
import time

import numpy as np


class BudgetExhausted(BaseException):
    """Stop before another backend call, including across Exception retry handlers."""


class BudgetedOracle:
    def __init__(self, backend, limit: int, dimension: int):
        if type(limit) is not int or limit < 1 or type(dimension) is not int or dimension < 1:
            raise ValueError("limit and dimension must be positive integers")
        self.backend, self.limit, self.dimension = backend, limit, dimension
        self.requests = self.cache_hits = self.denied = 0
        self.records = []
        self._cache_key = self._cache = self.best = None

    def evaluate(self, x):
        self.requests += 1
        x = np.asarray(x, dtype=np.float64).copy()
        key = (x.shape, x.tobytes())
        if key == self._cache_key:
            self.cache_hits += 1
            return tuple(a.copy() for a in self._cache)
        if len(self.records) >= self.limit:
            self.denied += 1
            raise BudgetExhausted("full-bundle evaluation budget exhausted")
        record = {
            "attempt": len(self.records) + 1,
            "x_sha256": hashlib.sha256(x.tobytes()).hexdigest(),
            "status": "running",
        }
        self.records.append(record)
        # A failed request must invalidate the last-successful-state cache:
        # otherwise a stateful backend could be left at the failed proposal.
        self._cache_key = self._cache = None
        started = time.monotonic()
        try:
            if x.shape != (self.dimension,) or not np.all(np.isfinite(x)):
                raise ValueError("invalid proposal shape or nonfinite coordinates")
            values, jacobian = [np.asarray(a, dtype=float).copy() for a in self.backend(x.copy())]
            if values.ndim != 1 or values.size == 0 or jacobian.shape != (len(values), len(x)):
                raise ValueError("invalid bundle/Jacobian shape")
            if not np.all(np.isfinite(values)) or not np.all(np.isfinite(jacobian)):
                raise ValueError("nonfinite bundle output")
            merit = float(values @ values / 2)
            if not np.isfinite(merit):
                raise ValueError("nonfinite bundle merit")
            record.update(status="completed", values=values.tolist(), merit=merit)
            self._cache_key, self._cache = key, (values.copy(), jacobian.copy())
            if self.best is None or merit < self.best["merit"]:
                self.best = {
                    "x": x.copy(),
                    "values": values.copy(),
                    "merit": merit,
                    "attempt": record["attempt"],
                    "x_sha256": record["x_sha256"],
                }
            return values, jacobian
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


class NamedVectorBackend:
    """Map each local objective's free-DOF Jacobian into an explicit global basis."""

    def __init__(self, global_objective, objectives, scales):
        self.global_objective = global_objective
        self.objectives = list(objectives)
        self.scales = np.asarray(scales, dtype=float)
        self.names = list(global_objective.dof_names)
        if len(set(self.names)) != len(self.names) or len(self.names) != len(global_objective.x):
            raise ValueError("global free-DOF names must be unique and complete")
        if self.scales.shape != (len(self.objectives),) or not np.all(np.isfinite(self.scales)):
            raise ValueError("one finite scale required per objective")
        if np.any(self.scales <= 0):
            raise ValueError("objective scales must be positive")
        positions = {name: i for i, name in enumerate(self.names)}
        self.indices = []
        for objective in self.objectives:
            names = list(objective.dof_names)
            if len(set(names)) != len(names) or len(names) != len(objective.x):
                raise ValueError("local free-DOF names must be unique and complete")
            if not set(names) <= positions.keys():
                raise ValueError("local degree of freedom missing from global basis")
            self.indices.append(np.array([positions[name] for name in names], dtype=int))

    def __call__(self, x):
        self.global_objective.x = x.copy()
        values = np.zeros(len(self.objectives))
        jacobian = np.zeros((len(self.objectives), len(x)))
        for i, (objective, indices) in enumerate(zip(self.objectives, self.indices, strict=True)):
            if not np.array_equal(objective.x, x[indices]):
                raise ValueError("local/global state mismatch after global update")
            values[i] = float(objective.J()) * self.scales[i]
            gradient = np.asarray(objective.dJ(), dtype=float)
            if gradient.shape != (len(indices),):
                raise ValueError("local gradient shape mismatch")
            jacobian[i, indices] = gradient * self.scales[i]
        return values, jacobian
