"""Shared fixtures: every test gets its own data folder and a small repository with a bundle."""

import pathlib as plb
import subprocess
from typing import Any, cast

import pytest
from langsmith import utils as langsmith_utils

from audit_cli.logs import configure_logging

CONCEPT = """---
type: decision
title: Use a queue
status: stable
---

# Use a queue

## Context

The CLI writes jobs to `jobs.db`. Each worker reads one job at a time.

## Decision

- The worker retries a failed job three times.
- It never writes outside `.okf/`.

## Correction, 2026-01-02

The worker retries twice, not three times.
"""


@pytest.fixture(autouse=True)
def data_dir(tmp_path: plb.Path, monkeypatch: pytest.MonkeyPatch) -> plb.Path:
    """Point the data and log folders and the working folder at temporary ones, so no test touches real ones."""
    folder = tmp_path / "data"
    monkeypatch.setenv("AUDIT_CLI_DATA_DIR", str(folder))
    monkeypatch.setenv("AUDIT_CLI_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.chdir(tmp_path)  # no audit.toml or .env from the folder the tests run in
    for name in [
        "LANGSMITH_API_KEY",
        "LANGSMITH_PROJECT",
        "LANGSMITH_TRACING",
        "LANGSMITH_TRACING_V2",
        "LANGCHAIN_TRACING_V2",
        "LANGSMITH_AGENT_ID",
        "LANGSMITH_AGENT_ENVIRONMENT",
    ]:
        monkeypatch.delenv(name, raising=False)  # restored after the test, even when the CLI set it
    cast(Any, langsmith_utils.get_env_var).cache_clear()  # the SDK caches variables; start each test fresh
    configure_logging(tmp_path / "logs" / "tests.log", "debug")  # keep library events out of the test output
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    return folder


def git(root: plb.Path, *args: str) -> None:
    """Run git in ``root``."""
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: plb.Path) -> plb.Path:
    """Return a git repository with code, an ignored file and a small .okf/ bundle."""
    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "src" / "worker.py").write_text("def retry(job):\n    return job\n")
    (root / "src" / "cache.pyc").write_bytes(b"\x00\x01")
    (root / "notes.txt").write_text("not an included extension\n")
    (root / "build").mkdir()
    (root / "build" / "out.py").write_text("x = 1\n")
    (root / ".gitignore").write_text("build/\n")
    (root / "vendor").mkdir()
    (root / "vendor" / "lib.py").write_text("y = 2\n")
    bundle = root / ".okf"
    (bundle / "decisions").mkdir(parents=True)
    (bundle / "index.md").write_text('---\nokf_version: "0.2"\n---\n\n# Index\n\nNot a concept.\n')
    (bundle / "decisions" / "0001-use-a-queue.md").write_text(CONCEPT)
    (bundle / "decisions" / "0002-old.md").write_text(
        "---\ntype: decision\ntitle: Old\nstatus: deprecated\n---\n\n# Old\n\n## Context\n\nGone now.\n"
    )
    (bundle / "prototypes").mkdir()
    (bundle / "prototypes" / "spike.md").write_text(
        "---\ntype: prototype\ntitle: Spike\n---\n\n# Spike\n\nSkipped folder.\n"
    )
    (root / "audit.toml").write_text('[agents.extractor]\nprovider = "openai"\nmodel = "test-model"\n')
    git(root, "init", "-q")
    git(root, "add", "-A")
    return root
