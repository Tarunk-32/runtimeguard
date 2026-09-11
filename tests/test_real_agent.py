"""Tests for RealAgent against the real Claude API.

These tests are SKIPPED BY DEFAULT: they make real, billed API calls and
require a valid ANTHROPIC_API_KEY (in the environment or a .env file), so
they should not run as part of the normal (free, offline) test suite.

To run them manually:
  1. Make sure ANTHROPIC_API_KEY is set (e.g. via .env).
  2. Set the environment variable RUN_REAL_AGENT_TESTS=1, e.g.:
       RUN_REAL_AGENT_TESTS=1 python -m unittest tests/test_real_agent.py -v
"""

import os
import unittest

from runtimeguard.logger import StepLogger
from runtimeguard.supervisor import Supervisor

RUN_REAL_TESTS = os.environ.get("RUN_REAL_AGENT_TESTS") == "1"


@unittest.skipUnless(
    RUN_REAL_TESTS,
    "Costs real money and needs ANTHROPIC_API_KEY. "
    "Set RUN_REAL_AGENT_TESTS=1 to run.",
)
class TestRealAgent(unittest.TestCase):
    def test_real_agent_logs_real_token_counts_and_cost(self):
        from runtimeguard.real_agent import RealAgent

        logger = StepLogger()
        supervisor = Supervisor(logger)
        agent = RealAgent(logger, supervisor)

        agent.run("Say hello in one word.", max_iterations=1)

        self.assertEqual(len(logger.steps), 1)
        step = logger.steps[0]
        self.assertGreater(step["output"]["input_tokens"], 0)
        self.assertGreater(step["output"]["output_tokens"], 0)
        self.assertGreater(step["output"]["cost"], 0.0)

        summary = supervisor.get_summary()
        self.assertGreater(summary["total_cost"], 0.0)

    def test_real_agent_stops_when_max_cost_is_hit(self):
        from runtimeguard.real_agent import RealAgent

        logger = StepLogger()
        # An extremely small cap that a single real call should exceed,
        # to prove the Supervisor stops RealAgent using real cost figures.
        supervisor = Supervisor(logger, max_cost=0.0000001)
        agent = RealAgent(logger, supervisor)

        agent.run("Say hello in one word.", max_iterations=5)

        summary = supervisor.get_summary()
        self.assertTrue(summary["stopped"])
        self.assertLess(len(logger.steps), 5)


if __name__ == "__main__":
    unittest.main()
