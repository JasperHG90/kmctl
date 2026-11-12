"""The audit page: what ``kmctl audit ui`` serves on localhost, and the feedback and second opinions it writes.

The page shows each document of the bundle with its claims, checks and how
sure each check is. People give a thumbs up or down and a note on a claim or
its check, say whether a claim holds, and ask the decision model for a second
opinion. Everything is read from and written to ``.kmctl/audit.sqlite``
(ADR 0041). The server listens on 127.0.0.1 only and refuses requests whose
Host or Origin is not local, so no other site can write through it.
"""

import asyncio
import importlib.resources
import importlib.util
import json
import sqlite3
import webbrowser
from collections import Counter
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from kmctl.audit_settings import Question, Settings, load, settings_path
from kmctl.claims import AuditError
from kmctl.claims.check_store import check
from kmctl.claims.check_verbs import CHECKABLE, lines_for, status_row
from kmctl.claims.feedback import (
    Feedback,
    FeedbackIn,
    HumanVerdict,
    Target,
    Vote,
    latest,
    record,
)
from kmctl.claims.models import Claim
from kmctl.claims.sections import cut, resolve_target
from kmctl.claims.steps import Repository
from kmctl.claims.store import Store
from kmctl.claims.verbs import todo
from kmctl.judge import Judgement

PAGE = "ui.html"
DEFAULT_PORT = 8765
LOCAL_HOSTS = ("127.0.0.1", "localhost")
#: The largest request body the server reads; a note is at most 4000 characters.
MAX_BODY = 64_000
#: Claim statuses per coverage, worst first; a sentence takes its worst claim's.
COVERAGE: list[tuple["Coverage", set[str]]] = [
    ("drift", {"drift", "fails"}),
    ("unchecked", {"no check", "stale reason", "not run", "skipped", "weak"}),
    ("reason", {"reason"}),
    ("checked", {"holds", "not measured"}),
]
Coverage = Literal["drift", "unchecked", "reason", "checked", "none"]


class QualityView(BaseModel):
    """A check's mutation score: edits tried, edits it caught, and the ones it missed."""

    mutants: int
    killed: int
    survived: list[str]


class CheckView(BaseModel):
    """A claim's stored check or reason as the page shows it."""

    kind: str = Field(description="check or reason.")
    strength: str
    why: str
    drift: str | None
    reason: str
    by: str = Field(description="Who submitted it.")
    steps: list[dict[str, object]]
    results: list[str] = Field(description="What each step saw on its last run.")
    quality: QualityView | None


class FeedbackView(BaseModel):
    """A person's latest judgment of a claim or its check."""

    vote: Vote | None
    verdict: HumanVerdict | None
    note: str
    by: str
    at: str
    answered: bool = Field(
        description="Whether an agent's answer has taken it in since it was given."
    )


class ClaimView(BaseModel):
    """One claim with its check, people's feedback, and the decision model's last answer."""

    id: str
    section: str
    n: int
    text: str
    kind: str
    quantifier: str
    status: str = Field(
        description="The check status kmctl audit checks list gives, or not checkable."
    )
    check: CheckView | None
    coverage: Coverage = Field(
        description="How the page marks it; a person's current verdict wins over the check."
    )
    human: HumanVerdict | None = Field(
        description="A person's verdict, while the files the judged answer read are unchanged."
    )
    human_stale: bool = Field(
        description="True when a person gave a verdict but the files it was given on have changed."
    )
    disagrees: bool = Field(
        description="Whether the check says the opposite of the person's verdict."
    )
    feedback: dict[Target, FeedbackView]
    ask: Question | None = Field(
        description="The question a second opinion asks: link, failure or claim; None when none fits yet."
    )
    opinion: Judgement | None = Field(
        description="The decision model's kept answer to that question, for the claim as it is now."
    )


class SentenceView(BaseModel):
    """One sentence of a section, with its verdict and claims."""

    n: int
    text: str
    kind: str | None
    reason: str
    claims: list[ClaimView]
    coverage: str = Field(
        description="pending, none, not checkable, or its worst claim's coverage."
    )


class SectionView(BaseModel):
    """One section of a document."""

    id: str
    name: str
    pending: bool = Field(
        description="True when its text changed since its claims were extracted."
    )
    sentences: list[SentenceView]


