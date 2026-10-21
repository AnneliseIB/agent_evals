.PHONY: setup check clean smoke oracle baseline

setup:
	uv sync --locked

check:
	uv run --locked ruff check .
	uv run --locked ruff format --check .

clean:
	rm -rf jobs .harbor htmlcov build dist
	rm -f .coverage .coverage.*
	find . -type d \( -name .git -o -name .venv \) -prune -o \
		-type d \( -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache -o -name '*.egg-info' \) \
		-prune -exec rm -rf {} +

# Makes one billable UNC Azure Responses API request.
smoke:
	uv run --locked --env-file .env openai-smoke

# Verifies the task's reference solution without making model calls.
oracle:
	uv run --locked harbor run --path tasks --agent oracle --env docker

# The unmodified task should earn a reward of 0.
baseline:
	uv run --locked harbor run --path tasks --agent nop --env docker
