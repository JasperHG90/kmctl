"""What every cost pilot shares: settings and tracing, the spending ledger, the claims, snippets and the models.

Settings come from the shell (the LangSmith and TypeSafe keys in ~/.zshrc) and then the notebook's .env, the
LangSmith settings that already work there (EU endpoint, agent id, environment). A value set in the shell wins.
Every DeepSeek call is traced by LangChain; every decision-model call by ``@traceable``.

The ledger (results/pilots/spend.json) adds up what the pilots spent and refuses a call that would pass the cap the
user agreed: 500k DeepSeek tokens (in plus out) and $1 of Jev, raised to 1.1M, 1.35M, 5M and then 10M tokens on 2026-11-10 (the user lifted the budget for measuring; the cap stays as a guard).
"""

import json
import os
import pathlib as plb
import re
import sqlite3
import subprocess
from dataclasses import dataclass
from typing import Any

import httpx
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langsmith import traceable
from platformdirs import user_data_dir

HERE = plb.Path(__file__).resolve().parents[2]
REPO = HERE.parents[2]
OUT = HERE / "results" / "pilots"
DB = plb.Path(user_data_dir("audit-cli")) / "projects" / "kmctl-f62c60167c76" / "audit.sqlite"
DEEPSEEK = "ollama/deepseek-v4.1-flash"
CLEF = "ollama/clef:27b"
JEV = "jev-latest"
BIFROST = "https://bifrost.lab.orangecluster.nl/v1"
JEV_URL = "https://api.typesafe.ai/v1/systemone"
TOKEN_CAP = 10_000_000
JEV_CAP_USD = 1.0
JEV_USD_PER_CALL = 0.0001
LEFT_OUT = (".okf/", ".loop/")


def settings() -> None:
    """Load the notebook's LangSmith settings under whatever the shell already set."""
    load_dotenv(HERE.parent / "audit-agent" / ".env", override=False)


class CapReached(RuntimeError):
    """A call would pass the agreed spending cap."""


class Ledger:
    """What the pilots spent, kept in a file so every pilot and every rerun counts against one cap."""

    def __init__(self, path: plb.Path = OUT / "spend.json") -> None:
        self.path = path
        self.data: dict[str, Any] = (
            json.loads(path.read_text()) if path.exists() else {"tokens": 0, "jev_calls": 0, "by_pilot": {}}
        )

    def check(self, tokens: int = 0, jev_calls: int = 0) -> None:
        """Raise when spending this much more would pass the cap."""
        if self.data["tokens"] + tokens > TOKEN_CAP:
            raise CapReached(f"{self.data['tokens']} + {tokens} tokens would pass the {TOKEN_CAP} cap")
        if (self.data["jev_calls"] + jev_calls) * JEV_USD_PER_CALL > JEV_CAP_USD:
            raise CapReached(f"{self.data['jev_calls'] + jev_calls} Jev calls would pass ${JEV_CAP_USD}")

    def add(self, pilot: str, tokens: int = 0, jev_calls: int = 0) -> None:
        """Record what a pilot spent and save."""
        self.data["tokens"] += tokens
        self.data["jev_calls"] += jev_calls
        mine = self.data["by_pilot"].setdefault(pilot, {"tokens": 0, "jev_calls": 0})
        mine["tokens"] += tokens
        mine["jev_calls"] += jev_calls
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=1))


@dataclass
class StoredClaim:
    """A claim from the database, with its sentence and where settle_claims.py found its named things."""

    claim_id: str
    chunk_id: str
    concept: str
    n: int
    kind: str
    text: str
    sentence: str
    anchors: list[dict[str, Any]]


def claims() -> list[StoredClaim]:
    """Return every stored claim, in document order, with its sentence and the settle step's anchors."""
    db = sqlite3.connect(DB)
    sentences = {cid: json.loads(s) for cid, s in db.execute("SELECT id, sentences FROM chunks")}
    settle = {}
    path = HERE / "results" / "settle" / "claims.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        settle[row["claim_id"]] = row["anchors"]
    rows = db.execute(
        "SELECT claim_id, chunk_id, sentence_n, claim_type, claim FROM claims ORDER BY chunk_id, sentence_n"
    ).fetchall()
    return [
        StoredClaim(cid, chunk, chunk.split("#")[0], n, kind, text, sentences[chunk][n - 1], settle.get(cid, []))
        for cid, chunk, n, kind, text in rows
    ]


