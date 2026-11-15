import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner, Result

from kmctl import app
from kmctl.okf import as_datetime
from kmctl.review_due import verification_commits
from kmctl.verify import verify

OLD = "2026-01-01T00:00:00+00:00"
VERIFIED = "2026-06-01T00:00:00Z"
NEW = "2026-09-01T00:00:00+00:00"


def _git(root: Path, *args: str, date: str = OLD) -> None:
    """Run git in ``root`` with a fixed author and commit date."""
    env = os.environ | {
        "GIT_AUTHOR_DATE": date,
        "GIT_COMMITTER_DATE": date,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
    }
    subprocess.run(["git", *args], cwd=root, env=env, check=True, capture_output=True)


def _write(root: Path, rel: str, text: str) -> None:
    """Write ``text`` to ``root / rel``, making its folders."""
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _concept(root: Path, rel: str, extra: str = "", verified: bool = True) -> None:
    """Write a concept at ``.okf/rel`` with optional extra front matter lines."""
    stamp = f"verified:\n  - {{by: 'human:j', at: '{VERIFIED}'}}\n" if verified else ""
    _write(
        root,
        f".okf/{rel}",
        f'---\ntype: note\ntitle: "{rel}"\ndescription: "A note."\n{stamp}{extra}---\n\n# {rel}\n',
    )


def _repo(root: Path) -> None:
    """A git repository with a bundle and one committed source file."""
    _git(root, "init", "-q", "-b", "main")
    _write(root, ".okf/index.md", '---\nokf_version: "0.2"\n---\n')
    _write(root, "src/app.py", "x = 1\n")


def _commit(root: Path, date: str = OLD) -> None:
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "c", date=date)


def _due(root: Path, *args: str) -> Result:
    return CliRunner().invoke(app, ["review", "due", "--path", str(root), *args])


def _data(root: Path) -> dict:
    return json.loads(_due(root, "--json").stdout)


def _reasons(root: Path) -> dict[str, list[str]]:
    return {d["id"]: d["reasons"] for d in _data(root)["due"]}


def test_due_stale_after(tmp_path: Path) -> None:
    _repo(tmp_path)
    _concept(tmp_path, "stale.md", "stale_after: 2020-01-01T00:00:00Z\n")
    _concept(tmp_path, "fresh.md", "stale_after: 2999-01-01T00:00:00Z\n")
    _commit(tmp_path)

    assert _reasons(tmp_path) == {"stale": ["stale_after passed"]}


def test_due_unverified(tmp_path: Path) -> None:
    _repo(tmp_path)
    _concept(tmp_path, "new.md", verified=False)
    _commit(tmp_path)

    assert _reasons(tmp_path) == {"new": ["unverified"]}


def test_due_source_changed_each_form(tmp_path: Path) -> None:
    _repo(tmp_path)
    _write(tmp_path, ".okf/decisions/notes.txt", "n\n")
    _concept(tmp_path, "target.md")
    forms = {
        "bundle-root": "/target.md",
        "concept-relative": "notes.txt",
        "repo-root": "src/app.py",
        "concept-id": "target",
    }
    for name, resource in forms.items():
        _concept(
            tmp_path,
            f"decisions/{name}.md",
            f"sources:\n  - {{id: s, resource: '{resource}'}}\n",
        )
    _commit(tmp_path)

    assert _reasons(tmp_path) == {}

    for rel in ("src/app.py", ".okf/decisions/notes.txt"):
        (tmp_path / rel).write_text("changed\n")
    target = (tmp_path / ".okf/target.md").read_text()
    (tmp_path / ".okf/target.md").write_text(target + "\nmore\n")
    _commit(tmp_path, date=NEW)

    reasons = _reasons(tmp_path)
    assert {k: v for k, v in reasons.items() if k != "target"} == {
        f"decisions/{name}": [f"source changed: {forms[name]}"] for name in forms
    }


def test_sources_urls_and_unresolved(tmp_path: Path) -> None:
    _repo(tmp_path)
    _concept(
        tmp_path,
        "mixed.md",
        "sources:\n  - {id: u, resource: 'https://example.com/x'}\n"
        "  - {id: f, resource: 'all queries in project X'}\n",
    )
    _commit(tmp_path)

    data = _data(tmp_path)

    assert data["due"] == []
    assert [(n["id"], n["resource"]) for n in data["notices"]] == [
        ("mixed", "all queries in project X")
    ]


