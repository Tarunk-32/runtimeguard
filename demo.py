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

    print()
    print("--- Real agent demo 1/2 (RealAgent, real Claude API calls, max_cost=0.01) ---")

    try:
        from runtimeguard.real_agent import RealAgent

        real_logger = StepLogger()
        # max_cost is a real, tiny dollar limit (not a fake fixed number) -
        # small enough that a couple of real API calls should trip it, which
        # proves the Supervisor's cost limit works against real token cost.
        real_supervisor = Supervisor(real_logger, max_cost=0.01)
        real_agent = RealAgent(real_logger, real_supervisor)
        real_agent.run("Summarize what a for-loop does in one sentence.")

        real_summary = real_supervisor.get_summary()
        print(
            f"Real agent summary: total_cost=${real_summary['total_cost']:.6f}, "
            f"step_count={real_summary['step_count']}, stopped={real_summary['stopped']}, "
            f"stop_reason={real_summary['stop_reason']}"
        )

        generate_report(real_logger, real_supervisor, "reports/real_agent_report.md")
        print("Report saved to reports/real_agent_report.md")
    except ValueError as e:
        print(f"Skipping real agent demo: {e}")
    except ImportError as e:
        print(
            "Skipping real agent demo: missing dependency "
            f"({e}). Run `pip install -r requirements.txt`."
        )
    except Exception as e:
        print(f"Skipping real agent demo: API call failed ({e}).")

    print()
    print("--- Real agent demo 2/2 (RealAgent, real Claude API calls, max_cost=0.0015 - expect early stop) ---")

    try:
        from runtimeguard.real_agent import RealAgent

        stopped_logger = StepLogger()
        # Observed per-step cost in demo 1/2 was roughly $0.0004/step, so a
        # $0.0015 cap should be crossed partway through the 5-step reasoning
        # loop (around step 4) instead of letting the run complete normally -
        # this proves the Supervisor actually enforces a real cost limit,
        # not just tracks it.
        stopped_supervisor = Supervisor(stopped_logger, max_cost=0.0015)
        stopped_agent = RealAgent(stopped_logger, stopped_supervisor)
        stopped_agent.run("Summarize what a for-loop does in one sentence.")

        stopped_summary = stopped_supervisor.get_summary()
        if stopped_summary["stopped"]:
            print(
                f"Real agent STOPPED EARLY at step {stopped_summary['step_count']} - "
                f"real cost at stop: ${stopped_summary['total_cost']:.6f} "
                f"(reason: {stopped_summary['stop_reason']})"
            )
        else:
            print(
                "Real agent completed all steps without hitting max_cost="
                f"0.0015 - total_cost=${stopped_summary['total_cost']:.6f}, "
                f"step_count={stopped_summary['step_count']}"
            )

        generate_report(
            stopped_logger, stopped_supervisor, "reports/real_agent_stopped_report.md"
        )
        print("Report saved to reports/real_agent_stopped_report.md")
    except ValueError as e:
        print(f"Skipping real agent demo: {e}")
    except ImportError as e:
        print(
            "Skipping real agent demo: missing dependency "
            f"({e}). Run `pip install -r requirements.txt`."
        )
    except Exception as e:
        print(f"Skipping real agent demo: API call failed ({e}).")


if __name__ == "__main__":
    main()
