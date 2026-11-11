"""Probe whether DeepSeek's thinking can be turned down through Bifrost: one tiny prompt, three settings.

Run from the audit-cli folder: uv run python scripts/probe/thinking.py
"""

import time

from dotenv import find_dotenv, load_dotenv
from langchain_openai import ChatOpenAI

from audit_cli.config import load_config

PROMPT = "A YAML file has jobs.build.steps, a list. Write a JMESPath query for the `with.enable-cache` value of every step whose `uses` starts with astral-sh/setup-uv. Answer with the query only."
SETTINGS: dict[str, dict[str, object]] = {
    "default": {},
    "reasoning_effort low": {"reasoning_effort": "low"},
    "think false": {"extra_body": {"think": False}},
    "reasoning disabled": {"extra_body": {"reasoning": {"enabled": False}}},
}


def main() -> None:
    """Print output tokens, reasoning tokens and seconds per setting."""
    load_dotenv(find_dotenv(usecwd=True))
    config = load_config(None, search=[__import__("pathlib").Path.cwd()])
    agent = config.agents["extractor"]
    provider = config.providers[agent.provider]
    for name, extra in SETTINGS.items():
        llm = ChatOpenAI(
            base_url=provider.base_url, api_key=provider.api_key(), model=agent.model, timeout=300, **extra
        )
        start = time.monotonic()
        try:
            answer = llm.invoke(PROMPT)
        except Exception as error:  # noqa: BLE001  # a refused setting is a result too
            print(f"{name:22} refused: {type(error).__name__}: {str(error)[:150]}")
            continue
        usage = answer.usage_metadata
        reasoning = usage.get("output_token_details", {}).get("reasoning", "?") if usage else "?"
        print(
            f"{name:22} out={usage['output_tokens'] if usage else '?'} reasoning={reasoning} s={time.monotonic() - start:.0f} | {str(answer.content)[:80]!r}"
        )


if __name__ == "__main__":
    main()
