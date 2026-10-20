.PHONY: setup check smoke oracle baseline

setup:
	uv sync --locked

check:
	uv run --locked ruff check .
	uv run --locked ruff format --check .

# Makes one billable OpenAI API request.
smoke:
	uv run --locked --env-file .env openai-smoke

# Verifies the task's reference solution without making model calls.
oracle:
	uv run --locked harbor run --path tasks --agent oracle --env docker

# The unmodified task should earn a reward of 0.
baseline:
	uv run --locked harbor run --path tasks --agent nop --env docker
