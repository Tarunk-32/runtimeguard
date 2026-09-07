"""Records the steps an agent takes so a run can be inspected or replayed later."""

import json
from datetime import datetime, timezone


class StepLogger:
    """Collects step records in memory and can persist them to a JSON file."""

    def __init__(self):
        self.steps = []

    def log_step(self, action_name, input_data, output_data):
        """Append a single step record with a UTC timestamp."""
        self.steps.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action_name": action_name,
            "input": input_data,
            "output": output_data,
        })

    def save(self, filepath):
        """Write all logged steps to filepath as a JSON array."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.steps, f, indent=2)
