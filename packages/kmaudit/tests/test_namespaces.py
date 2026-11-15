"""Any folder of markdown docs is a namespace with its own store (ADR 0043)."""

import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from kmaudit import AuditError, verbs
from kmaudit.cli import app
from kmaudit.coverage import coverage
from kmaudit.sections import concept_sections, resolve_target
from kmaudit.steps import Repository
from kmaudit.ui import build
from typer.testing import CliRunner

from .fixtures.audit_repo import git, make_repo

GUIDE = """# Guide

## Output

The CLI writes `out.txt` in `src/tool.py`.

## Start

It reads `config.toml` on start.
"""

README = "# Docs\n\n## About\n\nThese docs describe the tool.\n"
NESTED = "# Deep\n\n## Part\n\nThe tool has a deep part.\n"
INDEX = "# Index\n\n## Pages\n\nThe index lists the pages.\n"


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The fixture repository with an .okf/ bundle and a plain docs/ folder."""
    root = make_repo(tmp_path / "repo")
    docs = root / "docs"
    (docs / "sub").mkdir(parents=True)
    (docs / "guide.md").write_text(GUIDE)
    (docs / "README.md").write_text(README)
    (docs / "index.md").write_text(INDEX)
    (docs / "sub" / "deep.md").write_text(NESTED)
    git(root, "add", ".")
    git(root, "commit", "-qm", "docs")
    monkeypatch.chdir(root)
    return root


def run(*args: str, stdin: str | None = None) -> tuple[int, str, str]:
    """Run kmaudit with ``args``; (exit code, stdout, stderr)."""
    result = CliRunner().invoke(app, list(args), input=stdin)
    return result.exit_code, result.stdout, result.stderr


def todo(path: str = ".") -> dict:
    """What the claims_todo tool returns for ``path``, parsed."""
    return json.loads(verbs.todo(Path(path)).model_dump_json())


def submit(text: str, path: str = ".") -> dict:
    """What the claims_submit tool returns for the answers ``text`` sent to ``path``, parsed."""
    return json.loads(verbs.submit(Path(path), text).model_dump_json())


def refusal(path: str) -> str:
    """Why the claims_todo tool refuses ``path``."""
    with pytest.raises(AuditError) as refused:
        todo(path)
    return str(refused.value)


def answers(sections: list[dict], tag: str) -> str:
    """Answers for ``sections``: one point claim per sentence, its text tagged."""
    return json.dumps(
        [
            {
                "section": s["id"],
                "key": s["key"],
                "sentences": [
                    {
                        "n": t["n"],
                        "how_to_check": "open the file",
                        "reason": "names a file",
                        "kind": "point",
                        "claims": [
                            {
                                "claim": f"{tag} {s['id']} {t['n']}",
                                "quantifier": "exists",
                            }
                        ],
                    }
                    for t in s["sentences"]
                ],
            }
            for s in sections
        ]
    )


def claims_of(path: str) -> list[str]:
    """The claim texts ``kmaudit claims list PATH --claims --json`` shows."""
    code, out, err = run("claims", "list", path, "--claims", "--json")
    assert code == 0, err
    return [c["claim"] for c in json.loads(out)["claims"]]


def test_plain_folder_hands_out_every_section_of_every_page(repo: Path) -> None:
    out = todo("docs")
    docs = (repo / "docs").resolve()
    expected = {
        s.id
        for page in ("guide.md", "README.md", "index.md", "sub/deep.md")
        for s in concept_sections(docs, docs / page)
    }

    assert {s["id"] for s in out["sections"]} == expected
    assert len(expected) == 5
    assert out["namespace"] == "docs"


def test_namespaces_stay_apart_and_submit_names_its_own(repo: Path) -> None:
    docs = todo("docs")
    okf = todo(".okf")

    assert docs["next"] == "claims_submit with folder docs"
    assert okf["namespace"] == ".okf"
    assert submit(answers(docs["sections"], "D"), "docs")["refused"] == []
    assert submit(answers(okf["sections"], "O"), ".okf")["refused"] == []
    assert claims_of("docs") and all(c.startswith("D ") for c in claims_of("docs"))
    assert claims_of(".okf") and all(c.startswith("O ") for c in claims_of(".okf"))
    assert sorted(p.name for p in (repo / ".kmaudit").glob("*.sqlite")) == [
        ".okf.sqlite",
        "docs.sqlite",
    ]


def test_docs_answers_sent_to_okf_are_refused_not_stored(repo: Path) -> None:
    docs = todo("docs")
    todo(".okf")

    result = submit(answers(docs["sections"], "D"))

    assert result["stored"] == [] and result["refused"]
    assert not any(c.startswith("D ") for c in claims_of(".okf"))


def test_a_path_inside_a_namespace_maps_to_it(repo: Path) -> None:
    todo("docs")

    page = resolve_target(repo / "docs" / "sub" / "deep.md")
    folder = resolve_target(repo / "docs" / "sub")

    assert page.namespace == folder.namespace == "docs"
    assert page.concepts == folder.concepts == {"sub/deep"}
    assert sorted(p.name for p in (repo / ".kmaudit").glob("*.sqlite")) == [
        "docs.sqlite"
    ]


def test_a_folder_holding_a_namespace_maps_to_a_refusal_naming_it(repo: Path) -> None:
    todo("docs/sub")

    assert "docs/sub" in refusal("docs")


def test_a_page_with_no_namespace_above_it_is_refused(repo: Path) -> None:
    err = refusal("docs/guide.md")

    assert "give its folder first, such as docs," in err


def test_a_check_never_reads_the_audited_folder(repo: Path) -> None:
    (repo / "handbook").mkdir()
    (repo / "handbook" / "page.py").write_text("x = 1\n")
    (repo / "handbook" / "guide.md").write_text(GUIDE)
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "handbook")
    target = resolve_target(repo / "handbook")

    files = Repository(target.root, target.bundle).tracked
    whole = Repository(target.root).tracked

    assert "handbook/page.py" in whole
    assert not [f for f in files if f.startswith("handbook/")]


def test_namespaces_lists_each_with_counts(repo: Path) -> None:
    docs = todo("docs")
    submit(answers(docs["sections"], "D"), "docs")
    todo(".okf")

    code, out, err = run("namespaces", "--json")
    rows = {r["namespace"]: r for r in json.loads(out)["namespaces"]}
    _, text, _ = run("namespaces")

    assert code == 0, err
    assert set(rows) == {".okf", "docs"}
    assert rows["docs"]["folder"] == str((repo / "docs").resolve())
    assert rows["docs"]["sections"] == len(docs["sections"])
    assert rows["docs"]["claims"] > 0
    assert rows[".okf"]["claims"] == 0
    assert len(text.splitlines()) == 2


def _rows(path: Path) -> dict[str, int]:
    """Each table's row count in the SQLite file at ``path``."""
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        tables = [
            r[0]
            for r in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        ]
        return {
            t: db.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0] for t in tables
        }
    finally:
        db.close()


