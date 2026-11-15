"""Tests for mutation-testing checks: a check that tests code notices changes to it; one pinned to a comment does not."""

import pathlib as plb
import subprocess

import pytest
from pydantic import TypeAdapter

from audit_cli.checks.mutate import measure, mutants
from audit_cli.checks.steps import Repository, Step, run_check

STEPS = TypeAdapter(list[Step])
AGENT = '''SEVERITIES = ("low", "high")


def publish(findings, min_severity="high"):
    # findings: mismatches only
    """Post the report."""
    if not findings:
        return 0
    return 1
'''
WORKFLOW = "jobs:\n  publish:\n    if: ${{ success() }}\n    steps:\n      - uses: actions/checkout@abc # v4\n"


@pytest.fixture
def repo(tmp_path: plb.Path) -> Repository:
    """A repository with a Python file and a workflow."""
    root = tmp_path / "mutated"
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / "agent.py").write_text(AGENT)
    (root / ".github" / "workflows" / "audit.yml").write_text(WORKFLOW)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    return Repository(root)


def quality(repo: Repository, *steps: dict[str, object]) -> tuple[int, int]:
    """Run a holding check against its mutants and return (mutants, killed)."""
    parsed = STEPS.validate_python(list(steps))
    holds, results = run_check(repo, parsed)
    assert holds
    q = measure(repo, parsed, [r.detail for r in results])
    return q.mutants, q.killed


def test_a_check_pinned_to_a_comment_notices_no_change(repo: Repository) -> None:
    """A grep for a comment that restates the claim holds whatever the code does, and so kills no mutant."""
    tried, killed = quality(repo, {"op": "grep", "pattern": "findings: mismatches only", "paths": "agent.py"})
    assert tried > 0 and killed == 0


def test_a_check_of_the_code_notices_a_change_to_it(repo: Repository) -> None:
    """A code step on the default it claims notices when the default changes."""
    tried, killed = quality(
        repo, {"op": "code", "pattern": 'def publish($$$A, min_severity="high"): $$$B', "paths": "agent.py"}
    )
    assert tried > 0 and killed > 0


def test_a_query_is_tested_on_the_value_it_returned(repo: Repository) -> None:
    """A query's mutants change the line holding the value it returned, so a check of that value notices."""
    _, killed = quality(
        repo,
        {
            "op": "query",
            "paths": ".github/workflows/audit.yml",
            "query": "jobs.publish.if",
            "expect": "equals",
            "value": "${{ success() }}",
        },
    )
    assert killed > 0


def test_a_yaml_value_with_a_trailing_comment_is_changed(repo: Repository) -> None:
    """A pinned action line ends in a comment; its value is still replaced, and the comment kept."""
    steps = STEPS.validate_python(
        [{"op": "grep", "pattern": "uses: actions/checkout@", "paths": ".github/workflows/audit.yml"}]
    )
    _, results = run_check(repo, steps)
    found = [m for m in mutants(repo, steps, [r.detail for r in results]) if m.line == 5]
    assert found and found[0].text is not None and "uses: mutated # v4" in found[0].text


def test_every_mutant_still_parses_and_docstrings_are_left_alone(repo: Repository) -> None:
    """No mutant breaks the file's syntax, and none touches the docstring or the comment."""
    steps = STEPS.validate_python([{"op": "definition", "name": "publish", "paths": "agent.py"}])
    _, results = run_check(repo, steps)
    found = mutants(repo, steps, [r.detail for r in results])
    assert found and all(m.text is None or compile(m.text, "agent.py", "exec") for m in found)
    assert all(m.line not in {5, 6} for m in found)


def test_a_help_only_check_is_not_measured(repo: Repository) -> None:
    """A help step runs the CLI from disk, which an edit in memory never reaches: no mutants, no score."""
    steps = STEPS.validate_python([{"op": "help", "command": "x", "pattern": "y"}])
    assert mutants(repo, steps, ["could not run"]) == []


def _write(repo: Repository, path: str, text: str) -> Repository:
    """Add a tracked file and return the repository read afresh."""
    (repo.root / path).parent.mkdir(parents=True, exist_ok=True)
    (repo.root / path).write_text(text)
    subprocess.run(["git", "-C", str(repo.root), "add", "-A"], check=True)
    return Repository(repo.root)


def test_a_check_that_matched_only_a_docstring_is_marked_text_only(repo: Repository) -> None:
    """With no code within reach of its match there is nothing to change, so it says it matched only text."""
    from audit_cli.checks.mutate import TEXT_ONLY

    fresh = _write(repo, "doc.py", '"""Workers retry.\n\nThey retry\nthree times with backoff,\nalways.\n\nEnd.\n"""\n')
    steps = STEPS.validate_python([{"op": "grep", "pattern": "three times with backoff", "paths": "doc.py"}])
    _, results = run_check(fresh, steps)
    assert TEXT_ONLY in measure(fresh, steps, [r.detail for r in results]).survived


@pytest.mark.parametrize(
    ("path", "text", "step"),
    [
        (
            "conf.py",
            'DEFAULTS = {\n    "timeout": 30,\n    "retries": 3,\n}\n',
            {"op": "grep", "pattern": '"timeout": 30', "paths": "conf.py"},
        ),
        (
            "settings.json",
            '{\n  "timeout": 30,\n  "retries": 3\n}\n',
            {"op": "query", "paths": "settings.json", "query": "timeout", "expect": "equals", "value": 30},
        ),
    ],
)
def test_code_lines_that_start_with_a_quote_are_changed(
    repo: Repository, path: str, text: str, step: dict[str, object]
) -> None:
    """A dict entry or a JSON key starts with a quote but is code: it is changed, and a check of it notices."""
    fresh = _write(repo, path, text)
    tried, killed = quality(fresh, step)
    assert tried > 0 and killed > 0


def test_a_deleted_file_is_no_credit_for_a_check_that_also_reads_its_text(repo: Repository) -> None:
    """Deleting the file fails every step that reads it, so it only counts for a check made of file steps alone."""
    fresh = _write(repo, "x.py", "# retries are capped\ndef go():\n    return 1\n")
    tried, killed = quality(
        fresh,
        {"op": "file", "path": "x.py"},
        {"op": "grep", "pattern": "retries are capped", "paths": "x.py"},
    )
    assert tried > 0 and killed == 0


def test_a_yes_no_query_is_tested_on_the_values_it_compares_to(repo: Repository) -> None:
    """A query that returns true or false names its values in the query; the lines holding them are changed."""
    tried, killed = quality(
        repo,
        {
            "op": "query",
            "paths": ".github/workflows/audit.yml",
            "query": "contains(jobs.publish.steps[].uses, 'actions/checkout@abc')",
            "expect": "equals",
            "value": True,
        },
    )
    assert tried > 0 and killed > 0
