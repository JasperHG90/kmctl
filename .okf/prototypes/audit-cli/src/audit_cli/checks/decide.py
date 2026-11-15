"""A decision model: typed questions about a claim in, probabilities out.

It answers two questions in the checks stage:

- failure: a check failed. Does what its steps saw show the claim is false (drift), or was the check written wrong?
  It ranks failures so a person reads the likely drift first, and marks wrong checks to be written again.
- judge: a claim has no check. Do the lines found for it show it true, false, or neither? Fit for claims about prose
  (what a prompt or skill says), which a check reads only as text; weak on absence over files the lines do not show.

The endpoint takes ``{model, state, questions}`` and answers each question by name: a noul as a probability of yes
(``noul`` or ``value``), a choice as ``probabilities`` per option. TypeSafe's systemone endpoint (Jev) and a gateway's
decisions endpoint (Clef) both answer this way.
"""

import hashlib
import json
from typing import Any

import httpx
from langsmith import traceable
from pydantic import BaseModel, Field, ValidationError
from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt, wait_exponential_jitter

from audit_cli.config import DecisionsConfig

FAILURE = {
    "claim_false": {
        "type": "noul",
        "instructions": "A check was written to test the claim and it failed. Does what its steps saw show that the "
        "claim is false about the repository, rather than that the check was written wrong (wrong files, a guessed "
        "pattern, a syntax error, a word that does not have to be there)?",
    },
    "cause": {
        "type": "choice",
        "instructions": "Why did the check fail?",
        "criteria": {
            "claim_false": "what the steps saw contradicts the claim: the repository is not as the claim says",
            "check_wrong": "the check looked in the wrong place, guessed code it was not shown, could not run, or "
            "tested something the claim does not need",
            "unclear": "what the steps saw does not settle it either way",
        },
    },
}
JUDGE = {
    "shown_true": {
        "type": "noul",
        "instructions": "Do the lines shown establish that the claim is true of the repository? Lines that only "
        "mention what the claim names, without showing what it says about them, do not.",
    },
    "verdict": {
        "type": "choice",
        "instructions": "What do the lines shown say about the claim?",
        "criteria": {
            "true": "they show the claim holds",
            "false": "they show the claim does not hold: a different value, name, count, or the opposite",
            "not_shown": "they do not settle it either way",
        },
    },
}
LINK_LEVELS = ["unrelated", "keyword", "nearby", "the claim"]
LINK = {
    "link": {
        "type": "score",
        "instructions": "Does this check test what the claim says? A check holds when every step holds; it is good "
        "when it would fail if the claim were false.",
        "criteria": [
            "unrelated: the steps test something the claim does not say",
            "a keyword only: the steps look for a word or name from the claim, not what the claim says about it",
            "a nearby fact: the steps test something related that the claim needs, not the claim itself",
            "the claim itself: the steps fail exactly when the claim is false",
        ],
    }
}
ATTEMPTS = 3


class DecisionError(RuntimeError):
    """The decision endpoint refused a question or answered in a shape that cannot be read."""


class Answer(BaseModel):
    """One question's answer as the endpoint sends it."""

    noul: float | None = None
    value: float | None = None
    probabilities: dict[str, float] | None = None

    @property
    def yes(self) -> float:
        """A noul's probability of yes."""
        return float(self.noul if self.noul is not None else self.value or 0.0)

    @property
    def most_likely(self) -> str:
        """A choice's most likely option."""
        options = self.probabilities or {}
        return max(options, key=lambda k: options[k]) if options else ""


class Reply(BaseModel):
    """The endpoint's reply: an answer per question, and the tokens it counted when it says."""

    answers: dict[str, Answer]
    usage: dict[str, int] = Field(default_factory=dict)


def asked_key(question: str, state: dict[str, Any]) -> str:
    """Return a hash of a question and what it was asked about, so the same question is not asked twice."""
    return hashlib.sha256(json.dumps([question, state], sort_keys=True).encode()).hexdigest()[:16]


def _retryable(error: BaseException) -> bool:
    """Whether a failed call is worth trying again: a timeout, a dropped connection, a 429 or a 5xx."""
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code == 429 or error.response.status_code >= 500
    return isinstance(error, httpx.TransportError)