def test_the_old_store_is_copied_into_okf(repo: Path) -> None:
    okf = todo(".okf")
    submit(answers(okf["sections"], "O"))
    old = repo / ".kmctl" / "audit.sqlite"
    old.parent.mkdir()
    shutil.move(repo / ".kmaudit" / ".okf.sqlite", old)
    shutil.rmtree(repo / ".kmaudit")
    before = old.read_bytes()
    expected = {t: n for t, n in _rows(old).items() if t != "meta"}

    again = todo(".okf")

    copied = _rows(repo / ".kmaudit" / ".okf.sqlite")
    assert {t: n for t, n in copied.items() if t in expected} == expected
    assert old.read_bytes() == before
    assert again["sections"] == []


def test_the_root_means_okf_when_it_holds_one(repo: Path) -> None:
    assert todo()["namespace"] == ".okf"
    assert todo(".")["namespace"] == ".okf"


def test_a_root_without_okf_is_refused_rather_than_a_namespace_for_everything(
    repo: Path,
) -> None:
    shutil.rmtree(repo / ".okf")

    err = refusal(".")

    assert "such as docs" in err
    assert not (repo / ".kmaudit" / "..sqlite").exists()
    assert todo("docs")["namespace"] == "docs"


def test_page_and_coverage_work_for_a_plain_folder(repo: Path) -> None:
    (repo / "handbook").mkdir()
    (repo / "handbook" / "page.py").write_text("x = 1\n")
    (repo / "handbook" / "guide.md").write_text(GUIDE)
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "handbook")
    todo("handbook")
    todo(".okf")

    data = build(repo / "handbook")
    measured = coverage(repo / "handbook")

    assert [d.path for d in data.concepts] == ["handbook/guide.md"]
    assert not [f for f in data.code.files if f.path.startswith("handbook/")]
    assert not [f for f in measured.by_file if f.path.startswith("handbook/")]
    assert "handbook/page.py" in {f.path for f in coverage(repo / ".okf").by_file}


