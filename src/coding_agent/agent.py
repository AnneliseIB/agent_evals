"""The starting point for our own coding agent."""

from harbor.agents.base import BaseAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

from coding_agent.provider import UNCOpenAISettings


class CodingAgent(BaseAgent):
    """Run the Python agent locally and execute its tools in Harbor's sandbox."""

    @staticmethod
    def name() -> str:
        return "coding-agent"

    def version(self) -> str:
        return "0.1.0"

    def provider_settings(self) -> UNCOpenAISettings:
        """Prefer Harbor's per-run model; use the environment only as a default."""
        return UNCOpenAISettings.from_env(model=self.model_name)

    async def setup(self, environment: BaseEnvironment) -> None:
        """Task images provide the tools needed by the agent."""

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        # Start with settings = self.provider_settings(), then open
        # settings.create_async_client() and use model=settings.model.
        # Send Responses requests with store=False and background=False.
        # Send shell tool calls to await environment.exec(command=...).
        # Settings maps Harbor's openai/ prefix to the UNC deployment name.
        raise NotImplementedError("Implement the UNC Azure model/tool loop in CodingAgent.run().")
