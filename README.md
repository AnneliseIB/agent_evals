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

Fill in `OPENAI_API_KEY` with your UNC Azure subscription key. `OPENAI_MODEL` is
the smoke command's deployment and an optional default for the agent; use Harbor's
`--model` or job config to select models for experiments. Values must be exact
deployment aliases enabled for your subscription. Keep
`OPENAI_ENDPOINT=https://azureaiapi.cloud.unc.edu`. `.env` and generated
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

Use one naming scheme. A blank Azure setting overrides its legacy setting;
validation fails if that setting is needed. A run-specific model takes precedence
over both model environment settings. LearnWithAI currently defaults to
`gpt-5.6-luna`, but this harness has no built-in deployment default: confirm which
aliases your subscription exposes rather than assuming a public OpenAI model ID
will work. Deployment aliases are passed unchanged to the gateway; only Harbor's
optional `openai/` prefix is removed.

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

The scaffold's `self.provider_settings()` already connects Harbor's
`self.model_name` to `UNCOpenAISettings.from_env(model=...)`. The next
implementation steps are to obtain those settings, open
`settings.create_async_client()`, call `client.responses.create(...)` with
`model=settings.model`, `store=False`, and `background=False`, expose a shell tool
backed by `environment.exec`, and repeat until the model finishes or reaches a
step limit. Keep the subscription key in the local agent process. The scaffold
still raises `NotImplementedError`; this migration does not add the model loop.

## Select models per experiment

Harbor's idiomatic model selector is `--model` (`-m`), or `agents[].model_name`
in a job config. No custom model flag or environment edits are needed. This was
checked against the installed, pinned **Harbor 0.24.0**: its CLI builds an
`AgentConfig` for each model, its `AgentFactory` forwards `model_name` to the
custom agent, and `BaseAgent` exposes it as `self.model_name`.

Preview a comparison now, without credentials, Docker, or model requests:

```sh
uv run --locked harbor run \
  --path tasks/hello-python \
  --agent coding_agent.agent:CodingAgent \
  --model openai/gpt-5.6-luna \
  --model openai/gpt-5.6-terra \
  --env docker --n-concurrent 1 --n-attempts 1 --max-retries 0 \
  --print-config
```

`--model` is repeatable: this creates two agent configurations against the same
task, one attempt each, with one concurrent trial and no trial retries. Use a
single `--model` for a one-model run. These two aliases come from LearnWithAI's
balanced and higher-capability defaults; replace them if your subscription uses
different deployment aliases. They are examples, not a promise of availability.

The same comparison is committed as
[`experiments/unc-model-comparison.yaml`](experiments/unc-model-comparison.yaml).
It uses two `agents` entries, each with
`import_path: coding_agent.agent:CodingAgent` and its own `model_name`. Paths are
relative to the current directory, so run these commands from the repository root:

```sh
# Preview the committed YAML; exits without running trials.
uv run --locked harbor run --config experiments/unc-model-comparison.yaml --print-config

# Override the YAML's agent/model list for a one-off comparison target.
uv run --locked harbor run --config experiments/unc-model-comparison.yaml \
  --agent coding_agent.agent:CodingAgent --model openai/gpt-5.6-terra --print-config
```

In 0.24.0, pair `--agent` with CLI `--model` overrides: the pair replaces the
config's entire `agents` list. `--model` alone does not override the YAML's model
list in this version. Without overrides, each YAML entry keeps its own model.

Once the student `run()` loop is implemented and the deployment aliases are
confirmed, an actual comparison uses the same config and the existing local key:

```sh
uv run --locked --env-file .env harbor run --config experiments/unc-model-comparison.yaml
```

That command is documented for later; it was not executed for this migration.
It needs Docker and can make billable model requests once the loop exists.
The preview commands above were executed, and tests exercise their parsed configs
through Harbor's real factory. `--print-config` checks config resolution, not
credentials, endpoint availability, or whether the student loop is implemented.

### Model precedence and deployment aliases

`CodingAgent.provider_settings()` uses this order:

1. The run's `self.model_name`, from CLI `--model` or YAML `agents[].model_name`.
2. `AZURE_OPENAI_DEPLOYMENT` when the run model is omitted (`None`).
3. `OPENAI_MODEL` when both of the above are absent.
4. A configuration error if no deployment is selected.

Blank or invalid explicit models fail rather than falling back. A blank Azure
deployment default also fails instead of using a legacy default; an explicit run
model still wins. `make smoke` uses the environment default because it does not
run through Harbor. Pin models in job configs for repeatable experiments:
environment fallbacks are resolved by this adapter and are not materialized into
Harbor's saved `model_name` config field.

The Harbor identifier `openai/course-balanced` becomes the API deployment alias
`course-balanced`. A bare `course-balanced` also works. `openai/` is a label in
this adapter; it never selects a public OpenAI endpoint. The UNC gateway routing
and credentials remain the same when switching models.

A portal's model display name (for example, a GPT model family/version) and its
deployment alias can differ. Pass the **deployment alias**, not a UI tier name
such as "balanced" or "frontier", unless that is the actual alias. This adapter
does not translate marketing names or maintain a model catalog. It supports only
UNC/Azure deployments that expose the Responses API and the capabilities needed
by the eventual agent loop; availability, tool support, context limits, and
reasoning settings must be checked for each deployment. Other provider prefixes
such as `anthropic/` or `azure/` are rejected; supporting a different API requires
a separate adapter. No live model qualification was performed here.

### Harbor references

- [Custom agents: `--model` and external `BaseAgent`](https://docs.harborframework.com/agents/custom-agents)
- [Job configuration: `agents[].model_name` and multiple agents](https://docs.harborframework.com/jobs/configs)
- [0.24.0 CLI source: repeatable model selection and config overrides](https://github.com/harbor-framework/harbor/blob/v0.24.0/src/harbor/cli/jobs.py)
- [0.24.0 agent factory: forwards `config.model_name`](https://github.com/harbor-framework/harbor/blob/v0.24.0/src/harbor/agents/factory.py)
- [0.24.0 base agent: stores `self.model_name`](https://github.com/harbor-framework/harbor/blob/v0.24.0/src/harbor/agents/base.py)

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
