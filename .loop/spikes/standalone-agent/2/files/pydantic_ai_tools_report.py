# /// script
# requires-python = ">=3.11"
# dependencies = ["pydantic-ai-slim[openai]==2.57.0"]
# ///
"""Spike: does PydanticAI run tool calls and a typed final report through a
plain OpenAI-compatible endpoint? Exit 0 only when each tool ran at least once
and the output validated as Report.

Env: SPIKE_BASE_URL, SPIKE_API_KEY, SPIKE_MODEL (comma list; all must pass).
"""

import os
import subprocess
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider


class Finding(BaseModel):
    title: str
    severity: Literal["low", "medium", "high"]
    path: str
    evidence: list[str]


class Report(BaseModel):
    summary: str
    findings: list[Finding]


root = Path(tempfile.mkdtemp())
(root / "docs").mkdir()
(root / "docs" / "install.md").write_text(
    "# Install\n\nRun `pip install widget==1.0` to install.\n"
)
(root / "VERSION").write_text("2.3.0\n")

ok = True
for name in os.environ["SPIKE_MODEL"].split(","):
    model = OpenAIChatModel(
        name,
        provider=OpenAIProvider(
            base_url=os.environ["SPIKE_BASE_URL"], api_key=os.environ["SPIKE_API_KEY"]
        ),
    )
    agent = Agent(
        model,
        output_type=Report,
        instructions="You audit a small repository. Use the tools; do not guess.",
    )


    @agent.tool_plain
    def read_file(path: str) -> str:
        """Read a file in the repository, by path relative to its root."""
        return (root / path).read_text()


    @agent.tool_plain
    def run_shell(cmd: str) -> str:
        """Run a shell command in the repository root and return its output."""
        p = subprocess.run(
            cmd,
            shell=True,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
            env={"PATH": os.environ["PATH"], "HOME": str(root)},
        )
        return f"exit {p.returncode}\n{p.stdout}{p.stderr}"


    result = agent.run_sync(
        "Read docs/install.md with read_file. Then use run_shell to run `cat VERSION`. "
        "Report whether the version the install doc names matches VERSION, as findings "
        "with evidence quoted from both."
    )

    calls = [
        part.tool_name
        for msg in result.all_messages()
        if isinstance(msg, ModelResponse)
        for part in msg.parts
        if isinstance(part, ToolCallPart)
    ]
    print("pydantic-ai-slim", version("pydantic-ai-slim"))
    print("model", name)
    print("tool calls in order:", calls)
    print("output type:", type(result.output).__name__)
    print(result.output.model_dump_json(indent=2))
    print("usage:", result.usage)

    ok = ok and (
        isinstance(result.output, Report)
        and "read_file" in calls
        and "run_shell" in calls
    )
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
