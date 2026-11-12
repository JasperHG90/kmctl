"""``kmctl audit judge``: the one optional model call, a decision model's judgement about a stored check or claim.

The endpoint takes ``{model, state, questions}`` and answers each question by
name: a noul as a probability of yes (``noul`` or ``value``), a choice as
``probabilities`` per option, a score as ``probabilities`` per level.
TypeSafe's systemone endpoint (Jev) and a gateway's decisions endpoint
(Clef) both answer this way. kmctl builds the state from the store, caches
each answer under its asked key, and writes nothing but the store.

tenacity (and langsmith, for tracing) come from the ``kmctl[audit]`` extra,
imported only when a question is asked.
"""

import asyncio
import hashlib
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError

from kmctl.audit_settings import Question, Settings, api_key
from kmctl.claims import AuditError
from kmctl.claims.check_store import STEPS_ADAPTER, check, claim
from kmctl.claims.store import Store
from kmctl.tracing import traced

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
QUESTION_SETS: dict[str, dict[str, Any]] = {
    "failure": FAILURE,
    "claim": JUDGE,
    "link": LINK,
}
ATTEMPTS = 3
INSTALL = "uv tool install --force 'kmctl[audit] @ git+https://github.com/JasperHG90/kmctl@vX.Y.Z'"


class DecisionError(RuntimeError):
    """The decision endpoint refused a question or answered in a shape that cannot be read."""


class Answer(BaseModel):
    """One question's answer as the endpoint sends it."""

    noul: float | None = None
    value: float | None = None
    probabilities: dict[str, float] | None = None

    @property
    def yes(self) -> float:
        """A noul's probability of yes.

        Raises
        ------
        DecisionError
            When the answer carries neither ``noul`` nor ``value``, rather than read as 0 and cached.
        """
        found = self.noul if self.noul is not None else self.value
        if found is None:
            raise DecisionError(
                "the decision endpoint answered a yes/no question with no probability"
            )
        return float(found)

    @property
    def most_likely(self) -> str:
        """A choice's most likely option."""
        options = self.probabilities or {}
        return max(options, key=lambda k: options[k]) if options else ""


class Reply(BaseModel):
    """The endpoint's reply: an answer per question, and the tokens it counted when it says."""

    answers: dict[str, Answer]
    usage: dict[str, int] = Field(default_factory=dict)


class Judgement(BaseModel):
    """One answered question about one check or claim, as ``kmctl audit judge`` prints it."""

    question: str = Field(description="failure, claim or link.")
    id: str = Field(description="The check id (failure, link) or claim id (claim).")
    model: str
    cached: bool = Field(
        description="True when read from the store, with no request sent."
    )
    chance: float | None = Field(
        default=None,
        description="failure: the chance the claim is false. claim: the chance the lines show it true.",
    )
    cause: str | None = Field(
        default=None, description="failure: claim_false, check_wrong or unclear."
    )
    verdict: str | None = Field(
        default=None, description="claim: true, false or not_shown."
    )
    score: float | None = Field(
        default=None, description="link: 0 (unrelated) to 1 (tests the claim itself)."
    )
    level: str | None = Field(
        default=None, description="link: unrelated, keyword, nearby or the claim."
    )


def asked_key(question: str, model: str, state: dict[str, Any]) -> str:
    """A hash of a question set's text, the model asked and what it was asked about, so the same thing is asked once.

    The question set's text is in the hash, so rewording it asks again.
    """
    content = [question, QUESTION_SETS[question], model, state]
    return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()[:16]


def _one_line(text: str) -> str:
    """``text`` with its whitespace runs, line breaks among them, collapsed to one space."""
    return " ".join(text.split())


MAX_RETRY_AFTER_SECONDS = 60.0


class _RetryAfter:
    """A tenacity wait that honours a 429's ``Retry-After`` seconds, up to a minute, else falls back to ``fallback``."""

    def __init__(self, fallback: Callable[[Any], float]) -> None:
        self.fallback = fallback

    def __call__(self, state: Any) -> float:
        """The seconds to wait before the next attempt."""
        error = state.outcome.exception() if state.outcome is not None else None
        if (
            isinstance(error, httpx.HTTPStatusError)
            and error.response.status_code == 429
        ):
            try:
                return min(
                    float(error.response.headers.get("Retry-After", "")),
                    MAX_RETRY_AFTER_SECONDS,
                )
            except ValueError:
                pass
        return float(self.fallback(state))