class DocumentView(BaseModel):
    """One concept of the bundle as the page lists and shows it."""

    concept: str
    title: str
    sections: list[SectionView]
    counts: dict[str, int] = Field(description="Sentences per coverage.")
    outdated: bool
    state: str = Field(description="outdated, drift, unchecked or ok.")


class AuditView(BaseModel):
    """Everything the page shows, read from the store when it loads."""

    generated: str
    by: str = Field(description="The name feedback from this page is stored under.")
    questions: list[Question] = Field(
        description="The decision model questions switched on in the settings."
    )
    concepts: list[DocumentView]


class OpinionRequest(BaseModel):
    """What the page sends to ask for a second opinion on one claim."""

    model_config = ConfigDict(extra="forbid")

    claim: str = Field(min_length=1)


def coverage_of(status: str, human: HumanVerdict | None) -> Coverage:
    """How the page marks a claim: a person's verdict wins, then the check's status."""
    if status == "not checkable":
        return "none"
    if human == "false":
        return "drift"
    if human == "holds":
        return "checked"
    for name, members in COVERAGE:
        if status in members:
            return name
    return "checked"


def question_for(claim: Claim, store: Store) -> Question | None:
    """The question a second opinion asks about a claim.

    link asks whether a check that holds tests the claim, failure whether a
    failed check shows the claim is false, and claim whether the lines kmctl
    finds show a claim with only a reason, or no answer yet, true.
    """
    if claim.kind not in CHECKABLE:
        return None
    stored = check(store, claim.id)
    if stored is None or stored.kind == "reason":
        return "claim"
    if stored.holds is None:
        return None
    return "link" if stored.holds else "failure"


def _check_view(store: Store, claim_id: str) -> CheckView | None:
    """A claim's stored check or reason for the page, or None."""
    found = check(store, claim_id)
    if found is None:
        return None
    q = found.quality
    return CheckView(
        kind=found.kind,
        strength=found.strength,
        why=found.why,
        drift=found.drift,
        reason=found.reason,
        by=found.submitted_by,
        steps=[s.model_dump(mode="json") for s in found.steps],
        results=[r.detail for r in found.results],
        quality=None
        if q is None
        else QualityView(mutants=q.mutants, killed=q.killed, survived=q.survived),
    )


def _feedback_view(f: Feedback) -> FeedbackView:
    """A stored judgment for the page."""
    return FeedbackView(
        vote=f.vote,
        verdict=f.verdict,
        note=f.note,
        by=f.by,
        at=f.at,
        answered=f.answered_at is not None,
    )


def _claim_view(
    store: Store,
    repo: Repository,
    claim: Claim,
    said: dict[tuple[str, Target], Feedback],
    opinion: Judgement | None,
) -> ClaimView:
    """One claim for the page, from the store and the feedback already read."""
    row = status_row(store, repo, claim) if claim.kind in CHECKABLE else None
    status = row.status if row is not None else "not checkable"
    human = row.human if row is not None else None
    given = said.get((claim.id, "check"))
    ask = question_for(claim, store)
    return ClaimView(
        id=claim.id,
        section=claim.section,
        n=claim.n,
        text=claim.claim,
        kind=claim.kind,
        quantifier=claim.quantifier,
        status=status,
        check=_check_view(store, claim.id) if row is not None else None,
        coverage=coverage_of(status, human),
        human=human,
        human_stale=given is not None and given.verdict is not None and human is None,
        disagrees=row.disagrees if row is not None else False,
        feedback={
            t: _feedback_view(f)
            for t in ("claim", "check")
            if (f := said.get((claim.id, t))) is not None
        },
        ask=ask,
        opinion=opinion if opinion is not None and opinion.question == ask else None,
    )


def _settings(config: Path | None) -> Settings | None:
    """The decision model settings, or None when they do not read (the page then offers no second opinion)."""
    try:
        return load(config)
    except AuditError:
        return None


def _enabled(settings: Settings | None) -> list[Question]:
    """The questions switched on."""
    if settings is None:
        return []
    return [
        q
        for q in ("link", "failure", "claim")
        if settings.decisions.question(q).enabled
    ]