def test_handoffs_excluded_and_listed_once(tmp_path: Path) -> None:
    _repo(tmp_path)
    _concept(
        tmp_path,
        "handoffs/live.md",
        "stale_after: 2999-01-01T00:00:00Z\n",
        verified=False,
    )
    _concept(
        tmp_path,
        "handoffs/old.md",
        "stale_after: 2020-01-01T00:00:00Z\n",
        verified=False,
    )
    _commit(tmp_path)

    data = _data(tmp_path)

    assert data["due"] == []
    assert [h["id"] for h in data["expired_handoffs"]] == ["handoffs/old"]


def test_shallow_clone_skips_history(tmp_path: Path) -> None:
    origin = tmp_path / "origin"
    origin.mkdir()
    _repo(origin)
    _concept(origin, "c.md", "sources:\n  - {id: s, resource: 'src/app.py'}\n")
    _commit(origin)
    (origin / "src/app.py").write_text("changed\n")
    _commit(origin, date=NEW)
    clone = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", origin.resolve().as_uri(), str(clone)],
        check=True,
        capture_output=True,
    )

    data = _data(clone)
    text = _due(clone).stdout

    assert data["due"] == []
    assert data["history_skipped"]
    assert "shallow" in text


def test_exit_and_json(tmp_path: Path) -> None:
    _repo(tmp_path)
    _concept(tmp_path, "new.md", verified=False)
    _commit(tmp_path)

    result = _due(tmp_path)
    as_json = _due(tmp_path, "--json")
    data = json.loads(as_json.stdout)

    assert result.exit_code == 0
    assert as_json.exit_code == 0
    assert [d["id"] for d in data["due"]] == ["new"]
    assert {"due", "notices", "expired_handoffs", "history_skipped"} <= data.keys()


def test_due_source_with_non_ascii_name(tmp_path: Path) -> None:
    _repo(tmp_path)
    _write(tmp_path, "src/café.py", "x = 1\n")
    _concept(tmp_path, "c.md", "sources:\n  - {id: s, resource: 'src/café.py'}\n")
    _commit(tmp_path)
    (tmp_path / "src/café.py").write_text("x = 2\n")
    _commit(tmp_path, date=NEW)

    assert _reasons(tmp_path) == {"c": ["source changed: src/café.py"]}


def test_due_source_folder(tmp_path: Path) -> None:
    _repo(tmp_path)
    _concept(tmp_path, "c.md", "sources:\n  - {id: s, resource: 'src'}\n")
    _commit(tmp_path)
    (tmp_path / "src/app.py").write_text("x = 2\n")
    _commit(tmp_path, date=NEW)

    assert _reasons(tmp_path) == {"c": ["source changed: src"]}


def _docs_page(root: Path, rel: str, front: str) -> None:
    """Write a docs page at ``docs/rel`` with ``front`` as its front matter, or none when empty."""
    head = f"---\n{front}---\n\n" if front else ""
    _write(root, f"docs/{rel}", f"{head}# {rel}\n")


def test_docs_page_stale_after(tmp_path: Path) -> None:
    _repo(tmp_path)
    _docs_page(tmp_path, "how-to/old.md", "stale_after: 2020-01-01\n")
    _docs_page(tmp_path, "how-to/fresh.md", "stale_after: 2999-01-01\n")
    _docs_page(tmp_path, "how-to/plain.md", "")
    _commit(tmp_path)

    data = _data(tmp_path)

    assert {d["id"]: d["reasons"] for d in data["due"]} == {
        "docs/how-to/old": ["stale_after passed"]
    }
    assert data["due"][0]["path"] == "docs/how-to/old.md"
    assert set(data) == {"due", "notices", "expired_handoffs", "history_skipped"}


def test_docs_page_source_changed_after_page_commit(tmp_path: Path) -> None:
    _repo(tmp_path)
    _docs_page(tmp_path, "reference/app.md", "sources:\n  - src/app.py\n")
    _commit(tmp_path)

    assert _reasons(tmp_path) == {}

    (tmp_path / "src/app.py").write_text("x = 2\n")
    _commit(tmp_path, date=NEW)

    assert _reasons(tmp_path) == {"docs/reference/app": ["source changed: src/app.py"]}

    page = tmp_path / "docs/reference/app.md"
    page.write_text(page.read_text() + "\nUpdated.\n")
    _commit(tmp_path, date="2026-09-02T00:00:00+00:00")

    assert _reasons(tmp_path) == {}