def _retryable(error: BaseException) -> bool:
    """Whether a failed call is worth trying again: a timeout, a dropped connection, a 429 or a 5xx."""
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code == 429 or error.response.status_code >= 500
    return isinstance(error, httpx.TransportError)


def state_for(
    store: Store, question: Question, subject: str, lines: str = ""
) -> dict[str, Any]:
    """The state a question is asked about, built from the store.

    Raises
    ------
    AuditError
        When the id names no stored check or claim, or the check is not in the state the question needs.
    """
    if question == "claim":
        found = claim(store, subject)
        if found is None:
            raise AuditError(
                f"no stored claim {subject!r}; list them with kmctl audit claims list --claims"
            )
        if not lines.strip():
            raise AuditError(
                "the claim question needs the lines to judge on stdin; pipe them in"
            )
        return {"claim": found.claim, "sentence": found.sentence, "lines": lines}
    stored = check(store, subject)
    if stored is None or stored.kind != "check":
        raise AuditError(
            f"no stored check {subject!r}; list them with kmctl audit checks list"
        )
    if stored.holds is None:
        raise AuditError(f"check {subject} has not run; run kmctl audit checks run")
    if question == "failure" and stored.holds:
        raise AuditError(
            f"check {subject} holds; the failure question is for a failed check"
        )
    found = claim(store, subject)
    return {
        "claim": found.claim if found else "",
        "sentence": found.sentence if found else "",
        "steps": STEPS_ADAPTER.dump_python(stored.steps, mode="json"),
        "holds": stored.holds,
        "saw": [r.detail for r in stored.results],
    }


def _judgement(
    question: str, subject: str, model: str, answers: dict[str, Answer], cached: bool
) -> Judgement:
    """Read one question set's answers into a judgement.

    Raises
    ------
    DecisionError
        When the link question came back with no level probabilities.
    """
    out = Judgement(question=question, id=subject, model=model, cached=cached)
    if question == "failure":
        out.chance, out.cause = (
            round(answers["claim_false"].yes, 3),
            answers["cause"].most_likely,
        )
    elif question == "claim":
        out.chance, out.verdict = (
            round(answers["shown_true"].yes, 3),
            answers["verdict"].most_likely,
        )
    else:
        levels = answers["link"].probabilities or {}
        try:
            weights = {int(k): p for k, p in levels.items()}
        except ValueError as error:
            raise DecisionError(
                "the decision endpoint gave the link question levels that are not numbers"
            ) from error
        if not weights:
            raise DecisionError(
                "the decision endpoint gave the link question no level probabilities"
            )
        out.score = round(
            sum(level * p for level, p in weights.items()) / (len(LINK_LEVELS) - 1), 3
        )
        out.level = LINK_LEVELS[
            min(max(weights, key=lambda k: weights[k]), len(LINK_LEVELS) - 1)
        ]
    return out


@dataclass
class Asker:
    """Asks one question set of its provider, retrying timeouts, dropped connections, 429s and 5xx.

    Attributes
    ----------
    calls : int
        Requests that returned an answer.
    """

    settings: Settings
    client: httpx.AsyncClient
    calls: int = 0

    async def ask(self, question: Question, state: dict[str, Any]) -> Reply:
        """Send one question set about ``state`` and read the reply.

        Raises
        ------
        DecisionError
            When the endpoint still fails, refuses (a 4xx), or leaves out a question.
        AuditError
            When the provider's key variable is not set.
        """
        from tenacity import (
            AsyncRetrying,
            retry_if_exception,
            stop_after_attempt,
            wait_exponential_jitter,
        )

        decisions = self.settings.decisions
        q = decisions.question(question)
        provider = decisions.providers[q.provider]
        key = api_key(self.settings, q.provider)
        questions = QUESTION_SETS[question]
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(ATTEMPTS),
                wait=_RetryAfter(wait_exponential_jitter(initial=1, max=20)),
                retry=retry_if_exception(_retryable),
                reraise=True,
            ):
                with attempt:
                    response = await self.client.post(
                        provider.base_url,
                        headers={"Authorization": f"Bearer {key}"},
                        json={"model": q.model, "state": state, "questions": questions},
                        timeout=decisions.timeout,
                    )
                    response.raise_for_status()
            reply = Reply.model_validate_json(response.text)
        except httpx.HTTPStatusError as error:
            status = error.response.status_code
            hint = (
                f" (check decisions.providers.{q.provider}.api_key_env)"
                if status in {401, 403}
                else ""
            )
            body = _one_line(error.response.text.replace(key, "***"))[:200]
            raise DecisionError(
                f"the decision endpoint answered {status}{hint}: {body}"
            ) from error
        except ValidationError as error:
            first = error.errors()[0]
            where = ".".join(str(p) for p in first["loc"]) or "reply"
            raise DecisionError(
                f"the decision endpoint's reply does not read: {where}: {_one_line(first['msg'])}"
            ) from error
        except httpx.TransportError as error:
            raise DecisionError(
                _one_line(
                    f"the decision endpoint failed: {type(error).__name__}: {error}".replace(
                        key, "***"
                    )
                )[:300]
            ) from error
        missing = set(questions) - set(reply.answers)
        if missing:
            raise DecisionError(f"the decision endpoint left out {sorted(missing)}")
        self.calls += 1
        return reply


