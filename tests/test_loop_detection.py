"""Checks Supervisor's exact-match loop detection: it should catch a FakeAgent
stuck repeating the same step, and it should leave a normal, non-repeating
run alone."""

import unittest

from runtimeguard.logger import StepLogger
from runtimeguard.fake_agent import FakeAgent
from runtimeguard.supervisor import Supervisor


class TestLoopDetection(unittest.TestCase):
    def test_loop_threshold_stops_looping_agent_quickly(self):
        logger = StepLogger()
        agent = FakeAgent(logger)
        supervisor = Supervisor(logger, loop_threshold=3)

        agent.run("test task", supervisor, mode="loop")

        summary = supervisor.get_summary()
        self.assertTrue(summary["stopped"])
        # Should stop right when the 3rd identical step lands, well short of
        # FakeAgent's MAX_LOOP_ATTEMPTS safety cap of 10.
        self.assertLessEqual(summary["step_count"], 4)
        self.assertIn("loop", summary["stop_reason"].lower())

    def test_loop_threshold_does_not_flag_normal_run(self):
        logger = StepLogger()
        agent = FakeAgent(logger)
        supervisor = Supervisor(logger, loop_threshold=3)

        agent.run("test task", supervisor, mode="normal")

        self.assertEqual(len(logger.steps), 5)
        summary = supervisor.get_summary()
        self.assertFalse(summary["stopped"])
        self.assertIsNone(summary["stop_reason"])


if __name__ == "__main__":
    unittest.main()
