"""Checks that running FakeAgent produces exactly 5 well-formed log entries."""

import unittest

from runtimeguard.logger import StepLogger
from runtimeguard.fake_agent import FakeAgent


class TestStepLogger(unittest.TestCase):
    def test_fake_agent_logs_five_steps_with_required_fields(self):
        logger = StepLogger()
        agent = FakeAgent(logger)
        agent.run("test task")

        self.assertEqual(len(logger.steps), 5)

        for entry in logger.steps:
            self.assertIn("timestamp", entry)
            self.assertIn("action_name", entry)
            self.assertIn("input", entry)
            self.assertIn("output", entry)


if __name__ == "__main__":
    unittest.main()
