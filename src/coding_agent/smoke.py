"""An explicit, small Responses API call to check local OpenAI configuration."""

import os

from openai import OpenAI


def main() -> None:
    """Run with: uv run --env-file .env openai-smoke."""
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        raise SystemExit("Set OPENAI_API_KEY in .env before running the API smoke check.")
    model = os.environ.get("OPENAI_MODEL", "").strip()
    if not model:
        raise SystemExit("Set OPENAI_MODEL in .env to an API model ID available to your project.")

    with OpenAI(timeout=30.0, max_retries=0) as client:
        response = client.responses.create(
            model=model,
            input="Reply with exactly: OpenAI connection OK",
            max_output_tokens=256,
            store=False,
        )
    print(response.output_text)


if __name__ == "__main__":
    main()
