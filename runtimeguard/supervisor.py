"""Tracks cost and step count for an agent run and decides when to stop it."""


class Supervisor:
    """Enforces optional max_steps / max_cost limits on an agent run.

    The agent calls check_step() after each step it takes. The Supervisor
    keeps a running total of steps and cost, and tells the agent whether
    it's still allowed to continue.
    """

    def __init__(self, logger, max_steps=None, max_cost=None):
        self.logger = logger
        self.max_steps = max_steps
        self.max_cost = max_cost

        self.total_cost = 0.0
        self.step_count = 0
        self.stopped = False
        self.stop_reason = None

    def check_step(self, step_cost: float) -> bool:
        """Record one step's cost, then return True to continue or False to stop.

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

        return True

    def get_summary(self) -> dict:
        """Return the run's totals: cost, step count, and why it stopped (if it did)."""
        return {
            "total_cost": self.total_cost,
            "step_count": self.step_count,
            "stopped": self.stopped,
            "stop_reason": self.stop_reason,
        }
