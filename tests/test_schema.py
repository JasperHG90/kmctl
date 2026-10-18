"""kmctl schema prints the shape of each document kind, built from the table the writers use."""

import ast
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from typer.testing import CliRunner, Result

from kmctl import app
from kmctl.okf import ALLOWED_FIELDS, front_matter

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "kmctl"

KINDS = (
    "decision",
    "practice",
    "proposal",
    "prototype",
    "handoff",
    "manifesto",
    "summary",
    "index",
    "section-index",
    "log",
    "architecture",
    "tutorial",
    "how-to",
    "reference",
    "explanation",
    "docs-index",
    "docs-folder-index",
)
NO_FRONT_MATTER = (
    "section-index",
    "log",
    "docs-index",
    "docs-folder-index",
)
DOC_PAGES = ("tutorial", "how-to", "reference", "explanation")


def _invoke(*args: str) -> Result:
    return CliRunner().invoke(app, list(args))


def _schema(kind: str) -> dict[str, Any]:
    result = _invoke("schema", kind)
    assert result.exit_code == 0, result.output
    return json.loads(result.stdout)


def _json_ready(value: Any) -> Any:
    """``value`` as JSON would carry it: PyYAML's date and datetime objects as ISO strings."""
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_ready(v) for v in value]
    return value


def _sections(path: Path) -> list[str]:
    """The ``##`` headings of ``path``'s body, in order, outside code fences."""
    found, fenced = [], False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and line.startswith("## "):
            found.append(line[3:].strip())
    return found


def _check(path: Path, kind: str) -> None:
    """Assert ``path`` matches ``kind``'s schema: its front matter and its ## sections."""
    schema = _schema(kind)
    errors = [
        e.message
        for e in Draft202012Validator(schema).iter_errors(
            _json_ready(front_matter(path))
        )
    ]
    assert not errors, (path, errors)
    sections, body = _sections(path), schema["x-kmctl-sections"]
    if isinstance(body, list):
        then = schema.get("x-kmctl-then", {}).get("pattern")
        assert sections[: len(body)] == body, (path, sections, body)
        rest = sections[len(body) :]
        assert not rest or (then and all(re.fullmatch(then, s) for s in rest)), (
            path,
            rest,
        )
    elif body is None:
        pass
    elif "pattern" in body:
        assert sections, path
        assert all(re.fullmatch(body["pattern"], s) for s in sections), (
            path,
            sections,
        )
    else:
        assert sections and sections[-1] == body["last"], (path, sections)


def _property_paths(schema: dict[str, Any], prefix: str = "") -> list[tuple[str, Any]]:
    """Each property in ``schema`` as (path in ALLOWED_FIELDS form, its schema)."""
    found = []
    for alt in [schema, *schema.get("anyOf", [])]:
        for name, sub in alt.get("properties", {}).items():
            path = f"{prefix}{name}"
            found.append((path, sub))
            found += _property_paths(sub, f"{path}.")
        if "items" in alt:
            found += _property_paths(alt["items"], f"{prefix.rstrip('.')}[].")
    return found


def test_schema_lists_every_kind() -> None:
    result = _invoke("schema")

    assert result.exit_code == 0, result.output
    listed = {line.split()[0]: line for line in result.stdout.splitlines() if line}
    assert set(listed) == set(KINDS)
    assert all(len(line.split()) > 2 for line in listed.values())
    as_json = json.loads(_invoke("schema", "--json").stdout)
    assert set(as_json) == set(KINDS) and all(as_json.values())


def test_schema_lists_kinds_when_refusing_an_unknown_one() -> None:
    result = _invoke("schema", "nonsense")

    assert result.exit_code == 1
    assert "nonsense" in result.stderr
    assert all(kind in result.stderr for kind in KINDS)
    assert result.stdout == ""


@pytest.mark.parametrize("kind", KINDS)
def test_schema_is_valid(kind: str) -> None:
    schema = _schema(kind)

    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema.get("description")
    for path, sub in _property_paths(schema):
        single = re.sub(r"^(\w+)\.", r"\1[].", path)  # verified may be one mapping
        assert path in ALLOWED_FIELDS or single in ALLOWED_FIELDS, path
        assert sub.get("description"), path
    body = schema["x-kmctl-sections"]
    assert (
        body is None
        or (isinstance(body, list) and all(isinstance(s, str) for s in body))
        or set(body) in ({"pattern"}, {"last"})
    ), body
    then = schema.get("x-kmctl-then")
    assert then is None or (isinstance(body, list) and set(then) == {"pattern"}), then


@pytest.mark.parametrize("kind", DOC_PAGES)
def test_doc_page_front_matter_is_optional(kind: str) -> None:
    schema = _schema(kind)

    assert set(schema["properties"]) == {
        "description",
        "stale_after",
        "verified",
        "sources",
    }
    assert schema["required"] == []


@pytest.mark.parametrize("kind", NO_FRONT_MATTER)
def test_schema_is_valid_with_no_front_matter(kind: str) -> None:
    validator = Draft202012Validator(_schema(kind))

    assert validator.is_valid({})
    assert not validator.is_valid({"title": "x"})


def test_schema_is_valid_root_index_only_okf_version() -> None:
    validator = Draft202012Validator(_schema("index"))

    assert validator.is_valid({"okf_version": "0.2"})
    assert not validator.is_valid({})
    assert not validator.is_valid({"okf_version": "0.2", "title": "x"})