def _opinions(
    store: Store,
    repo: Repository,
    root: Path,
    claims: list[Claim],
    settings: Settings | None,
) -> dict[str, Judgement]:
    """The decision model's kept answers about these claims as they are now, asking nothing.

    Only claims the model was asked about before are looked up, so the
    lines a claim question needs are found for those alone.
    """
    from kmctl.judge import cached_judgement

    if not _enabled(settings) or settings is None:
        return {}
    asked = {
        row[0] for row in store.db.execute("SELECT DISTINCT subject FROM decisions")
    }
    candidates = [c for c in claims if c.id in asked]
    questions = {c.id: question_for(c, store) for c in candidates}
    lines = lines_for(
        store,
        repo,
        resolve_target(root),
        [c for c in candidates if questions[c.id] == "claim"],
    )
    found: dict[str, Judgement] = {}
    for c in candidates:
        q = questions[c.id]
        if q is None:
            continue
        shown = lines.get(c.id)
        j = cached_judgement(store, settings, q, c.id, shown.text if shown else "")
        if j is not None:
            found[c.id] = j
    return found


def build(root: Path, by: str = "human", config: Path | None = None) -> AuditView:
    """Read everything the page shows from the bundle and the store at ``root``.

    It refreshes the stored sections first, as ``kmctl audit claims todo``
    does, so a section whose text changed shows as needing extraction.

    Raises
    ------
    AuditError
        If ``root`` names no bundle.
    """
    todo(root)
    target = resolve_target(root)
    repo = Repository(target.root)
    settings = _settings(config)
    concepts: dict[str, DocumentView] = {}
    with Store(target.root) as store:
        pending = store.pending_sections()
        verdicts = {
            (sid, n): (kind, reason)
            for sid, n, kind, reason in store.db.execute(
                "SELECT section_id, n, kind, reason FROM verdicts"
            )
        }
        stored = store.claims()
        said = latest(store)
        opinions = _opinions(store, repo, target.root, stored, settings)
        by_sentence: dict[tuple[str, int], list[ClaimView]] = {}
        for c in stored:
            by_sentence.setdefault((c.section, c.n), []).append(
                _claim_view(store, repo, c, said, opinions.get(c.id))
            )
        order = {sec.id: i for i, sec in enumerate(cut(target))}
        rows = sorted(
            store.db.execute(
                "SELECT id, concept, title, section, sentences FROM sections"
            ),
            key=lambda row: order.get(row[0], len(order)),
        )
    for sid, concept, title, section, sentences in rows:
        doc = concepts.setdefault(
            concept,
            DocumentView(
                concept=concept,
                title=title,
                sections=[],
                counts={},
                outdated=False,
                state="ok",
            ),
        )
        out = []
        for n, text in enumerate(json.loads(sentences), start=1):
            kind, reason = verdicts.get((sid, n), (None, ""))
            found = by_sentence.get((sid, n), [])
            out.append(
                SentenceView(
                    n=n,
                    text=text,
                    kind=kind,
                    reason=reason,
                    claims=found,
                    coverage=sentence_coverage(sid in pending, found),
                )
            )
        doc.sections.append(
            SectionView(id=sid, name=section, pending=sid in pending, sentences=out)
        )
    for doc in concepts.values():
        count = Counter(s.coverage for sec in doc.sections for s in sec.sentences)
        doc.counts = dict(count)
        doc.outdated = any(sec.pending for sec in doc.sections)
        doc.state = (
            "outdated"
            if doc.outdated
            else "drift"
            if count["drift"]
            else "unchecked"
            if count["unchecked"]
            else "ok"
        )
    return AuditView(
        generated=datetime.now(UTC).isoformat(timespec="seconds"),
        by=by,
        questions=_enabled(settings),
        concepts=sorted(concepts.values(), key=lambda d: d.concept),
    )


def sentence_coverage(pending: bool, claims: list[ClaimView]) -> str:
    """A sentence's mark: pending, none, not checkable, or its worst claim's coverage."""
    if pending:
        return "pending"
    if not claims:
        return "none"
    marks = {c.coverage for c in claims} - {"none"}
    if not marks:
        return "not checkable"
    return next(name for name, _ in COVERAGE if name in marks)


