# Authoring a Harbor eval task

A Harbor task gives an agent an instruction, a starting environment, and a
verifier that scores the result. For our coding tasks, start with one small,
testable change and use [krisj_fix_add](../tasks/krisj_fix_add/) as a working
example. Run the commands below from `evals/` with Docker running.
[Harbor task overview](https://docs.harborframework.com/tasks/overview).

## Create the task

Generate a local task with the installed Harbor CLI:

```sh
uv run --locked harbor task init local/my-task --tasks-dir tasks --no-package
```

This creates `tasks/my-task/`. `local` supplies the CLI's namespace;
`--no-package` omits registry metadata. Fill in these files:

| File | Purpose |
| --- | --- |
| `instruction.md` | The task the agent receives. |
| `task.toml` | Metadata, time limits, and resource settings. |
| `environment/Dockerfile` | Tools, dependencies, and starting files. |
| `solution/solve.sh` | A reference solution for the oracle agent. |
| `tests/test.sh` | Runs verification and writes the reward. |
| `tests/test_outputs.py` | Checks the resulting behavior. |

The solution is optional in Harbor, but include one while developing tasks so
you can confirm they are solvable.
[Task tutorial](https://docs.harborframework.com/tutorials/create-a-task),
[solution reference](https://docs.harborframework.com/tasks/solution).

## Write a clear instruction

Describe the required behavior, exact file paths, inputs, and constraints. Every
graded requirement should follow from this instruction. For example:

> Fix `add(a, b)` in `/app/calculator.py` so it returns the sum of two integers
> or floats, including negative values and zero. Keep its name and signature.

Keep agent prompting and tool-loop instructions in the agent implementation.
The task should describe an outcome that different agents can attempt.
[Instruction reference](https://docs.harborframework.com/tasks/instruction).

## Build the starting environment

Put the starter code beside the Dockerfile and copy it into the container:

```dockerfile
FROM python:3.12-slim-bookworm
RUN python -m pip install --no-cache-dir pytest==9.1.1
WORKDIR /app
COPY calculator.py /app/calculator.py
```

Install pytest and the task's dependencies here and pin versions where practical. Keep
reference solutions and hidden tests out of the starting image. Harbor supplies
the solution for oracle runs and uploads tests for verification.
[Environment reference](https://docs.harborframework.com/tasks/environment),
[verifier reference](https://docs.harborframework.com/tasks/verifier).

Keep the generated schema fields in `task.toml`; adjust the existing sections
to give the task suitable limits. For a small Python repair:

```toml
[agent]
timeout_sec = 120.0

[verifier]
timeout_sec = 30.0

[environment]
build_timeout_sec = 300.0
cpus = 1
memory_mb = 512
```

These are starting values for this example.
[Configuration reference](https://docs.harborframework.com/tasks/configuration).

## Write the solution and verifier

Make `solution/solve.sh` perform a correct repair without interactive input.
Harbor's oracle runs it to check the task against your verifier.
[Solution reference](https://docs.harborframework.com/tasks/solution).

Use pytest for all tests and examples in this project. In
`tests/test_outputs.py`, write test functions with plain assertions and use
`pytest.mark.parametrize` for related cases. For example:

```python
import pytest
from calculator import add


@pytest.mark.parametrize("a,b,expected", [(2, 3, 5), (-2, 3, 1), (0, 0, 0)])
def test_add(a, b, expected):
    assert add(a, b) == expected
```

Include normal inputs and relevant edge cases, such as negative values, zero,
and fractional inputs. Check results rather than requiring one implementation.
[Pytest assertions](https://docs.pytest.org/en/stable/how-to/assert.html),
[parametrization](https://docs.pytest.org/en/stable/how-to/parametrize.html).

Run pytest from `tests/test.sh`:

```bash
#!/bin/bash
set -uo pipefail

mkdir -p /logs/verifier
if PYTHONPATH=/app python -m pytest -q /tests/test_outputs.py; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
```

Harbor requires a numerical reward file; here, `1` means pass and `0` means fail.
The `if` handles test failures so the script still writes a reward. Use absolute
paths: Harbor runs the script from the task's working directory. `PYTHONPATH=/app`
lets the tests import the starter module. Pytest must be installed inside the
sandbox, as shown in the Dockerfile; the host `.venv` is separate.
[Verifier reference](https://docs.harborframework.com/tasks/verifier).

## Validate the task

```sh
chmod +x tasks/my-task/solution/solve.sh tasks/my-task/tests/test.sh
uv run --locked harbor run --path tasks/my-task --agent oracle --env docker
uv run --locked harbor run --path tasks/my-task --agent nop --env docker
uv run --locked harbor view jobs
```

For a repair task with binary grading, expect the oracle to earn **1** and the
no-op agent to earn **0**. Inspect verifier logs to confirm the baseline fails
because of the intended bug. Dependency or import errors also fail tests and
can hide a broken verifier. Try a few plausible incorrect repairs as well.
Harbor's tutorial describes oracle validation and inspecting results in the
viewer. [Task tutorial](https://docs.harborframework.com/tutorials/create-a-task).

Once these checks pass, evaluate with our custom agent using the command in the
[README](../README.md#build-the-agent), replacing the task path. Its model/tool
loop must be implemented first.
