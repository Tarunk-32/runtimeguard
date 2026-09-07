"""Checks that Supervisor correctly stops a FakeAgent when limits are hit."""

import unittest

from runtimeguard.logger import StepLogger
from runtimeguard.fake_agent import FakeAgent
from runtimeguard.supervisor import Supervisor


class TestSupervisor(unittest.TestCase):
    def test_max_steps_stops_agent_at_exactly_that_step(self):
        logger = StepLogger()
        agent = FakeAgent(logger)
        supervisor = Supervisor(logger, max_steps=3)

        agent.run("test task", supervisor)

        self.assertEqual(len(logger.steps), 3)
        summary = supervisor.get_summary()
        self.assertTrue(summary["stopped"])
        self.assertEqual(summary["step_count"], 3)
        self.assertIn("max_steps", summary["stop_reason"])

    def test_max_cost_stops_agent_before_max_steps_would(self):
        logger = StepLogger()
        agent = FakeAgent(logger)
        # 0.02 per step means the 0.05 cap is crossed on the 3rd step,
        # before FakeAgent's normal 5 steps would complete.
        supervisor = Supervisor(logger, max_cost=0.05)

        agent.run("test task", supervisor)

        summary = supervisor.get_summary()
        self.assertLess(len(logger.steps), 5)
        self.assertTrue(summary["stopped"])
        self.assertGreaterEqual(summary["total_cost"], 0.05)
        self.assertIn("max_cost", summary["stop_reason"])

    def test_no_limits_lets_all_steps_complete(self):
        logger = StepLogger()
        agent = FakeAgent(logger)
        supervisor = Supervisor(logger)

        agent.run("test task", supervisor)

        self.assertEqual(len(logger.steps), 5)
        summary = supervisor.get_summary()
        self.assertFalse(summary["stopped"])
        self.assertIsNone(summary["stop_reason"])
        self.assertEqual(summary["step_count"], 5)


if __name__ == "__main__":
    unittest.main()