def test_the_old_store_copies_once_when_processes_open_it_at_once(repo: Path) -> None:
    okf = todo(".okf")
    submit(answers(okf["sections"], "O"))
    old = repo / ".kmctl" / "audit.sqlite"
    old.parent.mkdir()
    shutil.move(repo / ".kmaudit" / ".okf.sqlite", old)
    shutil.rmtree(repo / ".kmaudit")
    kmaudit = Path(sys.executable).parent / "kmaudit"

    procs = [
        subprocess.Popen(
            [str(kmaudit), "claims", "list", ".okf", "--json"],
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(6)
    ]
    results = [(p.wait(timeout=120), p.stderr.read()) for p in procs]

    assert [r for r in results if r[0] != 0] == []
    assert list((repo / ".kmaudit").glob("*.partial")) == []
    assert any(c.startswith("O ") for c in claims_of(".okf"))


@pytest.fixture
def nested(repo: Path) -> Path:
    """The fixture repository with a nested namespace, handbook/guides, holding claims."""
    guides = repo / "handbook" / "guides"
    guides.mkdir(parents=True)
    (guides / "guide.md").write_text(GUIDE)
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "handbook")
    sections = todo("handbook/guides")["sections"]
    submit(answers(sections, "H"), "handbook/guides")
    return repo


def test_a_nested_namespace_lists_its_counts(nested: Path) -> None:
    """A store named handbook%2Fguides.sqlite opens, so its counts are listed (the %2F once broke the URI)."""
    todo("docs")

    code, out, err = run("namespaces", "--json")
    rows = {r["namespace"]: r for r in json.loads(out)["namespaces"]}

    assert code == 0, err
    assert (nested / ".kmaudit" / "handbook%2Fguides.sqlite").is_file()
    assert set(rows) == {"docs", "handbook/guides"}
    assert rows["handbook/guides"]["sections"] == 2
    assert rows["handbook/guides"]["claims"] > 0


@pytest.mark.parametrize("name", ["r%2Fx", "r#x", "r?x", "r%x#y?z"])
def test_read_only_uri_opens_a_path_with_uri_characters(
    tmp_path: Path, name: str
) -> None:
    """``read_only_uri`` quotes %, # and ?, so SQLite opens the file the path names."""
    from kmaudit.namespaces import read_only_uri

    path = tmp_path / name / "a%2Fb.sqlite"
    path.parent.mkdir()
    sqlite3.connect(path).execute("CREATE TABLE t (x)").connection.close()

    db = sqlite3.connect(read_only_uri(path), uri=True)
    try:
        assert db.execute("SELECT count(*) FROM t").fetchone() == (0,)
    finally:
        db.close()


def test_read_only_uri_takes_a_relative_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A relative path resolves against the working directory rather than raising."""
    from kmaudit.namespaces import read_only_uri

    monkeypatch.chdir(tmp_path)
    sqlite3.connect("rel.sqlite").close()

    assert (
        read_only_uri(Path("rel.sqlite"))
        == (tmp_path / "rel.sqlite").resolve().as_uri() + "?mode=ro"
    )


def test_the_old_store_copies_from_a_repository_path_with_uri_characters(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The legacy store copy opens its source read-only through a quoted URI (uri)."""
    root = make_repo(tmp_path / "r%x#y")
    monkeypatch.chdir(root)
    okf = todo(".okf")
    submit(answers(okf["sections"], "O"))
    old = root / ".kmctl" / "audit.sqlite"
    old.parent.mkdir()
    shutil.move(root / ".kmaudit" / ".okf.sqlite", old)
    shutil.rmtree(root / ".kmaudit")

    again = todo(".okf")

    assert (root / ".kmaudit" / ".okf.sqlite").is_file()
    assert again["sections"] == []