def _cached(
    store: Store, key: str, question: str, subject: str, model: str
) -> Judgement | None:
    """The answer kept under ``key``, or None when that question was never asked of this state."""
    row = store.db.execute(
        "SELECT answers FROM decisions WHERE asked_key = ?", (key,)
    ).fetchone()
    if row is None:
        return None
    answers = {k: Answer.model_validate(v) for k, v in json.loads(row[0]).items()}
    return _judgement(question, subject, model, answers, cached=True)


def cached_judgement(
    store: Store, settings: Settings, question: Question, subject: str, lines: str = ""
) -> Judgement | None:
    """The kept answer to ``question`` about ``subject`` in its current state, asking nothing.

    Returns None when the question is off, the subject is not in a state the
    question takes, or the model was never asked about this state.
    """
    q = settings.decisions.question(question)
    if not q.enabled:
        return None
    try:
        state = state_for(store, question, subject, lines)
    except AuditError:
        return None
    return _cached(
        store, asked_key(question, q.model, state), question, subject, q.model
    )


async def judge(
    store: Store,
    settings: Settings,
    question: Question,
    subjects: list[str],
    lines: str = "",
    client: httpx.AsyncClient | None = None,
) -> list[Judgement | Exception]:
    """Ask ``question`` about each id, at most ``max_calls`` at once, reading cached answers from the store.

    Returns one judgement per id, in order, or the error that stopped it.

    Raises
    ------
    AuditError
        When the question is off, naming its settings table.
    """
    q = settings.decisions.question(question)
    if not q.enabled:
        raise AuditError(
            f"the {question} question is off; switch it on under [decisions.{question}] (enabled, provider, model) "
            f"in {settings.source or 'the audit.toml settings file'}"
        )
    limit = asyncio.Semaphore(settings.decisions.max_calls)
    own = client is None
    http = client or httpx.AsyncClient(timeout=settings.decisions.timeout)
    asker = Asker(settings, http)
    ask: Callable[[Question, dict[str, Any]], Awaitable[Reply]] = traced(
        asker.ask, "decision model"
    )

    async def one(subject: str) -> Judgement:
        """Answer one id from the cache, or ask and cache it."""
        state = state_for(store, question, subject, lines)
        key = asked_key(question, q.model, state)
        found = _cached(store, key, question, subject, q.model)
        if found is not None:
            return found
        async with limit:
            reply = await ask(question, state)
        judgement = _judgement(question, subject, q.model, reply.answers, cached=False)
        store.db.execute(
            "INSERT OR REPLACE INTO decisions (asked_key, question, subject, model, answers, asked_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                key,
                question,
                subject,
                q.model,
                json.dumps({k: v.model_dump() for k, v in reply.answers.items()}),
                datetime.now(UTC).isoformat(timespec="seconds"),
            ),
        )
        return judgement

    try:
        results = await asyncio.gather(
            *(one(s) for s in subjects), return_exceptions=True
        )
    finally:
        if own:
            await http.aclose()
    out: list[Judgement | Exception] = []
    for r in results:
        if isinstance(r, BaseException) and not isinstance(r, Exception):
            raise r
        out.append(r)
    return out
