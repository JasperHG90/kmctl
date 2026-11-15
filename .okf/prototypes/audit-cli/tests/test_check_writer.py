"""Tests for the check-writing agent, with a scripted stand-in for the model and a real git repository."""

import asyncio
import pathlib as plb
import subprocess
from typing import Any, cast

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

from audit_cli.checks.steps import Repository
from audit_cli.checks.writer import Budget, ClaimInput, Submit, write_checks

FILE_STEP = {"op": "file", "path": "action/agent.py"}
GONE_STEP = {"op": "file", "path": "action/gone.sh", "exists": True}


class ScriptedModel:
    """Answers each call with the next scripted reply (the last one repeats) and keeps what it was sent."""

    def __init__(self, replies: list[AIMessage], growing: bool = False) -> None:
        self.replies = replies
        self.growing = growing  # each call costs 100 more input tokens than the last, as a growing history does
        self.sent: list[list[BaseMessage]] = []
        self.final: dict[str, Any] | None = None  # what the last, submit-only call answers
        self.final_calls: list[list[dict[str, Any]]] = []  # raw tool calls the last call makes, one list a try

    def bind_tools(self, tools: list[Any]) -> "ScriptedModel":
        """Return itself, noting the tools' names: the script already knows what it calls."""
        self.tools = [t.__name__ for t in tools]
        return self

    def with_structured_output(self, schema: Any, **kwargs: Any) -> "FinalCall":
        """Return the stand-in for the last call, which answers with a set Submit or nothing."""
        return FinalCall(self)

    async def ainvoke(self, messages: list[BaseMessage]) -> AIMessage:
        """Return the next reply, with 100 tokens in (100 more each call when growing) and 10 out."""
        self.sent.append(list(messages))
        reply = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        tokens_in = 100 * len(self.sent) if self.growing else 100
        usage = {
            "input_tokens": tokens_in,
            "output_tokens": 10,
            "total_tokens": tokens_in + 10,
            "input_token_details": {"cache_read": 60},
        }
        return reply.model_copy(update={"usage_metadata": usage})


class FinalCall:
    """The last call: answers with the model's set final submission, parsed, or with nothing readable."""

    def __init__(self, model: ScriptedModel) -> None:
        self.model = model

    async def ainvoke(self, messages: list[BaseMessage]) -> dict[str, Any]:
        """Return the set final submission, with 100 tokens in, 90 of them cached, and 10 out.

        With ``final_calls`` set, each try instead answers with those raw tool calls and nothing parsed, as a reply
        that also calls another tool comes back.
        """
        self.model.sent.append(list(messages))
        if self.model.final_calls:
            calls = self.model.final_calls.pop(0)
            usage_raw: dict[str, Any] = {"input_tokens": 100, "output_tokens": 10, "total_tokens": 110}
            raw_reply = AIMessage(content="", tool_calls=cast(Any, calls), usage_metadata=cast(Any, usage_raw))
            return {"parsed": None, "raw": raw_reply, "parsing_error": "Unknown tool type: 'TryCheck'"}
        final = self.model.final
        usage: dict[str, Any] = {
            "input_tokens": 100,
            "output_tokens": 10,
            "total_tokens": 110,
            "input_token_details": {"cache_read": 90},
        }
        raw = AIMessage(content="", usage_metadata=cast(Any, usage))
        return {"parsed": Submit.model_validate(final) if final else None, "raw": raw, "parsing_error": "none set"}


def call(name: str, n: int, **args: Any) -> AIMessage:
    """Return a reply that makes one tool call."""
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": f"t{n}"}])


@pytest.fixture
def small(tmp_path: plb.Path) -> Repository:
    """A repository with one script."""
    root = tmp_path / "small"
    (root / "action").mkdir(parents=True)
    body = "".join(f"# line {n} of a script long enough that trimming its reads saves text\n" for n in range(40))
    (root / "action" / "agent.py").write_text("def run_shell(cmd):\n    return cmd\n" + body)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    return Repository(root)


CLAIMS = [ClaimInput("c1", "id1", "`action/agent.py` exists."), ClaimInput("c2", "id2", "The agent means well.")]
SUBMIT = {
    "checks": [{"claim": "c1", "steps": [FILE_STEP], "strength": "exact", "why": "the file is the claim"}],
    "no_checks": [{"claim": "c2", "reason": "intent"}],
}


def run(
    model: ScriptedModel,
    small: Repository,
    budget: Budget | None = None,
    claims: list[ClaimInput] = CLAIMS,
    **options: bool,
) -> Any:
    """Run the writer with the stand-in model."""
    return asyncio.run(write_checks(cast(BaseChatModel, cast(Any, model)), small, claims, budget, **options))


