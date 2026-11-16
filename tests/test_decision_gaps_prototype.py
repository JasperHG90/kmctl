"""The decision-gaps prototype: its scripts reproduce its results and its README reports what score.py prints."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / ".okf" / "prototypes" / "decision-gaps"
SCRIPTS = PROTOTYPE / "scripts"
RESULTS = PROTOTYPE / "results"


def _run(*args: str) -> str:
    """Run a prototype script with this interpreter and return its stdout."""
    return subprocess.run(
        [sys.executable, *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout


def _score() -> str:
    """score.py's output over the committed results."""
    return _run(str(SCRIPTS / "score.py"), str(RESULTS))


def _readme() -> str:
    """The prototype README with whitespace collapsed."""
    return " ".join((PROTOTYPE / "README.md").read_text().split())


@pytest.mark.integration
def test_units_and_signals_reproduce_the_committed_results() -> None:
    """Rerunning units.py and signals.py over the fixed range gives the committed files.

    Marked integration because it needs the repository's full history, which
    the loop's integration gate has and CI's shallow test checkout does not,
    as for test_cutoff_matches_tags.
    """
    units = _run(str(SCRIPTS / "units.py"), ".")
    assert units == (RESULTS / "units.jsonl").read_text()
    signals = _run(str(SCRIPTS / "signals.py"), ".", str(RESULTS / "units.jsonl"))
    assert signals == (RESULTS / "signals.jsonl").read_text()


def test_readme_filter_table_is_what_score_prints() -> None:
    """Each filter row score.py prints is a row of the README's filter table."""
    rows = re.findall(
        r"score >= (\d) \| (\d+/\d+ \(\d+%\)) \| (\d+/\d+ \(\d+%\))", _score()
    )
    readme = _readme()

    assert len(rows) == 5
    for threshold, kept, caught in rows:
        assert f"| {threshold} | {kept} | {caught} |" in readme


def test_judge_numbers_in_the_readme_are_what_score_prints() -> None:
    """Judge recall with its interval, misses, claims by label, precision, cost and time match score.py."""
    out = _score()
    readme = _readme()
    recall = re.search(
        r"judge recall (\d+/\d+ \(\d+%\)), 95% Wilson (\d+%) to (\d+%)", out
    )
    missed = re.search(r"judge missed (ADR [\d, ]+)", out)
    claims = re.search(
        r"claims on negatives (\d+)/130 \((\d+%)\): (\d+) gap, (\d+) false alarm, (\d+) recorded in the unit",
        out,
    )
    precision = re.search(
        r"precision (\d+/\d+ \(\d+%\)), 95% Wilson (\d+%) to (\d+%)", out
    )
    cost = re.search(
        r"cost (\$[\d.]+) for the range, (\$[\d.]+) per unit; (\d+) minutes, ([\d.]+) s per unit",
        out,
    )
    assert recall and missed and claims and precision and cost

    assert f"{recall[1]}, 95% Wilson {recall[2]} to {recall[3]}" in readme
    assert missed[1].strip() in readme
    assert (
        f"{claims[1]} ({claims[2]}): {claims[3]} gap, {claims[4]} false alarm, "
        f"{claims[5]} recorded in the unit" in readme
    )
    assert f"{precision[1]}, 95% Wilson {precision[2]} to {precision[3]}" in readme
    assert (
        f"{cost[1]} for the range, {cost[2]} per unit; {cost[3]} minutes, {cost[4]} s per unit"
        in readme
    )


def test_judge_verdict_and_record_only_count_match_score() -> None:
    """score.py keeps ADR 0030 out of recall, and the README's verdict is score.py's verdict against the plan's bars."""
    out = _score()
    readme = _readme()

    assert "positives counted 30, record-only apart 1 (ADR 0030)" in out
    assert "30 positives count" in readme
    verdict = re.search(r"verdict: (build|do not build)", out)
    assert verdict
    if verdict[1] == "build":
        assert (
            "All four bars are met, so `kmctl decision candidates` and its skill are worth building"
            in readme
        )
    else:
        assert "not worth building" in readme
