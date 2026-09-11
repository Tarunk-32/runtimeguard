"""A real, API-backed agent (via LangChain's Anthropic integration) that pairs
with the same StepLogger/Supervisor used by FakeAgent, but tracks *real* cost
computed from the token usage Anthropic actually reports for each call."""

import os

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


class RealAgent:
    """Runs a short multi-step reasoning loop against the real Claude API.

    Each step is one real API call. After the call returns, this class reads
    the actual input/output token counts Anthropic reports (LangChain surfaces
    them on `AIMessage.usage_metadata`), converts them to a real dollar cost
    using per-token pricing, logs the step (including the token counts) via
    StepLogger, and reports that real cost to the Supervisor via check_step().
    If the Supervisor says to stop, no further API calls are made.
    """

    # Per-token pricing for claude-haiku-4-5, in USD per token.
    #
    # Anthropic publishes these as USD per million tokens (as of 2026-09:
    # $1.00 / MTok input, $5.00 / MTok output for Claude Haiku 4.5 -
    # https://www.anthropic.com/pricing). Divide by 1,000,000 to get a
    # per-token rate. These are hardcoded constants and WILL drift over time
    # as Anthropic updates pricing - verify against the pricing page above
    # before relying on this for real budget enforcement.
    INPUT_COST_PER_TOKEN = 1.00 / 1_000_000
    OUTPUT_COST_PER_TOKEN = 5.00 / 1_000_000

    DEFAULT_MODEL = "claude-haiku-4-5"
    """Cheapest current-generation Claude model - kept cheap deliberately
    since this agent is meant for exercising RuntimeGuard's cost tracking,
    not for production quality output."""

    def __init__(self, logger, supervisor, model: str = DEFAULT_MODEL):
        self.logger = logger
        self.supervisor = supervisor
        self.model = model

        # python-dotenv looks for a `.env` file in the current directory (and
        # parent directories) and loads any KEY=VALUE lines into os.environ,
        # without overriding variables already set in the real environment.
        load_dotenv()

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Set it in a .env file or in "
                "your environment before creating a RealAgent."
            )

        self.llm = ChatAnthropic(model=self.model, api_key=api_key, max_tokens=256)

    def _cost_for(self, usage_metadata: dict) -> float:
        """Convert one API call's real token usage into a real dollar cost.

        `usage_metadata` is the dict LangChain attaches to an AIMessage as
        `.usage_metadata`, with keys "input_tokens" and "output_tokens" taken
        directly from Anthropic's response (not estimated). Cost is just
        those counts multiplied by the per-token pricing constants above.
        """
        input_tokens = usage_metadata.get("input_tokens", 0)
        output_tokens = usage_metadata.get("output_tokens", 0)
        return (
            input_tokens * self.INPUT_COST_PER_TOKEN
            + output_tokens * self.OUTPUT_COST_PER_TOKEN
        )

    def run(self, task: str, max_iterations: int = 5):
        """Work through `task` in up to `max_iterations` real API calls.

        Each call is one step of a simple reasoning loop: the model is asked
        to think a little further and refine its answer, building on its own
        prior responses (kept as real conversation history). The last
        iteration asks for a final answer instead. After every call, the
        step (with real token counts and real cost) is logged, and the
        Supervisor is given the real cost via check_step() - if it says to
        stop, this method returns immediately without making another call.
        """
        print(f"Starting real task: {task}")

        messages = [
            SystemMessage(
                content=(
                    "You are working step by step on a task, refining your "
                    "answer across several short turns. Be concise."
                )
            ),
            HumanMessage(content=f"Task: {task}"),
        ]

        for i in range(1, max_iterations + 1):
            is_final = i == max_iterations
            if is_final:
                action_name = "final_answer"
                prompt = "Give your final, concise answer now."
            else:
                action_name = f"reasoning_step_{i}"
                prompt = (
                    f"Reasoning step {i} of up to {max_iterations}: think "
                    "briefly about the task and give your current best "
                    "partial answer in one or two sentences."
                )

            messages.append(HumanMessage(content=prompt))

            print(f"Step {i}: {action_name} (calling {self.model})")
            response: AIMessage = self.llm.invoke(messages)
            messages.append(response)

            usage = response.usage_metadata or {}
            cost = self._cost_for(usage)

            input_data = {"task": task, "iteration": i, "prompt": prompt}
            output_data = {
                "response": response.content,
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "cost": cost,
            }
            self.logger.log_step(action_name, input_data, output_data)

            should_continue = self.supervisor.check_step(cost, action_name, input_data)
            if not should_continue:
                print(f"Stopping early: {self.supervisor.stop_reason}")
                return

            if is_final:
                print("Task complete.")
                return
