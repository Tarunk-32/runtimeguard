"""A fake agent that simulates a multi-step task without calling any real APIs."""


class FakeAgent:
    """Simulates a 5-step agent run, logging each step via a StepLogger."""

    def __init__(self, logger):
        self.logger = logger

    STEP_COST = 0.02
    """Fake per-step cost used to exercise Supervisor's cost tracking."""

    def run(self, task: str, supervisor=None):
        """Pretend to work through `task` in 5 steps, printing progress as it goes.

        If a Supervisor is given, it's checked after every step; if the
        Supervisor says to stop (a limit was hit), the agent stops
        immediately instead of running its remaining steps.
        """
        print(f"Starting task: {task}")

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
                should_continue = supervisor.check_step(self.STEP_COST)
                if not should_continue:
                    print(f"Stopping early: {supervisor.stop_reason}")
                    return

        print("Task complete.")
