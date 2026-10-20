# Coding agent evals

A minimal Python 3.12 workspace for building our own coding agent with the
[OpenAI Python SDK](https://developers.openai.com/api/docs/quickstart) and
evaluating it with [Harbor](https://docs.harborframework.com/).

## Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and
[Docker Desktop](https://docs.docker.com/desktop/), then start Docker Desktop.
Run these commands from this `evals/` directory:

```sh
uv sync --locked
cp .env.example .env
```

Fill in `OPENAI_API_KEY` and `OPENAI_MODEL` in `.env`. Choose an API model ID
available to your OpenAI project, without a provider prefix. `.env` and generated
job results are ignored by Git. `uv run` uses the project's `.venv`; activating
the environment is optional.

Check code style, then verify the sandbox with a model-free run:

```sh
make check
make oracle
```

The oracle should earn reward **1**. `make baseline` runs a no-op agent and should
earn reward **0**, confirming the verifier catches the starter bug. The first run
downloads the Python Docker image and installs pinned pytest dependencies into
the task image. Verification needs no package installation at runtime.

To check API access, explicitly run the following command. It makes one billable
Responses API request using your configured model:

```sh
make smoke
```

`uv run --env-file .env ...` loads the local configuration for that command.
The oracle and baseline need neither an API key nor a model.

## Testing conventions

Use pytest for all project tests, task verifiers, and examples. Prefer test
functions with plain assertions, fixtures for shared setup, and
`pytest.mark.parametrize` for related cases. See the official pytest guides on
[assertions](https://docs.pytest.org/en/stable/how-to/assert.html) and
[parametrization](https://docs.pytest.org/en/stable/how-to/parametrize.html).

Run project tests with `uv run --locked python -m pytest` once they are added.
Task verifiers run inside Harbor through `make oracle` and `make baseline`;
the host pytest configuration excludes `tasks/` and `jobs/`. The sample task
installs pytest in its Docker image and runs `python -m pytest` from its verifier
script.

## Build the agent

`src/coding_agent/agent.py` contains an importable `CodingAgent` scaffold. Its
`run()` method intentionally raises `NotImplementedError` until we implement the
model/tool loop. `src/coding_agent/smoke.py` provides a minimal SDK example.

We use Harbor's external `BaseAgent` integration so the Python loop and OpenAI
client run locally, while commands operate on the task's Docker filesystem via
`await environment.exec(command=...)`. See
[Harbor's custom agent guide](https://docs.harborframework.com/agents/custom-agents).

The next implementation steps are to create an `AsyncOpenAI` client, call
`client.responses.create(...)`, expose a shell tool backed by `environment.exec`,
and repeat until the model finishes or reaches a step limit. Keep the API key in
the local agent process.

Once `run()` is implemented, evaluate it with:

```sh
uv run --env-file .env harbor run \
  --path tasks/hello-python \
  --agent coding_agent.agent:CodingAgent \
  --model openai/YOUR_MODEL_ID \
  --env docker
```

Replace `YOUR_MODEL_ID` with the model you chose. Harbor passes `--model` through
`self.model_name`; adapt the `openai/` provider prefix to the bare model ID before
using the OpenAI SDK. `OPENAI_MODEL` is read by the API smoke command; Harbor uses
its explicit `--model` option.

## Tasks and results

`tasks/hello-python/` is a tiny coding task: fix a broken `add()` function. Each
task has instructions, `task.toml`, an environment image, a reference solution,
and a verifier that writes `/logs/verifier/reward.txt`. See
[Harbor's task tutorial](https://docs.harborframework.com/tutorials/create-a-task).
For a short walkthrough with local examples, read
[Authoring a Harbor eval task](docs/authoring-tasks.md).

`tasks/add-input-validation/` is Charlotte's input-validation task: add type
checks to `add()` while preserving valid addition. It accepts integers and
floats, rejects booleans and other types with `TypeError`, and grades behavior
with pytest. Validate it without model calls:

```sh
make oracle TASK=tasks/add-input-validation
make baseline TASK=tasks/add-input-validation
```

Expect oracle reward **1** and baseline reward **0**. Without `TASK`, these
targets continue to run `hello-python`.

```sh
uv run --locked harbor task init local/my-task --tasks-dir tasks --no-package
uv run harbor view jobs
```

Harbor writes results and logs under `jobs/`. Python dependencies are recorded in
`uv.lock`. To deliberately update them, run `uv lock --upgrade` followed by
`uv sync --locked` and recheck the smoke task.
