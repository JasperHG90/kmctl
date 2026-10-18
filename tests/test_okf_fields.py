"""Invariant I4: kmctl writes and reads only allowed OKF fields (ADR 0009)."""

import ast
import os
import re
import subprocess
from pathlib import Path

import pytest
from conftest import okf_validate
from typer.testing import CliRunner

from kmctl import app
from kmctl.okf import ALLOWED_FIELDS, field, front_matter

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "kmctl"


def _invoke(*args: str) -> None:
    result = CliRunner().invoke(app, list(args))
    assert result.exit_code == 0, result.output


def _paths(value: object, prefix: str = "") -> set[str]:
    """Every key in a front matter value, nested keys as a.b and list items as a[].b."""
    if isinstance(value, dict):
        out: set[str] = set()
        for key, inner in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            out.add(path)
            out |= _paths(inner, path)
        return out
    if isinstance(value, list):
        return (
            set().union(*(_paths(item, f"{prefix}[]") for item in value))
            if value
            else set()
        )
    return set()


def _written_keys(root: Path) -> set[str]:
    keys: set[str] = set()
    for page in list((root / ".okf").rglob("*.md")) + list(
        (root / "docs").rglob("*.md")
    ):
        keys |= _paths(front_matter(page))
    return keys


def test_written_keys_are_allowed(tmp_path: Path) -> None:
    root = str(tmp_path)
    _invoke("init", "--path", root)
    for kind in ("decision", "practice", "proposal", "prototype", "handoff"):
        _invoke("new", kind, f"One {kind}", "--description", "One.", "--path", root)
    _invoke(
        "new", "handoff", "Keyed", "--description", "K.", "--key", "k-1", "--path", root
    )
    _invoke(
        "new",
        "handoff",
        "Keyed again",
        "--description",
        "K2.",
        "--key",
        "k-1",
        "--path",
        root,
    )
    _invoke("new", "decision", "Two", "--description", "Two.", "--path", root)
    _invoke("decision", "supersede", "1", "--by", "2", "--path", root)
    _invoke("new", "doc", "how-to", "Install", "--path", root)

    written = _written_keys(tmp_path)

    assert written, "the verbs wrote no front matter"
    assert written <= set(ALLOWED_FIELDS), written - set(ALLOWED_FIELDS)


def test_checked_keys_ack_writes_are_allowed(tmp_path: Path) -> None:
    """kmctl summary ack writes checked, checked.at and checked.against, all allowed (ADR 0027)."""
    env = os.environ | {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
    }

    def git(*args: str) -> None:
        subprocess.run(
            ["git", *args], cwd=tmp_path, env=env, check=True, capture_output=True
        )

    root = str(tmp_path)
    git("init", "-q", "-b", "main")
    _invoke("init", "--path", root)
    git("add", "-A")
    git("commit", "-q", "-m", "init")
    _invoke("new", "decision", "Use a queue", "--description", "One.", "--path", root)
    _invoke("summary", "ack", "--path", root)

    summary = _paths(front_matter(tmp_path / ".okf" / "summary.md"))
    written = _written_keys(tmp_path)

    assert {"checked", "checked.at", "checked.against"} <= summary
    assert written <= set(ALLOWED_FIELDS), written - set(ALLOWED_FIELDS)


def _front_matter_names(tree: ast.AST) -> set[str]:
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and _is_front_matter_call(node.value):
            names |= {t.id for t in node.targets if isinstance(t, ast.Name)}
    return names


def _is_front_matter_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return (isinstance(func, ast.Name) and func.id == "front_matter") or (
        isinstance(func, ast.Attribute) and func.attr == "front_matter"
    )


def _is_field_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "field"
    )


def _bad_reads(tree: ast.AST) -> list[str]:
    """Uses of a front_matter result other than as field()'s first argument, or as the assigned value."""
    names = _front_matter_names(tree)
    allowed_ids: set[int] = set()
    for node in ast.walk(tree):
        if _is_field_call(node) and node.args:
            allowed_ids.add(id(node.args[0]))
        if isinstance(node, ast.Assign) and _is_front_matter_call(node.value):
            allowed_ids.add(id(node.value))
    bad = []
    for node in ast.walk(tree):
        is_load = isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        if is_load and node.id in names and id(node) not in allowed_ids:
            bad.append(f"line {node.lineno}: {node.id}")
        if _is_front_matter_call(node) and id(node) not in allowed_ids:
            bad.append(f"line {node.lineno}: front_matter(...) used outside field()")
    return bad


def test_reads_go_through_field() -> None:
    problems = []
    for module in sorted(SRC.glob("*.py")):
        if module.name == "okf.py":
            continue
        tree = ast.parse(module.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "kmctl.okf":
                problems += [
                    f"{module.name}:{node.lineno} imports {a.name} as {a.asname}"
                    for a in node.names
                    if a.name in {"front_matter", "field"} and a.asname
                ]
        problems += [f"{module.name} {b}" for b in _bad_reads(tree)]
        for node in ast.walk(tree):
            if _is_field_call(node) and len(node.args) > 1:
                key = node.args[1]
                assert isinstance(key, ast.Constant), (
                    f"{module.name}:{node.lineno} field key is not a literal"
                )
                if key.value not in ALLOWED_FIELDS:
                    problems.append(f"{module.name}:{node.lineno} reads {key.value!r}")

    assert problems == []


def test_reads_scan_catches_a_direct_get() -> None:
    tree = ast.parse(
        "meta = front_matter(p)\nx = meta.get('title')\ny = field(meta, 'title')\n"
    )

    assert _bad_reads(tree) == ["line 2: meta"]


def test_reads_scan_catches_attribute_calls() -> None:
    tree = ast.parse("meta = okf.front_matter(p)\nx = meta['title']\n")

    assert _bad_reads(tree) == ["line 2: meta"]


def test_field_forms() -> None:
    one = {"verified": {"by": "human:j", "at": "2026-01-01T00:00:00Z"}}
    many = {
        "verified": [{"at": "2026-01-01T00:00:00Z"}, {"at": "2026-02-01T00:00:00Z"}]
    }
    sources = {"sources": ["src/a.py", {"id": "s", "resource": "src/b.py"}]}

    assert field(one, "verified[].at") == ["2026-01-01T00:00:00Z"]
    assert field(many, "verified[].at") == [
        "2026-01-01T00:00:00Z",
        "2026-02-01T00:00:00Z",
    ]
    assert field(sources, "sources[].resource") == ["src/a.py", "src/b.py"]
    assert field({"sources": "src/a.py"}, "sources[].resource") == []
    assert field({"sources": {"resource": "src/a.py"}}, "sources[].resource") == []
    assert field({"generated": {"at": "x"}}, "generated.at") == "x"
    assert field({}, "title", "fallback") == "fallback"
    with pytest.raises(KeyError):
        field({}, "decision_status")


def test_manifesto_marks_i4_enforced() -> None:
    manifesto = (ROOT / ".okf" / "manifesto.md").read_text()
    i4 = manifesto[manifesto.index("- **I4.") :].split("\n- **", 1)[0]

    assert "enforced" in i4 and "tests/test_okf_fields.py" in i4
    assert re.search(r"I4.*enforced", (ROOT / ".okf" / "log.md").read_text())
    check = okf_validate(ROOT / ".okf")
    assert check.returncode == 0, check.stdout + check.stderr
