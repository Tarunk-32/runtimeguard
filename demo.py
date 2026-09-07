"""Demo script: run a FakeAgent, save its step log, and print a summary."""

import os

from runtimeguard.logger import StepLogger
from runtimeguard.fake_agent import FakeAgent


def main():
    logger = StepLogger()
    agent = FakeAgent(logger)
    agent.run("test task")

    os.makedirs("runs", exist_ok=True)
    logger.save("runs/demo_run.json")

    print(f"Summary: {len(logger.steps)} steps logged to runs/demo_run.json")


if __name__ == "__main__":
    main()