def claim_view(root: Path, claim_id: str, config: Path | None = None) -> ClaimView:
    """One claim as the page shows it, read again after feedback or a second opinion.

    Raises
    ------
    AuditError
        If ``root`` names no bundle, or the store has no such claim.
    """
    target = resolve_target(root)
    repo = Repository(target.root)
    settings = _settings(config)
    with Store(target.root) as store:
        found = store.claim(claim_id)
        if found is None:
            raise AuditError(
                f"no stored claim {claim_id!r}; it was re-extracted or removed, so reload the page"
            )
        opinion = _opinions(store, repo, target.root, [found], settings).get(found.id)
        return _claim_view(store, repo, found, latest(store, [found.id]), opinion)


def give_feedback(
    root: Path, given: FeedbackIn, by: str, config: Path | None = None
) -> ClaimView:
    """Store a person's judgment of a claim or its check, and return the claim as it now shows.

    A verdict on a claim whose answer read no files (no check yet, or a
    reason found by keyword) is kept with the files behind the lines
    ``kmctl audit checks todo`` shows for it, so it goes stale when they
    change.

    Raises
    ------
    AuditError
        If ``root`` names no bundle, or the store has no such claim.
    """
    target = resolve_target(root)
    repo = Repository(target.root)
    with Store(target.root) as store:
        found = store.claim(given.claim)
        lines_read: dict[str, str] = {}
        if found is not None and given.target == "check" and given.verdict:
            shown = lines_for(store, repo, target, [found])[found.id]
            lines_read = {p: repo.sha(p) for p in shown.files}
        record(store, given, by, lines_read)
    return claim_view(root, given.claim, config)


def second_opinion(root: Path, claim_id: str, config: Path | None = None) -> ClaimView:
    """Ask the decision model about one claim, and return the claim with its answer.

    The question depends on the claim's answer: link for a check that holds,
    failure for one that fails, and claim, on the lines ``kmctl audit checks
    todo`` would show, for a reason or no answer yet. A question asked of the
    same state before is answered from the store with no request.

    Raises
    ------
    AuditError
        When the claim is unknown or has nothing to ask about, the
        ``kmctl[audit]`` extra is missing, the settings do not read, the
        question is off, or the model's endpoint fails.
    """
    from kmctl.claims.check_verbs import claim_lines
    from kmctl.judge import INSTALL, judge

    target = resolve_target(root)
    with Store(target.root) as store:
        found = store.claim(claim_id)
        if found is None:
            raise AuditError(
                f"no stored claim {claim_id!r}; it was re-extracted or removed, so reload the page"
            )
        question = question_for(found, store)
    if question is None:
        raise AuditError(
            "this claim is not checkable"
            if found.kind not in CHECKABLE
            else "its check has not run yet; run kmctl audit checks run, then reload the page"
        )
    if importlib.util.find_spec("tenacity") is None:
        raise AuditError(f"a second opinion needs the kmctl[audit] extra; {INSTALL}")
    settings = load(config)
    if not settings.decisions.question(question).enabled:
        raise AuditError(
            f"the {question} question is off; switch it on under [decisions.{question}] "
            f"(enabled, provider, model) in {settings.source or settings_path(config)}"
        )
    lines = claim_lines(root, claim_id) if question == "claim" else ""
    with Store(target.root) as store:
        result = asyncio.run(judge(store, settings, question, [claim_id], lines))[0]
    if isinstance(result, Exception):
        raise AuditError(str(result)) from result
    return claim_view(root, claim_id, config)


class AuditServer(ThreadingHTTPServer):
    """The local server behind the audit page, bound to 127.0.0.1.

    Parameters
    ----------
    root :
        The repository, bundle or a path inside it.
    port :
        The port to listen on; 0 picks a free one.
    by :
        The name feedback from the page is stored under.
    config :
        The decision model settings file, or None for the per-user one.
    """

    daemon_threads = True

    def __init__(
        self, root: Path, port: int, by: str, config: Path | None = None
    ) -> None:
        super().__init__(("127.0.0.1", port), _Handler)
        self.root = root
        self.by = by
        self.config = config

    @property
    def url(self) -> str:
        """The page's address."""
        return f"http://127.0.0.1:{self.server_address[1]}/"


