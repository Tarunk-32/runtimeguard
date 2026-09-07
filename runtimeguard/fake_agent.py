"""A fake agent that simulates a multi-step task without calling any real APIs."""


class FakeAgent:
    """Simulates a 5-step agent run, logging each step via a StepLogger."""

    def __init__(self, logger):
        self.logger = logger

    def run(self, task: str):
        """Pretend to work through `task` in 5 steps, printing progress as it goes."""
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

        print("Task complete.")
