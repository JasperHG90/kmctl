"""The fixes from the first audit of kmctl's own decision log (ADR 0002, I4)."""

import re
from pathlib import Path

from conftest import okf_validate
from test_okf_fields import _paths

from kmctl.okf import ALLOWED_FIELDS, front_matter

ROOT = Path(__file__).resolve().parents[1]
OKF = ROOT / ".okf"
DECISIONS = OKF / "decisions"


def _records() -> list[Path]:
    return sorted(p for p in DECISIONS.glob("*.md") if p.name != "index.md")


def test_bundle_keys_are_allowed() -> None:
    bad = {}
    for page in sorted(OKF.rglob("*.md")):
        extra = _paths(front_matter(page)) - set(ALLOWED_FIELDS)
        if extra:
            bad[str(page.relative_to(ROOT))] = sorted(extra)

    assert bad == {}


def test_records_have_consequences() -> None:
    records = _records()
    log = (OKF / "log.md").read_text(encoding="utf-8")

    assert len(records) == 12
    missing = [
        p.name
        for p in records
        if not re.search(r"^#+ Consequences\s*$", p.read_text(), re.MULTILINE)
    ]
    assert missing == []
    unlogged = [p.stem for p in records if f"`decisions/{p.stem}`" not in log]
    assert unlogged == []


def test_bundle_valid() -> None:
    check = okf_validate(OKF)

    assert check.returncode == 0, check.stdout + check.stderr


def test_supersede_docstring() -> None:
    assert (
        "decision_status" not in (ROOT / "src" / "kmctl" / "supersede.py").read_text()
    )
