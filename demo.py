"""Demo script: run a FakeAgent, save its step log, and print a summary."""

import os

from runtimeguard.logger import StepLogger
from runtimeguard.fake_agent import FakeAgent
from runtimeguard.supervisor import Supervisor


def main():
    logger = StepLogger()
    agent = FakeAgent(logger)

    # max_steps is set deliberately low (3) so we can see the Supervisor
    # stop the agent early, even though FakeAgent normally takes 5 steps.
    supervisor = Supervisor(logger, max_steps=3)
    agent.run("test task", supervisor)

    os.makedirs("runs", exist_ok=True)
    logger.save("runs/demo_run.json")

    print(f"Summary: {len(logger.steps)} steps logged to runs/demo_run.json")

    summary = supervisor.get_summary()
    print(
        f"Supervisor summary: total_cost=${summary['total_cost']:.4f}, "
        f"step_count={summary['step_count']}, stopped={summary['stopped']}, "
        f"stop_reason={summary['stop_reason']}"
    )


if __name__ == "__main__":
    main()
