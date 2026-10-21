"""Install any agent from the sibling CLI project into a Harbor task sandbox."""

import shlex
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from dotenv import dotenv_values
from harbor.agents.installed.base import BaseInstalledAgent
from harbor.agents.options import InstalledAgentOptions
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext
from pydantic import Field

_INSTALL_DIR = "/installed-agent/agents590"
_SOURCE_DIR = f"{_INSTALL_DIR}/source"
_VENV_DIR = f"{_INSTALL_DIR}/venv"
_PYTHON = f"{_VENV_DIR}/bin/python"
_UV_VERSION = "0.10.6"


class LocalAgentOptions(InstalledAgentOptions):
    """Adapter settings, supplied through Harbor's --ak options."""

    agent: str = Field(
        default="krisj_coding", min_length=1, description="Registered agents590 agent"
    )
    package_path: Path = Field(default=Path("../590_agents"), description="Local package root")
    env_file: Path | None = Field(default=None, description="Host-only agent environment file")


def stage_package(package_path: Path, destination: Path) -> None:
    """Snapshot only installable source and metadata, excluding checkout secrets and results."""
    root = package_path.expanduser().resolve()
    if (
        not (root / "pyproject.toml").is_file()
        or not (root / "uv.lock").is_file()
        or not (root / "src").is_dir()
    ):
        raise ValueError("package_path must contain pyproject.toml, uv.lock, and src/")
    for name in ("pyproject.toml", "README.md", "uv.lock"):
        source = root / name
        if source.is_file():
            shutil.copy2(source, destination / name)
    shutil.copytree(
        root / "src",
        destination / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".env", ".env.*"),
    )


class LocalCliAgent(BaseInstalledAgent):
    """A generic evaluation adapter; the sibling package owns all agent behavior."""

    options_model = LocalAgentOptions
    options: LocalAgentOptions

    @staticmethod
    def name() -> str:
        return "local-cli-agent"

    async def install(self, environment: BaseEnvironment) -> None:
        with TemporaryDirectory(prefix="harbor-local-agent-") as directory:
            stage = Path(directory)
            stage_package(self.options.package_path, stage)
            await environment.upload_dir(stage, _SOURCE_DIR)

        await self.ensure_system_dependencies(environment, ("curl",))
        user = shlex.quote(str(environment.default_user or "root"))
        await self.exec_as_root(
            environment,
            command=f"mkdir -p {_INSTALL_DIR} && chown -R {user} {_INSTALL_DIR}",
        )
        await self.exec_as_agent(
            environment,
            command=(
                "set -eu; "
                "if ! command -v uv >/dev/null 2>&1; then "
                f"curl -LsSf https://astral.sh/uv/{_UV_VERSION}/install.sh | "
                f"env UV_INSTALL_DIR={_INSTALL_DIR}/bin UV_NO_MODIFY_PATH=1 sh; fi; "
                f"export PATH={_INSTALL_DIR}/bin:$PATH; "
                f"UV_PROJECT_ENVIRONMENT={_VENV_DIR} "
                f"uv sync --locked --no-dev --python 3.12 --project {_SOURCE_DIR}"
            ),
            timeout_sec=300,
        )

    async def run(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ) -> None:
        command = [_PYTHON, "-m", "agents590", self.options.agent, "-i", instruction]
        if self.model_name is not None:
            command.extend(("--model", self.model_name))
        env: dict[str, str] = {}
        if self.options.env_file is not None:
            env_file = self.options.env_file.expanduser().resolve()
            if not env_file.is_file():
                raise ValueError("env_file must name an existing host file")
            env = {
                key: value for key, value in dotenv_values(env_file).items() if value is not None
            }
        env.update(self.extra_env)
        result = await self.exec_as_agent(
            environment,
            command=shlex.join(command),
            env=env,
            cwd=environment.task_env_config.workdir,
        )
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.logs_dir / "stdout.txt").write_text(result.stdout or "")
        (self.logs_dir / "stderr.txt").write_text(result.stderr or "")
        context.metadata = {"agent": self.options.agent}
