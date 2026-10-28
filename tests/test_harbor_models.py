"""Exercise Harbor's real config/factory boundary without model or Docker calls."""

from pathlib import Path

import pytest
from harbor.agents.factory import AgentFactory
from harbor.cli.main import app
from harbor.models.job.config import JobConfig
from harbor.models.trial.config import AgentConfig
from typer.testing import CliRunner

from eval_adapters.local import LocalCliAgent

AGENT_PATH = "eval_adapters.local:LocalCliAgent"
COMPARISON_CONFIG = Path(__file__).resolve().parents[1] / "experiments/model-comparison.yaml"


@pytest.fixture(autouse=True)
def disable_telemetry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HARBOR_TELEMETRY", "0")


def _job_from_cli(*args: str) -> JobConfig:
    result = CliRunner().invoke(app, ["run", *args, "--print-config"])
    assert result.exit_code == 0, result.output
    return JobConfig.model_validate_json(result.stdout)


def _agent(config: AgentConfig, tmp_path: Path) -> LocalCliAgent:
    agent = AgentFactory.create_agent_from_config(config, logs_dir=tmp_path)
    assert isinstance(agent, LocalCliAgent)
    return agent


def test_repeatable_models_and_agent_selection_reach_the_adapter(tmp_path: Path) -> None:
    config = _job_from_cli(
        "--path",
        "tasks",
        "--agent",
        AGENT_PATH,
        "--ak",
        "agent=krisj_echo",
        "--model",
        "openai/first-deployment",
        "--model",
        "openai/second-deployment",
    )
    agents = [_agent(config, tmp_path) for config in config.agents]
    assert [agent.model_name for agent in agents] == [
        "openai/first-deployment",
        "openai/second-deployment",
    ]
    assert all(agent.options.agent == "krisj_echo" for agent in agents)


def test_comparison_yaml_reaches_the_generic_adapter(tmp_path: Path) -> None:
    config = _job_from_cli("--config", str(COMPARISON_CONFIG))
    assert config.n_attempts == 1
    assert config.n_concurrent_trials == 1
    assert config.retry.max_retries == 0
    assert config.tasks == []
    assert [dataset.path for dataset in config.datasets] == [Path("tasks")]
    assert all(dataset.task_names is None for dataset in config.datasets)
    agents = [_agent(config, tmp_path) for config in config.agents]
    assert [agent.model_name for agent in agents] == [
        "openai/gpt-5.6-luna",
        "openai/gpt-5.6-terra",
    ]
    assert all(agent.options.agent == "krisj_starter" for agent in agents)


def test_cli_agent_and_model_replace_yaml_agents(tmp_path: Path) -> None:
    config = _job_from_cli(
        "--config",
        str(COMPARISON_CONFIG),
        "--agent",
        AGENT_PATH,
        "--ak",
        "agent=krisj_echo",
        "--model",
        "openai/override",
    )
    assert len(config.agents) == 1
    agent = _agent(config.agents[0], tmp_path)
    assert agent.model_name == "openai/override"
    assert agent.options.agent == "krisj_echo"


def test_model_only_override_keeps_yaml_agents() -> None:
    config = _job_from_cli("--config", str(COMPARISON_CONFIG), "--model", "unused")
    assert [agent.model_name for agent in config.agents] == [
        "openai/gpt-5.6-luna",
        "openai/gpt-5.6-terra",
    ]
