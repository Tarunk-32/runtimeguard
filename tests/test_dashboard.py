"""Checks that generate_dashboard() writes a valid, self-contained HTML file:
every run's label shows up, a chart is present, and special characters in a
run's stop_reason are HTML-escaped rather than injected raw."""

import os
import shutil
import tempfile
import unittest

from runtimeguard.dashboard import generate_dashboard


class TestDashboard(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _sample_records(self):
        return [
            {
                "label": "Fake Agent - Normal",
                "total_cost": 0.06,
                "step_count": 3,
                "stopped": True,
                "stop_reason": "max_steps limit reached: 3/3 steps",
                "timestamp": "2026-09-11T00:00:00+00:00",
            },
            {
                "label": "Real Agent - Under Budget",
                "total_cost": 0.0021,
                "step_count": 5,
                "stopped": False,
                "stop_reason": None,
                "timestamp": "2026-09-11T00:01:00+00:00",
            },
        ]

    def test_dashboard_contains_every_label_and_a_chart(self):
        output_path = os.path.join(self.tmp_dir, "dashboard.html")
        generate_dashboard(self._sample_records(), output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Fake Agent - Normal", content)
        self.assertIn("Real Agent - Under Budget", content)
        self.assertTrue("Chart" in content or "<canvas" in content)

    def test_special_characters_in_stop_reason_are_escaped(self):
        records = self._sample_records()
        records[0]["stop_reason"] = '<script>alert("x")</script> & <img src=x>'

        output_path = os.path.join(self.tmp_dir, "dashboard.html")
        generate_dashboard(records, output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        # The raw, unescaped tag must never appear as real markup...
        self.assertNotIn("<script>alert", content)
        self.assertNotIn("<img src=x>", content)
        # ...but the escaped text should still be present somewhere.
        self.assertIn("&lt;script&gt;", content)
        self.assertIn("&lt;img src=x&gt;", content)

    def test_output_directory_is_created_if_missing(self):
        output_path = os.path.join(self.tmp_dir, "nested", "dashboard.html")
        generate_dashboard(self._sample_records(), output_path)

        self.assertTrue(os.path.exists(output_path))


if __name__ == "__main__":
    unittest.main()
