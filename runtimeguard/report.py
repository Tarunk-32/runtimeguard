"""Turns a StepLogger + Supervisor's records of a run into a human-readable
Markdown report, so someone can see what an agent did without reading JSON."""

import os
from datetime import datetime, timezone


def _short(value, max_len=80):
    """Render input/output data as a short one-line string, truncating if long."""
    text = str(value)
    text = " ".join(text.split())
    if len(text) > max_len:
        text = text[: max_len - 3] + "..."
    return text


def generate_report(logger, supervisor, output_path: str):
    """Write a Markdown report of a run to output_path.

    `logger` is the StepLogger that recorded the run's steps, and `supervisor`
    is the Supervisor that watched over it. The report has a title, a summary
    (steps, cost, whether/why it stopped early), and a step-by-step timeline.
    If the run was stopped early, a callout is added near the top so that's
    immediately visible.
    """
    summary = supervisor.get_summary()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = []
    lines.append(f"# RuntimeGuard Run Report — {now}")
    lines.append("")

    if summary["stopped"]:
        lines.append("> ⚠️ **Stopped Early**")
        lines.append(f"> {summary['stop_reason']}")
        lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Total steps | {summary['step_count']} |")
    lines.append(f"| Total cost | ${summary['total_cost']:.4f} |")
    lines.append(f"| Stopped early | {'Yes' if summary['stopped'] else 'No'} |")
    reason = summary["stop_reason"] if summary["stopped"] else "Completed normally"
    lines.append(f"| Reason | {reason} |")
    lines.append("")

    lines.append("## Step-by-step timeline")
    lines.append("")
    if not logger.steps:
        lines.append("_No steps were logged._")
    else:
        for i, step in enumerate(logger.steps, start=1):
            lines.append(
                f"{i}. **{step['action_name']}** — "
                f"input: `{_short(step['input'])}` → "
                f"output: `{_short(step['output'])}` "
                f"_(at {step['timestamp']})_"
            )
    lines.append("")

    parent_dir = os.path.dirname(output_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
