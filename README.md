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

Fill in `OPENAI_API_KEY` with your UNC Azure subscription key and `OPENAI_MODEL`
with the exact deployment alias enabled for that subscription, without a provider
prefix. Keep `OPENAI_ENDPOINT=https://azureaiapi.cloud.unc.edu`. `.env` and generated
job results are ignored by Git. `uv run` uses the project's `.venv`; activating
the environment is optional.

Check code style, then verify the sandbox with a model-free run:

```sh
make check
make oracle
```

GitHub Actions runs `make check` and the project pytest tests on pull requests
and pushes to `main`, using the Python version in `.python-version` and
dependencies from `uv.lock`.

The oracle should earn reward **1**. `make baseline` runs a no-op agent and should
earn reward **0**, confirming the verifier catches the starter bug. The first run
downloads the Python Docker image and installs pinned pytest dependencies into
the task image. Verification needs no package installation at runtime.

To check API access, explicitly run the following command. It makes one billable
request to UNC's Azure Responses API using your configured deployment:

```sh
make smoke
```

`uv run --env-file .env ...` loads the local configuration for that command.
The oracle and baseline need neither an API key nor a model.

## UNC Azure configuration

The shared client factories in `src/coding_agent/provider.py` follow
LearnWithAI's current chat implementation: the standard `OpenAI` / `AsyncOpenAI`
SDK clients use `https://azureaiapi.cloud.unc.edu/openai/v1/` and send the UNC
subscription key as `Authorization: Bearer <key>`. This is the OpenAI-compatible
Responses v1 gateway, so it uses neither `AzureOpenAI` deployment URLs nor an
`api-version` query parameter. Responses requests set `store=False` and
`background=False`.

| Setting | Azure alias (takes precedence) | Value |
| --- | --- | --- |
| `OPENAI_API_KEY` | `AZURE_OPENAI_API_KEY` | UNC Azure subscription key; required |
| `OPENAI_MODEL` | `AZURE_OPENAI_DEPLOYMENT` | Deployment alias; required for smoke |
| `OPENAI_ENDPOINT` | `AZURE_OPENAI_ENDPOINT` | HTTPS endpoint origin; defaults to `https://azureaiapi.cloud.unc.edu` |

Use one naming scheme. An explicitly blank Azure alias overrides its legacy
setting and fails validation. LearnWithAI currently defaults to `gpt-5.6-luna`,
but this harness requires an explicit deployment: confirm which aliases your
subscription exposes rather than assuming a public OpenAI model ID will work.
Deployment aliases are passed unchanged to the gateway; only Harbor's optional
`openai/` prefix is removed.

Existing `.env` files must replace public OpenAI keys and model IDs with UNC
subscription credentials and deployment aliases. `OPENAI_BASE_URL` is ignored;
the client always sets its base URL explicitly. Endpoint overrides must be HTTPS
origins without paths, credentials, query strings, or fragments, and public
`openai.com` endpoints are rejected before sending a request. No credentials are
needed for project tests, which use mocked HTTP transports and run in CI.

Reference inspected for this migration: private LearnWithAI revision
`5c239db1b27abdb28c1969fbb1046ee0d700ea53`, particularly its
`learnwithai/config.py` aliases and `AiResponseStreamService` client setup. No
reference credentials or private application code are included here.

## Testing conventions

Use pytest for all project tests, task verifiers, and examples. Prefer test
functions with plain assertions, fixtures for shared setup, and
`pytest.mark.parametrize` for related cases. See the official pytest guides on
[assertions](https://docs.pytest.org/en/stable/how-to/assert.html) and
[parametrization](https://docs.pytest.org/en/stable/how-to/parametrize.html).

Run project tests with `uv run --locked python -m pytest`.
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

The next implementation steps are to load
`UNCOpenAISettings.from_env(model=self.model_name)` from `coding_agent.provider`,
open `settings.create_async_client()`, call `client.responses.create(...)` with
`model=settings.model`, `store=False`, and `background=False`, expose a shell tool
backed by `environment.exec`, and repeat until the model finishes or reaches a
step limit. Keep the subscription key in the local agent process. The scaffold
still raises `NotImplementedError`; this migration does not add the model loop.

Once `run()` is implemented, evaluate it with:

```sh
uv run --env-file .env harbor run \
  --path tasks/hello-python \
  --agent coding_agent.agent:CodingAgent \
  --model openai/YOUR_UNC_DEPLOYMENT \
  --env docker
```

Replace `YOUR_UNC_DEPLOYMENT` with the enabled UNC deployment alias. Harbor passes
`--model` through `self.model_name`; `UNCOpenAISettings.from_env(model=...)` strips
the `openai/` prefix and uses that deployment instead of the environment's model.
The prefix is a Harbor model label; the client factory selects the UNC endpoint.
`OPENAI_MODEL` (or `AZURE_OPENAI_DEPLOYMENT`) is read by the API smoke command;
Harbor uses its explicit `--model` option.

## Tasks and results

`tasks/hello-python/` is a tiny coding task: fix a broken `add()` function. Each
task has instructions, `task.toml`, an environment image, a reference solution,
and a verifier that writes `/logs/verifier/reward.txt`. See
[Harbor's task tutorial](https://docs.harborframework.com/tutorials/create-a-task).
For a short walkthrough with local examples, read
[Authoring a Harbor eval task](docs/authoring-tasks.md).

```sh
uv run --locked harbor task init local/my-task --tasks-dir tasks --no-package
uv run harbor view jobs
```

Harbor writes results and logs under `jobs/`. Run `make clean` to delete generated
jobs, Harbor state, Python/pytest/Ruff caches, coverage reports, and build outputs.
It preserves `.env`, `.venv`, Git data, source files, and the dependency lockfile.

Python dependencies are recorded in `uv.lock`. To deliberately update them, run
`uv lock --upgrade` followed by
`uv sync --locked` and recheck the smoke task.
