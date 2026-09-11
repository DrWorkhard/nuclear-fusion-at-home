"""Monotonic request-boundary deadline, retaining the existing physical oracle ledger."""

import math
import time

from .budgeted_oracle import BudgetedOracle, BudgetExhausted


class TimedOracle(BudgetedOracle):
    def __init__(self, backend, limit, dimension, seconds, clock=time.monotonic):
        if isinstance(seconds, bool) or not math.isfinite(seconds) or seconds <= 0:
            raise ValueError("positive finite wall-clock budget required")
        super().__init__(backend, limit, dimension)
        self.clock = clock
        self.seconds = float(seconds)
        self.started = clock()
        self.deadline = self.started + self.seconds
        self.time_denials = 0
        self.stopped = None

    def evaluate(self, x):
        now = self.clock()
        if now >= self.deadline:
            self.requests += 1
            self.denied += 1
            self.time_denials += 1
            self.stopped = now
            raise BudgetExhausted("monotonic wall-clock budget exhausted")
        return super().evaluate(x)

    def timing(self):
        observed = self.clock() if self.stopped is None else self.stopped
        return {
            "budget_seconds": self.seconds,
            "elapsed_to_stop_seconds": observed - self.started,
            "overrun_seconds": max(0.0, observed - self.deadline),
            "time_denials": self.time_denials,
            "deadline_checked_on_cache_hits": True,
        }