def test_a_submission_is_run_and_recorded(small: Repository) -> None:
    """Each check runs once on submit; each reason is kept; tokens are counted."""
    result = run(ScriptedModel([call("Search", 1, pattern="def run_shell"), call("Submit", 2, **SUBMIT)]), small)
    assert [(c.claim_id, c.holds) for c in result.checks] == [("id1", True)]
    assert result.no_checks == {"id2": "intent"}
    assert (result.turns, result.tokens_in, result.unfinished) == (2, 200, [])


def test_a_failing_check_is_sent_back_once_then_kept(small: Repository) -> None:
    """A check that does not hold goes back once with what it saw; resubmitted as drift, it is kept as written."""
    wrong = SUBMIT | {"checks": [{"claim": "c1", "steps": [GONE_STEP], "strength": "exact", "why": "x"}]}
    drift = SUBMIT | {"checks": [{"claim": "c1", "steps": [GONE_STEP], "strength": "exact", "why": "drift: gone"}]}
    model = ScriptedModel([call("Submit", 1, **wrong), call("Submit", 2, **drift)])
    result = run(model, small)
    assert "c1: 0 matching" in str(model.sent[1][-1].content)
    assert [(c.holds, c.check.why) for c in result.checks] == [(False, "drift: gone")]


def test_a_failing_check_is_kept_after_its_second_look(small: Repository) -> None:
    """Sent back once, a failing check resubmitted unchanged is accepted, not sent back forever."""
    wrong = SUBMIT | {"checks": [{"claim": "c1", "steps": [GONE_STEP], "strength": "exact", "why": "x"}]}
    result = run(ScriptedModel([call("Submit", 1, **wrong), call("Submit", 2, **wrong)]), small)
    assert result.turns == 2 and [c.holds for c in result.checks] == [False]


def test_a_check_with_no_steps_is_refused(small: Repository) -> None:
    """A check with no steps must be a reason instead, so it never reads as a failing check."""
    empty = SUBMIT | {"checks": [{"claim": "c1", "steps": [], "strength": "proxy", "why": "x"}]}
    model = ScriptedModel([call("Submit", 1, **empty), call("Submit", 2, **SUBMIT)])
    run(model, small)
    assert "Submit was not valid" in str(model.sent[1][-1].content)


def test_claims_are_submitted_as_they_are_ready(small: Repository) -> None:
    """One call may hand in part of the batch; the agent is told what is still open, and the batch ends when all are."""
    first = {"checks": SUBMIT["checks"]}
    second = {"no_checks": SUBMIT["no_checks"]}
    model = ScriptedModel([call("Submit", 1, **first), call("Search", 2, pattern="x"), call("Submit", 3, **second)])
    result = run(model, small)
    assert "Recorded: c1." in str(model.sent[1][-1].content) and "Still open: c2." in str(model.sent[1][-1].content)
    assert result.no_checks == {"id2": "intent"} and result.turns == 3 and result.unfinished == []


def test_old_tool_output_is_trimmed_by_size_and_repeats(small: Repository) -> None:
    """Newest results are kept up to the size limit; an older copy of a repeated call is always trimmed."""
    reads = [call("ReadFile", n, path="action/agent.py", start=n) for n in range(1, 4)]
    model = ScriptedModel([*reads, call("ReadFile", 4, path="action/agent.py", start=1), call("Submit", 9, **SUBMIT)])
    run(model, small)
    tools = [m for m in model.sent[-1] if isinstance(m, ToolMessage)]
    assert [str(m.content).startswith("[trimmed: ReadFile") for m in tools] == [True, False, False, False]


def test_output_past_the_size_limit_is_trimmed(small: Repository, monkeypatch: pytest.MonkeyPatch) -> None:
    """Once the newest results fill the limit, every older one is sent as a note."""
    monkeypatch.setattr("audit_cli.checks.writer.KEEP_CHARS", 10)
    reads = [call("ReadFile", n, path="action/agent.py", start=n) for n in range(1, 4)]
    model = ScriptedModel([*reads, call("Submit", 9, **SUBMIT)])
    result = run(model, small)
    tools = [m for m in model.sent[-1] if isinstance(m, ToolMessage)]
    assert [str(m.content).startswith("[trimmed") for m in tools] == [True, True, False]
    assert 0 < result.chars_sent < result.chars_untrimmed


