# Project conventions

- This repository owns Harbor tasks and evaluation adapters only. Agent logic,
  standalone CLIs, and model-provider configuration belong in `../590_agents`.
- Keep the local-agent adapter generic: select an agent through `--ak agent=...`
  and install a source snapshot from the sibling package. Keep credentials out of
  uploaded source, commands, and version control.
- Use pytest for all Python tests, Harbor task verifiers, and documentation examples.
- Prefer test functions with plain assertions, pytest fixtures for setup, and
  `pytest.mark.parametrize` for related input cases.
- Task verifiers run inside Harbor's sandbox. Install pytest in the task image
  and invoke it with `python -m pytest` from `tests/test.sh`.
- After changing a task environment or verifier, run `make oracle` and
  `make baseline` to check that correct and incorrect starter code receive the
  expected rewards.
