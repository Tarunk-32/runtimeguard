"""Tracks cost and step count for an agent run and decides when to stop it."""


class Supervisor:
    """Enforces optional max_steps / max_cost limits on an agent run.

    The agent calls check_step() after each step it takes. The Supervisor
    keeps a running total of steps and cost, and tells the agent whether
    it's still allowed to continue.
    """

    def __init__(self, logger, max_steps=None, max_cost=None, loop_threshold=None, label=None):
        self.logger = logger
        self.max_steps = max_steps
        self.max_cost = max_cost
        self.loop_threshold = loop_threshold
        self.label = label
        """Optional human-readable name for this run (e.g. "Project A",
        "Client Demo"), used to identify the run in things like the
        dashboard. Purely descriptive - has no effect on limit checking."""
        """If set (e.g. 3), stop the run when the same action+input repeats
        this many times in a row. None (the default) turns loop detection off."""

        self.total_cost = 0.0
        self.step_count = 0
        self.stopped = False
        self.stop_reason = None

        self._recent_steps = []
        """Rolling history of (action_name, input_data) pairs, used for exact-match
        loop detection. Only the last loop_threshold entries matter, but we don't
        bother trimming it since runs are short-lived."""

    def check_step(self, step_cost: float, action_name=None, input_data=None) -> bool:
        """Record one step, then return True to continue or False to stop.

        `action_name` and `input_data` are optional so existing callers that only
        care about cost/step limits keep working unchanged. Passing them enables
        loop detection: if loop_threshold is set and the last N steps (N =
        loop_threshold) all share the same action_name and input_data, the run
        is stopped as a detected loop.

        If a limit is set and has been reached, self.stop_reason is set to a
        human-readable explanation of which limit triggered the stop.
        """
        self.step_count += 1
        self.total_cost += step_cost

        if self.max_steps is not None and self.step_count >= self.max_steps:
            self.stopped = True
            self.stop_reason = (
                f"max_steps limit reached: {self.step_count}/{self.max_steps} steps"
            )
            return False

        if self.max_cost is not None and self.total_cost >= self.max_cost:
            self.stopped = True
            self.stop_reason = (
                f"max_cost limit reached: ${self.total_cost:.4f}/${self.max_cost:.4f}"
            )
            return False

        if self.loop_threshold is not None and action_name is not None:
            self._recent_steps.append((action_name, input_data))
            n = self.loop_threshold
            last_n = self._recent_steps[-n:]
            if len(last_n) == n and all(step == last_n[0] for step in last_n):
                self.stopped = True
                self.stop_reason = (
                    f"Loop detected: '{action_name}' repeated {n} times with identical input"
                )
                return False

        return True

    def get_summary(self) -> dict:
        """Return the run's totals: cost, step count, and why it stopped (if it did)."""
        return {
            "total_cost": self.total_cost,
            "step_count": self.step_count,
            "stopped": self.stopped,
            "stop_reason": self.stop_reason,
            "label": self.label,
        }
