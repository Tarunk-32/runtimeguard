"""A fake agent that simulates a multi-step task without calling any real APIs."""


class FakeAgent:
    """Simulates an agent run, logging each step via a StepLogger.

    Supports two modes, chosen via the `mode` argument to run():
    - "normal" (default): works through a fixed 5-step plan, same as before.
    - "loop": repeats the exact same step over and over, to exercise a
      Supervisor's loop detection.
    """

    def __init__(self, logger):
        self.logger = logger

    STEP_COST = 0.02
    """Fake per-step cost used to exercise Supervisor's cost tracking."""

    MAX_LOOP_ATTEMPTS = 10
    """Safety cap on how many times "loop" mode repeats its step if nothing stops it."""

    def run(self, task: str, supervisor=None, mode: str = "normal"):
        """Pretend to work through `task`, printing progress as it goes.

        If a Supervisor is given, it's checked after every step; if the
        Supervisor says to stop (a limit was hit, or a loop was detected),
        the agent stops immediately instead of continuing.
        """
        print(f"Starting task: {task}")

        if mode == "loop":
            self._run_loop(task, supervisor)
        else:
            self._run_normal(task, supervisor)

    def _run_normal(self, task, supervisor):
        """Run the original fixed 5-step plan (unchanged from Phase 1/2 behavior)."""
        step_data = [
            ("plan_task", {"task": task}, {"plan": "break task into subtasks"}),
            ("search_info", {"query": task}, {"results": ["fact A", "fact B"]}),
            ("analyze_info", {"facts": ["fact A", "fact B"]}, {"analysis": "facts support a solution"}),
            ("draft_answer", {"analysis": "facts support a solution"}, {"draft": "here is a draft answer"}),
            ("finalize_answer", {"draft": "here is a draft answer"}, {"final": "here is the final answer"}),
        ]

        for i, (action_name, input_data, output_data) in enumerate(step_data, start=1):
            print(f"Step {i}: {action_name}")
            self.logger.log_step(action_name, input_data, output_data)

            if supervisor is not None:
                should_continue = supervisor.check_step(self.STEP_COST, action_name, input_data)
                if not should_continue:
                    print(f"Stopping early: {supervisor.stop_reason}")
                    return

        print("Task complete.")

    def _run_loop(self, task, supervisor):
        """Repeat the exact same step (same action_name, same input) up to
        MAX_LOOP_ATTEMPTS times, so a loop-detecting Supervisor can be tested."""
        action_name = "search_info"
        input_data = {"query": task}
        output_data = {"results": ["fact A", "fact B"]}

        for i in range(1, self.MAX_LOOP_ATTEMPTS + 1):
            print(f"Step {i}: {action_name} (loop mode)")
            self.logger.log_step(action_name, input_data, output_data)

            if supervisor is not None:
                should_continue = supervisor.check_step(self.STEP_COST, action_name, input_data)
                if not should_continue:
                    print(f"Stopping early: {supervisor.stop_reason}")
                    return

        print(f"Reached max loop attempts ({self.MAX_LOOP_ATTEMPTS}) without being stopped.")
