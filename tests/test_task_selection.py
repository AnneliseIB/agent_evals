"""Resolve real Harbor task selections through both make and the native CLI."""

import asyncio
import shutil
import subprocess
from pathlib import Path

import pytest
from harbor.cli.main import app
from harbor.models.job.config import JobConfig
from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[1]


def _task_names(config: JobConfig) -> set[str]:
    names = {task.path.name for task in config.tasks}
    for dataset in config.datasets:
        names.update(task.path.name for task in asyncio.run(dataset.get_task_configs()))
    return names


@pytest.mark.parametrize("target", ["agent", "oracle", "baseline"])
@pytest.mark.parametrize(
    ("selection", "expected"),
    [
        ("", None),
        ("krisj_fix_add", {"krisj_fix_add"}),
        ("krisj_fix_add lucasdmo_feature_merge", {"krisj_fix_add", "lucasdmo_feature_merge"}),
        ("lucasdmo_*", {"lucasdmo_feature_merge", "lucasdmo_rebase_conflicts"}),
    ],
)
def test_make_targets_resolve_all_tasks_or_the_selected_subset(
    target: str, selection: str, expected: set[str] | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HARBOR_TELEMETRY", "0")
    result = subprocess.run(
        ["make", "--silent", target, "ARGS=--print-config", f"TASKS={selection}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    config = JobConfig.model_validate_json(result.stdout)
    if expected is None:
        expected = {path.parent.name for path in (ROOT / "tasks").glob("*/task.toml")}
    assert _task_names(config) == expected
    if target == "agent":
        assert config.agents[0].kwargs["agent"] == "krisj_starter"


def test_dataset_discovers_tasks_added_after_config_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HARBOR_TELEMETRY", "0")
    dataset = tmp_path / "tasks"
    shutil.copytree(ROOT / "tasks/krisj_fix_add", dataset / "first")
    result = CliRunner().invoke(app, ["run", "--path", str(dataset), "--print-config"])
    assert result.exit_code == 0, result.output
    config = JobConfig.model_validate_json(result.stdout)
    assert _task_names(config) == {"first"}

    shutil.copytree(ROOT / "tasks/krisj_fix_add", dataset / "new_task")
    assert _task_names(config) == {"first", "new_task"}


def test_comparison_config_accepts_repeatable_native_task_filters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HARBOR_TELEMETRY", "0")
    result = CliRunner().invoke(
        app,
        [
            "run",
            "--config",
            str(ROOT / "experiments/model-comparison.yaml"),
            "--path",
            "tasks",
            "--include-task-name",
            "krisj_fix_add",
            "--include-task-name",
            "lucasdmo_feature_merge",
            "--print-config",
        ],
    )
    assert result.exit_code == 0, result.output
    assert _task_names(JobConfig.model_validate_json(result.stdout)) == {
        "krisj_fix_add",
        "lucasdmo_feature_merge",
    }
