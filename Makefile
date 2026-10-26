.PHONY: setup check test clean agent oracle baseline

AGENTS_PROJECT ?= ../590_agents
AGENT ?= krisj_starter
TASKS ?=
MODEL ?=
ENV_FILE ?=
ARGS ?=

TASK_FLAGS = $(foreach task,$(TASKS),--include-task-name "$(task)")

setup:
	uv sync --locked

check:
	uv run --locked ruff check .
	uv run --locked ruff format --check .
	uv run --locked pyright

test:
	uv run --locked python -m pytest

clean:
	rm -rf jobs .harbor htmlcov build dist
	rm -f .coverage .coverage.*
	find . -type d \( -name .git -o -name .venv \) -prune -o \
		-type d \( -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache -o -name '*.egg-info' \) \
		-prune -exec rm -rf {} +

# Run all tasks by default; TASKS accepts task names or glob patterns.
agent:
	uv run --locked harbor run --path tasks $(TASK_FLAGS) \
		--agent eval_adapters.local:LocalCliAgent --env docker \
		--ak agent="$(AGENT)" --ak package_path="$(AGENTS_PROJECT)" \
		$(if $(MODEL),--model "$(MODEL)",) \
		$(if $(ENV_FILE),--ak env_file="$(ENV_FILE)",) $(ARGS)

# Verifies the task's reference solution without making model calls.
oracle:
	uv run --locked harbor run --path tasks $(TASK_FLAGS) --agent oracle --env docker $(ARGS)

# The unmodified task should earn a reward of 0.
baseline:
	uv run --locked harbor run --path tasks $(TASK_FLAGS) --agent nop --env docker $(ARGS)
