"""Exercise Harbor's real config/factory boundary without running any trials."""

import asyncio
import json
import os
from functools import partial
from pathlib import Path
from typing import cast

import httpx
import pytest
from harbor.agents.factory import AgentFactory
from harbor.cli.main import app
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext
from harbor.models.job.config import JobConfig
from harbor.models.trial.config import AgentConfig
from openai import AsyncOpenAI
from typer.testing import CliRunner

from coding_agent import provider
from coding_agent.agent import CodingAgent
from coding_agent.provider import UNC_ENDPOINT

AGENT_PATH = "coding_agent.agent:CodingAgent"
COMPARISON_CONFIG = Path(__file__).resolve().parents[1] / "experiments/unc-model-comparison.yaml"


@pytest.fixture(autouse=True)
def isolated_provider_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name.startswith(("OPENAI_", "AZURE_OPENAI_")):
            monkeypatch.delenv(name)
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-unc-key")
    monkeypatch.setenv("HARBOR_TELEMETRY", "0")


def _job_from_cli(*args: str) -> JobConfig:
    result = CliRunner().invoke(app, ["run", *args, "--print-config"])
    assert result.exit_code == 0, result.output
    return JobConfig.model_validate_json(result.stdout)


def _agent(config: AgentConfig, tmp_path: Path) -> CodingAgent:
    agent = AgentFactory.create_agent_from_config(config, logs_dir=tmp_path)
    assert isinstance(agent, CodingAgent)
    return agent


def test_repeatable_cli_models_reach_each_custom_agent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "environment-default")
    config = _job_from_cli(
        "--path",
        "tasks/hello-python",
        "--agent",
        AGENT_PATH,
        "--model",
        "openai/balanced-deployment",
        "--model",
        "openai/frontier-deployment",
        "--n-concurrent",
        "1",
        "--n-attempts",
        "1",
        "--max-retries",
        "0",
    )
    assert [agent.model_name for agent in config.agents] == [
        "openai/balanced-deployment",
        "openai/frontier-deployment",
    ]
    for agent_config in config.agents:
        agent = _agent(agent_config, tmp_path)
        assert agent.model_name == agent_config.model_name
        assert agent.provider_settings().model == agent.model_name.removeprefix("openai/")


def test_comparison_yaml_reaches_each_custom_agent(tmp_path: Path) -> None:
    config = _job_from_cli("--config", str(COMPARISON_CONFIG))
    assert config.n_attempts == 1
    assert config.n_concurrent_trials == 1
    assert config.retry.max_retries == 0
    assert [task.path for task in config.tasks] == [Path("tasks/hello-python")]
    assert [_agent(agent, tmp_path).provider_settings().model for agent in config.agents] == [
        "gpt-5.6-luna",
        "gpt-5.6-terra",
    ]


def test_cli_agent_and_model_replace_config_agents(tmp_path: Path) -> None:
    config = _job_from_cli(
        "--config",
        str(COMPARISON_CONFIG),
        "--agent",
        AGENT_PATH,
        "--model",
        "openai/one-off-deployment",
    )
    assert len(config.agents) == 1
    assert _agent(config.agents[0], tmp_path).provider_settings().model == "one-off-deployment"


def test_model_only_cli_flag_keeps_yaml_agents() -> None:
    config = _job_from_cli("--config", str(COMPARISON_CONFIG), "--model", "openai/unused-override")
    assert [agent.model_name for agent in config.agents] == [
        "openai/gpt-5.6-luna",
        "openai/gpt-5.6-terra",
    ]


def test_cli_without_model_uses_environment_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_MODEL", "default-deployment")
    config = _job_from_cli("--path", "tasks/hello-python", "--agent", AGENT_PATH)
    assert config.agents[0].model_name is None
    assert _agent(config.agents[0], tmp_path).provider_settings().model == "default-deployment"


@pytest.mark.parametrize(
    ("run_model", "azure_default", "legacy_default", "expected"),
    [
        ("openai/run-deployment", "azure-default", "legacy-default", "run-deployment"),
        ("bare-run-deployment", None, None, "bare-run-deployment"),
        ("openai/run-deployment", "", "", "run-deployment"),
        (None, "azure-default", "legacy-default", "azure-default"),
        (None, None, "legacy-default", "legacy-default"),
    ],
)
def test_run_model_then_azure_then_legacy_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    run_model: str | None,
    azure_default: str | None,
    legacy_default: str | None,
    expected: str,
) -> None:
    for name, value in [
        ("AZURE_OPENAI_DEPLOYMENT", azure_default),
        ("OPENAI_MODEL", legacy_default),
    ]:
        if value is not None:
            monkeypatch.setenv(name, value)
    agent = _agent(AgentConfig(import_path=AGENT_PATH, model_name=run_model), tmp_path)
    assert agent.provider_settings().model == expected


@pytest.mark.parametrize("model", ["", " ", "openai/", "anthropic/model", "azure/model"])
def test_invalid_explicit_model_never_falls_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, model: str
) -> None:
    monkeypatch.setenv("OPENAI_MODEL", "working-default")
    agent = _agent(AgentConfig(import_path=AGENT_PATH, model_name=model), tmp_path)
    with pytest.raises(ValueError):
        agent.provider_settings()


def test_no_run_model_or_default_fails(tmp_path: Path) -> None:
    agent = _agent(AgentConfig(import_path=AGENT_PATH), tmp_path)
    with pytest.raises(ValueError, match="OPENAI_MODEL"):
        agent.provider_settings()


def test_agent_selected_deployment_keeps_unc_sdk_routing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "environment-default")
    requests: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"id": "resp_mock", "output": []})

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handle))
    monkeypatch.setattr(provider, "AsyncOpenAI", partial(AsyncOpenAI, http_client=http_client))
    agent = _agent(AgentConfig(import_path=AGENT_PATH, model_name="openai/run-alias"), tmp_path)
    settings = agent.provider_settings()

    async def request() -> None:
        async with settings.create_async_client() as client:
            await client.responses.create(
                model=settings.model, input="synthetic test", store=False, background=False
            )

    asyncio.run(request())
    assert len(requests) == 1
    assert str(requests[0].url) == f"{UNC_ENDPOINT}/openai/v1/responses"
    assert json.loads(requests[0].content)["model"] == "run-alias"
    assert requests[0].headers["authorization"] == "Bearer synthetic-unc-key"
    assert http_client.is_closed


def test_model_override_cannot_enable_public_endpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_ENDPOINT", "https://api.openai.com")
    agent = _agent(AgentConfig(import_path=AGENT_PATH, model_name="openai/run-alias"), tmp_path)
    with pytest.raises(ValueError, match="public OpenAI endpoints are disabled"):
        agent.provider_settings()


def test_student_loop_remains_unimplemented(tmp_path: Path) -> None:
    agent = _agent(AgentConfig(import_path=AGENT_PATH), tmp_path)
    with pytest.raises(NotImplementedError):
        asyncio.run(agent.run("test", cast(BaseEnvironment, None), AgentContext()))