def test_schema_matches_what_kmctl_writes(tmp_path: Path) -> None:
    assert _invoke("init", "--path", str(tmp_path)).exit_code == 0
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("")
    written: dict[str, str] = {
        "docs/README.md": "docs-index",
        ".okf/index.md": "index",
        ".okf/log.md": "log",
        ".okf/manifesto.md": "manifesto",
        ".okf/summary.md": "summary",
        ".okf/decisions/index.md": "section-index",
    }
    (first,) = (tmp_path / ".okf" / "decisions").glob("0001-*.md")
    written[first.relative_to(tmp_path).as_posix()] = "decision"
    for kind, folder in (
        ("decision", "decisions"),
        ("practice", "practices"),
        ("proposal", "proposals"),
        ("prototype", "prototypes"),
        ("handoff", "handoffs"),
    ):
        args = ["new", kind, f"A {kind}", "--description", "One sentence."]
        args += ["--stale-after", "30d", "--path", str(tmp_path)]
        if kind != "handoff":
            args += ["--source", "src/app.py"]
        result = _invoke(*args)
        assert result.exit_code == 0, result.output
        written[result.stdout.split()[1]] = kind
        written[f".okf/{folder}/index.md"] = "section-index"
    for doc_type in ("tutorial", "how-to", "reference", "explanation"):
        result = _invoke("new", "doc", doc_type, "A page", "--path", str(tmp_path))
        assert result.exit_code == 0, result.output
        written[result.stdout.split()[1]] = doc_type
        written[str(Path(result.stdout.split()[1]).parent / "README.md")] = (
            "docs-folder-index"
        )

    for rel, kind in written.items():
        _check(tmp_path / rel, kind)


def test_schema_matches_what_kmctl_writes_on_supersede(tmp_path: Path) -> None:
    assert _invoke("init", "--path", str(tmp_path)).exit_code == 0
    new = _invoke(
        "new", "decision", "Later", "--description", "One.", "--path", str(tmp_path)
    )
    assert new.exit_code == 0, new.output
    decisions = tmp_path / ".okf" / "decisions"
    (first,) = decisions.glob("0001-*.md")
    (second,) = decisions.glob("0002-*.md")
    result = _invoke("decision", "supersede", "1", "--by", "2", "--path", str(tmp_path))
    assert result.exit_code == 0, result.output
    assert "## Correction, " in first.read_text(encoding="utf-8")

    _check(first, "decision")
    _check(second, "decision")


def test_schema_matches_what_kmctl_writes_on_a_stray_section(tmp_path: Path) -> None:
    path = tmp_path / "0001-x.md"
    path.write_text(
        "---\ntype: decision\ntitle: X\ndescription: X.\ntags: []\nstatus: stable\n"
        "generated:\n  by: human:x\n  at: 2026-10-16\n---\n\n## Context\n\n"
        "## Decision\n\n## Consequences\n\n## Notes\n"
    )

    with pytest.raises(AssertionError):
        _check(path, "decision")


def test_schema_matches_what_kmctl_writes_on_this_architecture_page() -> None:
    _check(ROOT / ".okf" / "architecture" / "overview.md", "architecture")


def test_schema_is_documented() -> None:
    help_text = " ".join(_invoke("schema", "--help").stdout.split())

    assert "built from kmctl's own table" in help_text
    assert "what kmctl writes" in help_text
    assert "kmctl check" not in help_text
    assert "validator" not in help_text
    assert "kmctl schema" in " ".join(
        _invoke("briefing", "--path", str(ROOT)).stdout.split()
    )


def _constants(path: Path) -> list[ast.AST]:
    return list(ast.walk(ast.parse(path.read_text(encoding="utf-8"))))


def test_schema_tables_have_one_definition() -> None:
    from kmctl import kinds

    skeletons = [
        k.sections for k in kinds.KINDS.values() if isinstance(k.sections, list)
    ]
    statuses = set(kinds.STATUS_VALUES)
    words = {"Depicts", "architecture", *statuses}
    assert statuses == {"draft", "stable", "deprecated"}
    for path in SRC.glob("*.py"):
        if path.name == "kinds.py":
            continue
        nodes = _constants(path)
        prose = {id(n.value) for n in nodes if isinstance(n, ast.Expr)}  # docstrings
        for node in nodes:
            if id(node) in prose:
                continue
            if isinstance(node, ast.Assign | ast.AnnAssign):
                targets = (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
                names = [t.id for t in targets if isinstance(t, ast.Name)]
                assert "SKELETONS" not in names, path
            if isinstance(node, ast.List | ast.Tuple | ast.Set):
                values = [
                    e.value
                    for e in node.elts
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)
                ]
                assert values not in skeletons, (path, values)
                assert not statuses <= set(values), (path, values)
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert node.value not in words, (path, node.value)
                assert not re.search(
                    r"status: (draft|stable|deprecated)|## (Depicts|What this is for|Invariants|Values)\b",
                    node.value,
                ), (path, node.value)
    for name in ("concepts.py", "docs.py", "scaffold.py", "supersede.py"):
        imports = [
            n.module for n in _constants(SRC / name) if isinstance(n, ast.ImportFrom)
        ]
        assert "kmctl.kinds" in imports, name
