"""The starting point for our own coding agent."""

from harbor.agents.base import BaseAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class CodingAgent(BaseAgent):
    """Run the Python agent locally and execute its tools in Harbor's sandbox."""

    @staticmethod
    def name() -> str:
        return "coding-agent"

    def version(self) -> str:
        return "0.1.0"

    async def setup(self, environment: BaseEnvironment) -> None:
        """Task images provide the tools needed by the agent."""

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        # Build the model/tool loop here using openai.AsyncOpenAI().
        # Send shell tool calls to await environment.exec(command=...).
        # self.model_name is the model supplied through Harbor's --model option.
        raise NotImplementedError("Implement the OpenAI model/tool loop in CodingAgent.run().")
