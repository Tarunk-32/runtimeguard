"""Demo script: run a FakeAgent, save its step log, and print a summary."""

import os

from runtimeguard.logger import StepLogger
from runtimeguard.fake_agent import FakeAgent
from runtimeguard.supervisor import Supervisor
from runtimeguard.report import generate_report


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

    generate_report(logger, supervisor, "reports/normal_run_report.md")
    print("Report saved to reports/normal_run_report.md")

    print()
    print("--- Loop detection demo ---")

    # loop_threshold=3 means: if the same action+input shows up 3 times in a
    # row, treat it as a stuck agent and stop it.
    loop_logger = StepLogger()
    loop_agent = FakeAgent(loop_logger)
    loop_supervisor = Supervisor(loop_logger, loop_threshold=3)
    loop_agent.run("test task", loop_supervisor, mode="loop")

    loop_summary = loop_supervisor.get_summary()
    print(
        f"Loop supervisor summary: step_count={loop_summary['step_count']}, "
        f"stopped={loop_summary['stopped']}, stop_reason={loop_summary['stop_reason']}"
    )

    generate_report(loop_logger, loop_supervisor, "reports/loop_run_report.md")
    print("Report saved to reports/loop_run_report.md")


if __name__ == "__main__":
    main()