def test_docs_page_source_changed_after_verified(tmp_path: Path) -> None:
    _repo(tmp_path)
    _docs_page(
        tmp_path,
        "reference/app.md",
        f"verified:\n  - {{by: 'human:j', at: '{VERIFIED}'}}\nsources:\n  - resource: src/app.py\n",
    )
    _commit(tmp_path, date=NEW)
    (tmp_path / "src/app.py").write_text("x = 2\n")
    _commit(tmp_path, date="2026-09-02T00:00:00+00:00")

    assert _reasons(tmp_path) == {"docs/reference/app": ["source changed: src/app.py"]}


def test_docs_page_without_okf(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q", "-b", "main")
    _docs_page(tmp_path, "how-to/old.md", "stale_after: 2020-01-01\n")
    _commit(tmp_path)

    assert _reasons(tmp_path) == {"docs/how-to/old": ["stale_after passed"]}


def test_due_listing_names_kmctl_verify(tmp_path: Path) -> None:
    _repo(tmp_path)
    _concept(tmp_path, "new.md", verified=False)
    _commit(tmp_path)

    last = _due(tmp_path).stdout.strip().splitlines()[-1]

    assert last.startswith("Next: ")
    assert "kmctl verify ID --by human:" in last
    assert "--stale-after" in last


def test_nothing_due_names_no_verify(tmp_path: Path) -> None:
    _repo(tmp_path)
    _concept(tmp_path, "checked.md")
    _concept(
        tmp_path,
        "handoffs/old.md",
        "stale_after: 2020-01-01T00:00:00Z\n",
        verified=False,
    )
    _commit(tmp_path)

    assert "kmctl verify" not in _due(tmp_path).stdout


def test_json_keys_unchanged(tmp_path: Path) -> None:
    _repo(tmp_path)
    _concept(tmp_path, "new.md", verified=False)
    _commit(tmp_path)

    data = _data(tmp_path)

    assert set(data) == {"due", "notices", "expired_handoffs", "history_skipped"}


# Commit order, not dates, decides (issues #17 and #18). These commit dates
# run against the order on purpose: a landing is dated after the verification,
# and a later change may carry an earlier date.
LANDED = "2026-09-01T00:00:00+00:00"
CONCEPT = ("decisions/use-app", ".okf/decisions/use-app.md")
PAGE = ("docs/reference/app", "docs/reference/app.md")
LANDINGS = ("squash", "rebase", "merge")


def _verify(root: Path, cid: str, at: str, stale_after: str | None = None) -> None:
    """Record a person's verified entry for ``cid`` at the time ``at``, as kmctl verify does."""
    verify(
        root, cid, "human:j", stale_after=stale_after, now=datetime.fromisoformat(at)
    )


def _file(root: Path, target: tuple[str, str]) -> None:
    """Write the concept or docs page ``target`` with src/app.py as its source, unverified."""
    if target == CONCEPT:
        _concept(
            root,
            "decisions/use-app.md",
            "sources:\n  - {id: s, resource: 'src/app.py'}\n",
            verified=False,
        )
    else:
        _docs_page(
            root,
            "reference/app.md",
            'description: "A page."\nsources:\n  - src/app.py\n',
        )


def _verified(root: Path, target: tuple[str, str]) -> None:
    """A repository where ``target`` is committed, then verified in a commit of its own."""
    _repo(root)
    _file(root, target)
    _commit(root)
    _verify(root, target[0], VERIFIED)
    _commit(root, date=VERIFIED)


def _landed(root: Path, how: str, target: tuple[str, str]) -> None:
    """Issue #17: ``target`` is verified on a branch after its source changed, then lands by ``how``."""
    _repo(root)
    _file(root, target)
    _commit(root)
    _git(root, "switch", "-q", "-c", "feature")
    (root / "src/app.py").write_text("x = 2\n")
    _commit(root)
    _verify(root, target[0], VERIFIED)
    _commit(root, date=VERIFIED)
    _git(root, "switch", "-q", "main")
    _write(root, "other.txt", "main moved on\n")
    _commit(root, date=VERIFIED)
    if how == "squash":
        _git(root, "merge", "-q", "--squash", "feature", date=LANDED)
        _commit(root, date=LANDED)
    elif how == "rebase":
        _git(root, "switch", "-q", "feature")
        _git(root, "rebase", "-q", "main", date=LANDED)
        _git(root, "switch", "-q", "main")
        _git(root, "merge", "-q", "--ff-only", "feature", date=LANDED)
    else:
        _git(root, "merge", "-q", "--no-ff", "-m", "merge", "feature", date=LANDED)


@pytest.mark.parametrize("how", LANDINGS)
def test_not_due_after_landing(tmp_path: Path, how: str) -> None:
    _landed(tmp_path, how, CONCEPT)

    assert _reasons(tmp_path) == {}


@pytest.mark.parametrize("how", LANDINGS)
def test_source_changed_after_verification(tmp_path: Path, how: str) -> None:
    _landed(tmp_path, how, CONCEPT)
    (tmp_path / "src/app.py").write_text("x = 3\n")
    _commit(tmp_path)  # dated before the verification: the order still counts

    assert _reasons(tmp_path) == {CONCEPT[0]: ["source changed: src/app.py"]}


def _edit(root: Path, rel: str, edit: str) -> None:
    """Change the file at ``rel``: append to its body, or change its description."""
    path = root / rel
    text = path.read_text()
    if edit == "body":
        new = text + "\nEdited after verification.\n"
    else:
        new = text.replace('description: "A', 'description: "Another', 1)
    assert new != text
    path.write_text(new)


@pytest.mark.parametrize("edit", ["body", "description"])
def test_edited_after_verification(tmp_path: Path, edit: str) -> None:
    _verified(tmp_path, CONCEPT)
    _edit(tmp_path, CONCEPT[1], edit)
    _commit(tmp_path)

    assert _reasons(tmp_path) == {CONCEPT[0]: ["edited after verification"]}


def test_edited_after_verification_with_source_change(tmp_path: Path) -> None:
    _verified(tmp_path, CONCEPT)
    _edit(tmp_path, CONCEPT[1], "body")
    (tmp_path / "src/app.py").write_text("x = 2\n")
    _commit(tmp_path, date=NEW)

    assert _reasons(tmp_path) == {
        CONCEPT[0]: ["source changed: src/app.py", "edited after verification"]
    }


@pytest.mark.parametrize("stale_after", [None, "2999-01-01"])
def test_verify_only_commit(tmp_path: Path, stale_after: str | None) -> None:
    _verified(tmp_path, CONCEPT)
    _edit(tmp_path, CONCEPT[1], "body")
    (tmp_path / "src/app.py").write_text("x = 2\n")
    _commit(tmp_path, date=NEW)
    _verify(tmp_path, CONCEPT[0], NEW, stale_after)
    _commit(tmp_path)  # dated before both: only the order counts

    assert _reasons(tmp_path) == {}


def test_verify_only_commit_not_made_yet_counts_nothing(tmp_path: Path) -> None:
    _verified(tmp_path, CONCEPT)
    (tmp_path / "src/app.py").write_text("x = 2\n")
    _commit(tmp_path, date=NEW)
    _verify(tmp_path, CONCEPT[0], NEW)

    assert _reasons(tmp_path) == {}


def test_verify_only_commit_never_made_counts_nothing(tmp_path: Path) -> None:
    _repo(tmp_path)
    _file(tmp_path, CONCEPT)
    _commit(tmp_path)
    _verify(tmp_path, CONCEPT[0], VERIFIED)
    (tmp_path / "src/app.py").write_text("x = 2\n")
    _commit(tmp_path, date=NEW)

    assert _reasons(tmp_path) == {}


@pytest.mark.parametrize("how", LANDINGS)
def test_docs_page_not_due_after_landing(tmp_path: Path, how: str) -> None:
    _landed(tmp_path, how, PAGE)

    assert _reasons(tmp_path) == {}

    (tmp_path / "src/app.py").write_text("x = 3\n")
    _commit(tmp_path)

    assert _reasons(tmp_path) == {PAGE[0]: ["source changed: src/app.py"]}


@pytest.mark.parametrize("edit", ["body", "description"])
def test_docs_page_edited_after_verification(tmp_path: Path, edit: str) -> None:
    _verified(tmp_path, PAGE)
    _edit(tmp_path, PAGE[1], edit)
    _commit(tmp_path)

    assert _reasons(tmp_path) == {PAGE[0]: ["edited after verification"]}


@pytest.mark.parametrize("stale_after", [None, "2999-01-01"])
def test_docs_page_verify_only_commit(tmp_path: Path, stale_after: str | None) -> None:
    _verified(tmp_path, PAGE)
    _edit(tmp_path, PAGE[1], "body")
    (tmp_path / "src/app.py").write_text("x = 2\n")
    _commit(tmp_path, date=NEW)
    _verify(tmp_path, PAGE[0], NEW, stale_after)
    _commit(tmp_path)

    assert _reasons(tmp_path) == {}


def test_docs_page_unverified_baseline_by_commit(tmp_path: Path) -> None:
    _repo(tmp_path)
    _file(tmp_path, PAGE)
    _commit(tmp_path, date=NEW)
    (tmp_path / "src/app.py").write_text("x = 2\n")
    _commit(tmp_path)  # dated before the page's commit, but made after it

    assert _reasons(tmp_path) == {PAGE[0]: ["source changed: src/app.py"]}


def _per_file(root: Path, rel: str, newest: datetime) -> str | None:
    """The verification commit by one ``git log`` of ``rel`` alone, as a reference."""
    log = subprocess.run(
        ["git", "log", "--format=%H", "--", rel],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    found = None
    for commit in log:
        shown = subprocess.run(
            ["git", "show", f"{commit}:{rel}"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if shown.returncode == 0 and newest in _holds(shown.stdout):
            found = commit  # the log is newest first, so the last one is the oldest
    return found


def _holds(text: str) -> list[datetime]:
    meta = yaml.safe_load(text.split("\n---", 1)[0].removeprefix("---\n")) or {}
    entries = meta.get("verified") or []
    return [as_datetime(e["at"]) for e in entries]


def test_batched_walk_matches_per_file_log(tmp_path: Path) -> None:
    _repo(tmp_path)
    for name in ("a", "b", "c", "d", "old"):
        _concept(tmp_path, f"{name}.md", verified=False)
    _commit(tmp_path)
    day = iter(range(1, 31))

    def commit() -> None:
        _commit(tmp_path, date=f"2026-06-{next(day):02d}T00:00:00+00:00")

    def verify_now(cid: str) -> None:
        _verify(tmp_path, cid, f"2026-07-{next(day):02d}T00:00:00+00:00")

    # A merge commit: the branch verifies a, main verifies b. Both log it, so
    # the merge keeps main's .okf/log.md.
    _git(tmp_path, "switch", "-q", "-c", "feature")
    verify_now("a")
    commit()
    _git(tmp_path, "switch", "-q", "main")
    verify_now("b")
    commit()
    _git(tmp_path, "merge", "-q", "--no-ff", "-X", "ours", "-m", "merge", "feature")
    # A merge whose conflict resolution adds the verified entry to c.
    _git(tmp_path, "switch", "-q", "-c", "side")
    _edit(tmp_path, ".okf/c.md", "body")
    commit()
    _git(tmp_path, "switch", "-q", "main")
    (tmp_path / ".okf/c.md").write_text(
        (tmp_path / ".okf/c.md").read_text() + "\nMain.\n"
    )
    commit()
    subprocess.run(
        ["git", "merge", "-q", "side"], cwd=tmp_path, capture_output=True, check=False
    )
    _concept(tmp_path, "c.md", verified=False)
    verify_now("c")
    commit()
    # A rename: old is verified, then moved to renamed.md unchanged.
    verify_now("old")
    commit()
    _git(tmp_path, "mv", ".okf/old.md", ".okf/renamed.md")
    commit()
    # d is verified twice; the newest entry is the one that counts.
    verify_now("d")
    commit()
    verify_now("d")
    commit()

    newest = {
        f".okf/{name}.md": max(_holds((tmp_path / f".okf/{name}.md").read_text()))
        for name in ("a", "b", "c", "d", "renamed")
    }
    per_file = {rel: _per_file(tmp_path, rel, at) for rel, at in newest.items()}

    assert verification_commits(tmp_path, newest) == per_file
    assert all(per_file.values())


def test_docs_page_with_a_spaced_path_deleted_in_history(tmp_path: Path) -> None:
    _repo(tmp_path)
    rel = "docs/how/my page.md"
    _write(
        tmp_path,
        rel,
        f"---\nverified:\n  - {{by: 'human:j', at: '{VERIFIED}'}}\n---\n\n# Page\n",
    )
    _commit(tmp_path)
    _git(tmp_path, "rm", "-q", rel)
    _commit(tmp_path)
    _git(tmp_path, "checkout", "HEAD~1", "--", rel)
    _commit(tmp_path)

    result = _due(tmp_path, "--json")

    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["due"] == []