class _Handler(BaseHTTPRequestHandler):
    """Serves the page and its three calls: the data, feedback and a second opinion."""

    server: AuditServer

    def log_message(self, format: str, *args: object) -> None:
        """Keep the terminal quiet; refusals reach the page instead."""

    def _send(
        self, status: HTTPStatus, body: bytes, kind: str = "application/json"
    ) -> None:
        """Write one response with its length and type."""
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: HTTPStatus, message: str) -> None:
        """Send ``{"error": message}``."""
        self._send(status, json.dumps({"error": message}).encode())

    def _local(self) -> bool:
        """Whether the Host header names this machine, so a rebound domain cannot reach the server."""
        host = urlsplit("//" + self.headers.get("Host", "")).hostname
        return host in LOCAL_HOSTS

    def _same_origin(self) -> bool:
        """Whether a write comes from this page: an Origin, when sent, must match the Host."""
        origin = self.headers.get("Origin")
        return origin is None or origin == f"http://{self.headers.get('Host', '')}"

    def do_GET(self) -> None:
        """Serve the page or its data."""
        if not self._local():
            self._error(HTTPStatus.FORBIDDEN, "open the page at 127.0.0.1 or localhost")
            return
        path = urlsplit(self.path).path
        if path == "/":
            page = importlib.resources.files("kmctl.claims").joinpath(PAGE)
            self._send(HTTPStatus.OK, page.read_bytes(), "text/html; charset=utf-8")
        elif path == "/api/data":
            try:
                view = build(self.server.root, self.server.by, self.server.config)
            except AuditError as error:
                self._error(HTTPStatus.BAD_REQUEST, str(error))
                return
            self._send(HTTPStatus.OK, view.model_dump_json().encode())
        else:
            self._error(HTTPStatus.NOT_FOUND, f"no page at {path}")

    def do_POST(self) -> None:
        """Store feedback, or ask for a second opinion, and answer with the claim as it now shows."""
        if not self._local() or not self._same_origin():
            self._error(
                HTTPStatus.FORBIDDEN, "writes come only from the audit page itself"
            )
            return
        if not self.headers.get("Content-Type", "").startswith("application/json"):
            self._error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "send JSON")
            return
        given = self.headers.get("Content-Length", "")
        if not given.isdigit():
            self._error(HTTPStatus.LENGTH_REQUIRED, "send a Content-Length")
            return
        if int(given) > MAX_BODY:
            self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "the request is too large")
            return
        body = self.rfile.read(int(given))
        path = urlsplit(self.path).path
        try:
            if path == "/api/feedback":
                view = give_feedback(
                    self.server.root,
                    FeedbackIn.model_validate_json(body),
                    self.server.by,
                    self.server.config,
                )
            elif path == "/api/opinion":
                asked = OpinionRequest.model_validate_json(body)
                view = second_opinion(self.server.root, asked.claim, self.server.config)
            else:
                self._error(HTTPStatus.NOT_FOUND, f"no call at {path}")
                return
        except ValidationError as error:
            first = error.errors()[0]
            where = ".".join(str(p) for p in first["loc"]) or "body"
            self._error(HTTPStatus.BAD_REQUEST, f"{where}: {first['msg']}")
            return
        except AuditError as error:
            self._error(HTTPStatus.BAD_REQUEST, str(error))
            return
        except sqlite3.Error as error:
            self._error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"the audit store failed: {error}; close other writers and try again",
            )
            return
        self._send(HTTPStatus.OK, view.model_dump_json().encode())


def serve(
    root: Path,
    port: int = DEFAULT_PORT,
    by: str = "human",
    config: Path | None = None,
    open_browser: bool = True,
) -> AuditServer:
    """Bind the audit page's server and optionally open the page in a browser.

    The caller runs ``serve_forever`` and closes the server.

    Raises
    ------
    AuditError
        If ``root`` names no bundle, or the port is taken.
    """
    resolve_target(root)
    try:
        server = AuditServer(root, port, by, config)
    except OSError as error:
        raise AuditError(
            f"port {port} is taken ({error.strerror}); pass --port with another, or --port 0 for any free one"
        ) from error
    if open_browser:
        webbrowser.open(server.url)
    return server