def test_a_batch_stops_at_its_budget_and_reports_the_rest_unfinished(small: Repository) -> None:
    """A model that never submits is warned, then stopped; its claims are unfinished, not lost silently."""
    model = ScriptedModel([call("ListFiles", 1, glob="**")])
    result = run(model, small, Budget(max_turns=4))
    assert result.turns == 5 and result.stopped and result.unfinished == ["id1", "id2"]  # the last call, tried twice
    assert any("Budget nearly spent" in str(m.content) for m in model.sent[-1])


def test_a_partial_submission_is_accepted_near_the_end(small: Repository) -> None:
    """Once warned, a submission that leaves claims out is taken, and those claims are unfinished."""
    model = ScriptedModel([call("ListFiles", 1, glob="**"), call("Submit", 2, checks=SUBMIT["checks"])])
    result = run(model, small, Budget(max_turns=3))
    assert [c.claim_id for c in result.checks] == ["id1"] and result.unfinished == ["id2"]


def test_the_last_call_can_only_submit(small: Repository) -> None:
    """A model that ignores the tool list still hands in at the last call, through structured output."""
    model = ScriptedModel([call("ListFiles", 1, glob="**")])
    model.final = SUBMIT
    result = run(model, small, Budget(max_turns=3))
    assert [c.claim_id for c in result.checks] == ["id1"] and result.no_checks == {"id2": "intent"}
    assert result.unfinished == [] and result.stopped is None


def test_open_claims_are_named_every_few_turns(small: Repository) -> None:
    """Every fifth turn the agent is told which claims are open and asked to submit what it has."""
    model = ScriptedModel([call("ListFiles", n, glob=f"g{n}") for n in range(6)] + [call("Submit", 9, **SUBMIT)])
    run(model, small)
    assert any("Still open: c1, c2. Submit now" in str(m.content) for m in model.sent[5])


def test_with_trimming_off_every_call_sends_the_history_as_it_grew(small: Repository) -> None:
    """Off, nothing is rewritten: each call's input starts with the last call's, so a prompt cache can serve it."""
    reads = [call("ReadFile", n, path="action/agent.py", start=n) for n in range(1, 4)]
    model = ScriptedModel([*reads, call("ReadFile", 4, path="action/agent.py", start=1), call("Submit", 9, **SUBMIT)])
    result = run(model, small, Budget(trim=False))
    for before, after in zip(model.sent, model.sent[1:], strict=False):
        assert [m.content for m in after[: len(before)]] == [m.content for m in before]
    assert result.chars_sent == result.chars_untrimmed


def test_lines_found_are_shown_once_in_the_first_message(small: Repository) -> None:
    """Lines found for the claims go in the first message, a block two claims share only once."""
    block = "--- action/agent.py:1-2\n1: def run_shell(cmd):"
    claims = [ClaimInput("c1", "id1", "a", lines=block), ClaimInput("c2", "id2", "b", lines=block)]
    model = ScriptedModel([call("Submit", 1, **SUBMIT)])
    run(model, small, claims=claims)
    first = str(model.sent[0][1].content)
    assert first.count(block) == 1
    assert first.index("c2: b") < first.index(block)


def test_cached_input_tokens_are_counted(small: Repository) -> None:
    """The cached input the provider reports is added up beside input and output."""
    model = ScriptedModel([call("ReadFile", 1, path="action/agent.py"), call("Submit", 2, **SUBMIT)])
    result = run(model, small)
    assert (result.tokens_in, result.tokens_cached) == (200, 120)


def test_running_out_of_tokens_still_makes_the_last_submit_call(small: Repository) -> None:
    """When another call would pass the token budget, the next call is the submit-only one, so work is not lost."""
    model = ScriptedModel([call("ListFiles", 1, glob="**")])
    model.final = SUBMIT
    result = run(model, small, Budget(max_tokens=300))
    assert result.unfinished == [] and result.stopped is None
    assert result.turns == 3


def test_a_growing_history_still_gets_the_last_submit_call(small: Repository) -> None:
    """Calls grow as the history does, so the next one is judged by the last one's size and growth, not the mean."""
    model = ScriptedModel([call("ListFiles", 1, glob="**")], growing=True)
    model.final = SUBMIT
    result = run(model, small, Budget(max_tokens=1000))
    assert result.unfinished == [] and result.stopped is None
    assert str(model.sent[-1][-1].content).startswith("Last call")
    assert result.turns == 4  # 110, 210, 310, then the last call: 630 + 310 + 100 reaches 1000