def graded_ids() -> list[str]:
    """Return the 19 claims the check-writer pilot wrote checks for, which were graded by hand."""
    return list(json.loads((HERE / "results" / "checks" / "checks.json").read_text()))


def git_files() -> list[str]:
    """Return the repository's tracked files."""
    out = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z"], capture_output=True, text=True, check=True)
    return [f for f in out.stdout.split("\0") if f]


def located_files(claim: StoredClaim) -> list[str]:
    """Return the tracked files the settle step tied the claim to: paths found, definitions, mentions, scripts."""
    files: list[str] = []
    for anchor in claim.anchors:
        for where in anchor["where"]:
            path = where.split()[0]  # "action/agent.py publish" is a command of that script
            if (REPO / path).is_file() and path not in files:
                files.append(path)
    return files


def snippets(claim: StoredClaim, limit: int = 6000, around: int = 8) -> str:
    """Return the lines around each named thing in the files the settle step found, up to ``limit`` characters.

    A name found in a file gives the lines around its first three matches there; a found path that names a file
    gives its first 40 lines. Nothing is searched: only what the settle step already located is read.
    """
    parts: list[str] = []
    for anchor in claim.anchors:
        needle = anchor["text"].split()[-1].lstrip("-") if anchor["kind"] == "command" else anchor["text"]
        for where in anchor["where"][:3]:
            path = where.split()[0]
            if not (REPO / path).is_file() or path.startswith(LEFT_OUT) or path.endswith(".md"):
                continue
            lines = (REPO / path).read_text(errors="replace").splitlines()
            if anchor["kind"] == "path" and path == anchor["text"].rstrip("/"):
                parts.append(
                    f"--- {path} (first lines)\n" + "\n".join(f"{i}: {l}" for i, l in enumerate(lines[:40], 1))
                )
                continue
            hits = [i for i, line in enumerate(lines) if needle in line][:3]
            for i in hits:
                lo, hi = max(i - around, 0), min(i + around + 1, len(lines))
                parts.append(f"--- {path}:{lo + 1}-{hi}\n" + "\n".join(f"{j + 1}: {lines[j]}" for j in range(lo, hi)))
    text = "\n".join(dict.fromkeys(parts))  # one copy of a range two anchors share
    return text[:limit] or "(the settle step found nothing to show)"


def deepseek(effort: str | None = "low", timeout: int = 600) -> ChatOpenAI:
    """Return DeepSeek through Bifrost; effort None sends no reasoning_effort (the model's default)."""
    extra: dict[str, Any] = {"reasoning_effort": effort} if effort else {}
    return ChatOpenAI(
        base_url=BIFROST,
        api_key=os.environ["BIFROST_CC_VIRTUAL_KEY"],
        model=DEEPSEEK,
        timeout=timeout,
        max_retries=2,
        **extra,
    )


@traceable(run_type="llm", name="decision model")
async def decide(
    client: httpx.AsyncClient, model: str, state: dict[str, Any], questions: dict[str, Any]
) -> dict[str, Any]:
    """Ask a decision model typed questions; return each answer's probability of yes (a noul) or probabilities (a
    choice or a score).

    Clef sends a noul's probability as ``value``, Jev as ``noul``; a score also gives ``score``, its position.
    """
    if model == JEV:
        url, key = JEV_URL, os.environ["TYPESAFE_API_KEY"]
    else:
        url, key = f"{BIFROST}/decisions", os.environ["BIFROST_CC_VIRTUAL_KEY"]
    response = await client.post(
        url, headers={"Authorization": f"Bearer {key}"}, json={"model": model, "state": state, "questions": questions}
    )
    response.raise_for_status()
    return {
        name: a.get("probabilities", a.get("noul", a.get("value"))) for name, a in response.json()["answers"].items()
    }


def slug(text: str) -> str:
    """Return a file-safe name."""
    return re.sub(r"[^\w.-]+", "_", text)
