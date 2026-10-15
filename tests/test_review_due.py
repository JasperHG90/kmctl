import json
import os
import subprocess
from pathlib import Path

from typer.testing import CliRunner, Result

from kmctl import app

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