def test_the_last_call_counts_its_cached_tokens(small: Repository) -> None:
    """The submit-only call's tokens, cached ones too, are added like any other call's."""
    model = ScriptedModel([call("ListFiles", 1, glob="**")])
    model.final = SUBMIT
    result = run(model, small, Budget(max_turns=2))
    assert (result.tokens_in, result.tokens_cached) == (200, 150)


def test_code_tools_are_offered_only_when_asked(small: Repository) -> None:
    """Off, CodeSearch is no tool of the agent's; on, it finds code by shape and Outline lists a file's parts."""
    off = ScriptedModel([call("CodeSearch", 1, pattern="return $X", paths="action/*.py"), call("Submit", 2, **SUBMIT)])
    run(off, small)
    assert "CodeSearch" not in off.tools
    assert str(off.sent[1][-1].content) == "No tool called CodeSearch."
    on = ScriptedModel(
        [
            call("CodeSearch", 1, pattern="return $X", paths="action/*.py"),
            call("Outline", 2, path="action/agent.py"),
            call("Submit", 3, **SUBMIT),
        ]
    )
    run(on, small, code_tools=True)
    assert {"CodeSearch", "Outline"} <= set(on.tools)
    assert str(on.sent[1][-1].content) == "action/agent.py:2: return cmd"
    assert str(on.sent[2][-1].content) == "1-2: def run_shell(cmd):"
    assert "Outline" in str(on.sent[0][0].content) and "Outline" not in str(off.sent[0][0].content)


@pytest.mark.parametrize(("pattern", "error"), [("def (", "ValueError"), ("a; b", "RuntimeError")])
def test_a_broken_code_search_says_why(small: Repository, pattern: str, error: str) -> None:
    """A pattern that parses in no language of the files, or that ast-grep refuses, comes back as the tool's error,
    not a crash."""
    model = ScriptedModel([call("CodeSearch", 1, pattern=pattern, paths="action/*.py"), call("Submit", 2, **SUBMIT)])
    run(model, small, code_tools=True)
    assert str(model.sent[1][-1].content).startswith(f"CodeSearch failed: {error}")


def test_hints_are_added_to_the_prompt_only_when_asked(small: Repository) -> None:
    """The syntax hints go in the system prompt when asked for, and not otherwise."""
    on, off = ScriptedModel([call("Submit", 1, **SUBMIT)]), ScriptedModel([call("Submit", 1, **SUBMIT)])
    run(on, small, hints=True)
    run(off, small)
    assert "Syntax that often fails" in str(on.sent[0][0].content)
    assert "Syntax that often fails" not in str(off.sent[0][0].content)


def test_a_submit_beside_another_tool_call_in_the_last_call_is_read(small: Repository) -> None:
    """The model calls TryCheck and Submit in its last call; the Submit is still recorded."""
    model = ScriptedModel([call("ListFiles", 1, glob="**")])
    model.final_calls = [
        [
            {"name": "TryCheck", "args": {"steps": [FILE_STEP]}, "id": "f1"},
            {"name": "Submit", "args": SUBMIT, "id": "f2"},
        ]
    ]
    result = run(model, small, Budget(max_turns=2))
    assert result.unfinished == [] and result.stopped is None


def test_an_unreadable_last_call_is_made_once_more(small: Repository) -> None:
    """A last call with no Submit in it gets one more try, told that only Submit exists."""
    model = ScriptedModel([call("ListFiles", 1, glob="**")])
    model.final_calls = [[{"name": "TryCheck", "args": {"steps": [FILE_STEP]}, "id": "f1"}]]
    model.final = SUBMIT
    result = run(model, small, Budget(max_turns=2))
    assert result.unfinished == [] and result.turns == 3
    assert str(model.sent[-1][-1].content).startswith("Only the Submit tool exists now")


def test_checks_sent_as_json_text_are_read() -> None:
    """DeepSeek sometimes sends the checks list as JSON text; Submit reads it as the list."""
    import json

    from audit_cli.checks.writer import Submit

    submission = Submit.model_validate({"checks": json.dumps(SUBMIT["checks"]), "no_checks": SUBMIT["no_checks"]})
    assert [c.claim for c in submission.checks] == ["c1"]


def test_a_last_submit_for_other_claims_is_tried_again(small: Repository) -> None:
    """A last call that submits only labels the batch does not have gets its second try."""
    model = ScriptedModel([call("ListFiles", 1, glob="**")])
    model.final_calls = [[{"name": "Submit", "args": {"no_checks": [{"claim": "c9", "reason": "x"}]}, "id": "f1"}]]
    model.final = SUBMIT
    result = run(model, small, Budget(max_turns=2))
    assert result.unfinished == [] and result.turns == 3