class Decider:
    """Asks each enabled question of the provider and model set for it; use one per run, with its own HTTP client.

    Parameters
    ----------
    config :
        The ``[decisions]`` settings.
    client :
        The HTTP client, reused for every call.

    Raises
    ------
    ConfigError
        When a provider an enabled question uses has no key in the environment.
    """

    def __init__(self, config: DecisionsConfig, client: httpx.AsyncClient) -> None:
        self.config = config
        self.client = client
        self.keys = {
            name: config.providers[name].api_key(name) for name in {config.question(q).provider for q in config.enabled}
        }
        self.calls = 0
        self.tokens_in = 0

    def asks(self, question: str) -> bool:
        """Whether a question is switched on."""
        return question in self.config.enabled

    def model(self, question: str) -> str:
        """The model that answers a question."""
        return self.config.question(question).model

    @traceable(run_type="llm", name="decision model")
    async def ask(self, question: str, state: dict[str, Any], questions: dict[str, Any]) -> Reply:
        """Ask typed questions about ``state``; retry timeouts, 429s and 5xx.

        Raises
        ------
        DecisionError
            When the endpoint still fails, refuses the question (a 4xx: a wrong key or model), or answers without one
            of the questions asked.
        """
        try:
            reply = await self._post(question, state, questions)
        except httpx.HTTPStatusError as error:
            status = error.response.status_code
            provider = self.config.question(question).provider
            hint = f" (check decisions.providers.{provider}.api_key_env)" if status in {401, 403} else ""
            raise DecisionError(
                f"the decision endpoint answered {status}{hint}: {error.response.text[:200]}"
            ) from error
        except (httpx.TransportError, ValidationError) as error:
            raise DecisionError(f"the decision endpoint failed: {type(error).__name__}: {error}"[:300]) from error
        missing = set(questions) - set(reply.answers)
        if missing:
            raise DecisionError(f"the decision endpoint left out {sorted(missing)}")
        return reply

    async def _post(self, question: str, state: dict[str, Any], questions: dict[str, Any]) -> Reply:
        """Send one question set to its provider, retrying timeouts, dropped connections, 429s and 5xx."""
        settings = self.config.question(question)
        provider = self.config.providers[settings.provider]
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(ATTEMPTS),
            wait=wait_exponential_jitter(initial=1, max=20),
            retry=retry_if_exception(_retryable),
            reraise=True,
        ):
            with attempt:
                response = await self.client.post(
                    provider.base_url,
                    headers={"Authorization": f"Bearer {self.keys[settings.provider]}"},
                    json={"model": settings.model, "state": state, "questions": questions},
                    timeout=self.config.timeout,
                )
                response.raise_for_status()
        reply = Reply.model_validate_json(response.text)
        self.calls += 1
        self.tokens_in += reply.usage.get("input_tokens", 0)
        return reply

    async def failure(self, state: dict[str, Any]) -> tuple[float, str, dict[str, Any]]:
        """Ask why a check failed; return the chance the claim is false, the most likely cause, and the answers."""
        reply = await self.ask("failure", state, FAILURE)
        claim_false, cause = reply.answers["claim_false"], reply.answers["cause"]
        return claim_false.yes, cause.most_likely, reply.model_dump()["answers"]

    async def link(self, state: dict[str, Any]) -> tuple[float, str]:
        """Ask whether a check tests its claim; return a score from 0 (unrelated) to 1 (the claim) and its level."""
        reply = await self.ask("link", state, LINK)
        levels = reply.answers["link"].probabilities or {}
        if not levels:
            raise DecisionError("the decision endpoint gave the link question no level probabilities")
        expected = sum(int(level) * p for level, p in levels.items()) / (len(LINK_LEVELS) - 1)
        likeliest = int(max(levels, key=lambda k: levels[k]))
        return round(expected, 3), LINK_LEVELS[min(likeliest, len(LINK_LEVELS) - 1)]

    async def judge(self, state: dict[str, Any]) -> tuple[float, str, dict[str, Any]]:
        """Ask what a claim's lines show; return the chance they show it true, the verdict, and the answers."""
        reply = await self.ask("judge", state, JUDGE)
        shown_true, verdict = reply.answers["shown_true"], reply.answers["verdict"]
        return shown_true.yes, verdict.most_likely, reply.model_dump()["answers"]
