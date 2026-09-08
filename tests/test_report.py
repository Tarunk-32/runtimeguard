"""Checks that generate_report() produces a Markdown file that accurately
reflects a run: whether it completed normally or was stopped early, why,
and how many steps it took."""

import os
import shutil
import tempfile
import unittest

from runtimeguard.logger import StepLogger
from runtimeguard.fake_agent import FakeAgent
from runtimeguard.supervisor import Supervisor
from runtimeguard.report import generate_report


class TestReport(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_completed_run_report_says_completed_and_not_stopped(self):
        logger = StepLogger()
        agent = FakeAgent(logger)
        supervisor = Supervisor(logger)

        agent.run("test task", supervisor)

        output_path = os.path.join(self.tmp_dir, "report.md")
        generate_report(logger, supervisor, output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Completed", content)
        self.assertNotIn("Stopped Early", content)

    def test_stopped_run_report_shows_callout_and_reason(self):
        logger = StepLogger()
        agent = FakeAgent(logger)
        supervisor = Supervisor(logger, max_steps=3)

        agent.run("test task", supervisor)

        output_path = os.path.join(self.tmp_dir, "report.md")
        generate_report(logger, supervisor, output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Stopped Early", content)
        self.assertIn(supervisor.stop_reason, content)

    def test_report_timeline_lists_every_logged_step(self):
        logger = StepLogger()
        agent = FakeAgent(logger)
        supervisor = Supervisor(logger, max_steps=3)

        agent.run("test task", supervisor)

        output_path = os.path.join(self.tmp_dir, "report.md")
        generate_report(logger, supervisor, output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        for i, step in enumerate(logger.steps, start=1):
            self.assertIn(f"{i}. **{step['action_name']}**", content)


if __name__ == "__main__":
    unittest.main()
