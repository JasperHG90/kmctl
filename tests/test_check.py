import json
from pathlib import Path

from typer.testing import CliRunner, Result

from kmctl import app
from kmctl.docs_index import folder_index

CONCEPT = (
    '---\ntype: note\ntitle: "{title}"\ndescription: "A note."\n---\n\n# {title}\n'
)


def _write(root: Path, rel: str, text: str) -> None:
    """Write ``text`` to ``root / rel``, making its folders."""
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _good_repo(root: Path) -> None:
    """A repository whose docs/ and .okf/ indexes all agree with their folders."""
    _write(
        root,
        "docs/README.md",
        "# Docs\n\n- [How-to guides](how-to/README.md): one task each.\n",
    )
    _write(root, "docs/how-to/install.md", "# Install\n")
    _write(root, "docs/how-to/README.md", folder_index(root / "docs/how-to"))
    _write(
        root,
        ".okf/index.md",
        '---\nokf_version: "0.2"\n---\n\n# Bundle\n\n'
        "- [Manifesto](manifesto.md): the design.\n"
        "- [Decisions](decisions/index.md): why.\n",
    )
    _write(root, ".okf/log.md", "# Log\n")
    _write(root, ".okf/manifesto.md", CONCEPT.format(title="Manifesto"))
    _write(
        root,
        ".okf/decisions/index.md",
        "# Decisions\n\n- [ADR 0001](0001-first.md): the first.\n",
    )
    _write(root, ".okf/decisions/0001-first.md", CONCEPT.format(title="ADR 0001"))


def _check(root: Path, *args: str) -> Result:
    """Run ``kmctl check`` on ``root``."""
    return CliRunner().invoke(app, ["check", "--path", str(root), *args])


def _findings(root: Path) -> list[dict]:
    """The error findings ``kmctl check --json`` reports for ``root``."""
    return [
        f for f in json.loads(_check(root, "--json").stdout) if f["level"] == "error"
    ]


def test_index_check_passes(tmp_path: Path) -> None:
    _good_repo(tmp_path)

    result = _check(tmp_path)

    assert result.exit_code == 0, result.output
    assert _findings(tmp_path) == []


def test_index_check_missing_entry(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    _write(tmp_path, "docs/upgrade.md", "# Upgrade\n")
    _write(tmp_path, ".okf/decisions/0002-second.md", CONCEPT.format(title="ADR 0002"))

    result = _check(tmp_path)
    files = {f["file"] for f in _findings(tmp_path) if f["check"] == "index"}

    assert result.exit_code != 0
    assert files == {"docs/upgrade.md", ".okf/decisions/0002-second.md"}


def test_index_check_entry_without_file(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    readme = tmp_path / "docs/README.md"
    readme.write_text(readme.read_text() + "- [Gone](gone.md): removed.\n")

    result = _check(tmp_path)
    [finding] = _findings(tmp_path)

    assert result.exit_code != 0
    assert finding["file"] == "docs/README.md"
    assert finding["line"] == 4
    assert finding["check"] == "index"


def test_index_check_unlinked_section(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    _write(
        tmp_path,
        ".okf/practices/index.md",
        "# Practices\n\n- [One](one.md): a lesson.\n",
    )
    _write(tmp_path, ".okf/practices/one.md", CONCEPT.format(title="One"))

    result = _check(tmp_path)
    files = [f["file"] for f in _findings(tmp_path)]

    assert result.exit_code != 0
    assert files == [".okf/practices"]


def test_index_check_skips_missing_docs(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    for path in sorted((tmp_path / "docs").rglob("*"), reverse=True):
        path.rmdir() if path.is_dir() else path.unlink()
    (tmp_path / "docs").rmdir()

    result = _check(tmp_path)

    assert result.exit_code == 0, result.output
    assert "skipped docs/" in result.stdout


def test_check_json_findings(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    _write(tmp_path, "docs/how-to/upgrade.md", "# Upgrade\n")

    data = json.loads(_check(tmp_path, "--json").stdout)

    assert isinstance(data, list)
    assert data
    for finding in data:
        assert {"check", "file", "line", "message"} <= finding.keys()


def test_check_prototype_readme_is_the_concept(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    _write(
        tmp_path,
        ".okf/index.md",
        (tmp_path / ".okf/index.md").read_text()
        + "- [Prototypes](prototypes/index.md): spikes.\n",
    )
    _write(
        tmp_path,
        ".okf/prototypes/index.md",
        "# Prototypes\n\n- [Speed](speed/README.md): a spike.\n",
    )
    _write(tmp_path, ".okf/prototypes/speed/README.md", CONCEPT.format(title="Speed"))
    _write(tmp_path, ".okf/prototypes/speed/notes.md", "raw notes\n")

    assert _findings(tmp_path) == []


def test_check_ignores_entries_in_code_fences(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    readme = (tmp_path / "docs/README.md").read_text()
    fence = "\n```markdown\n- [Example](example.md): shown.\n```\n"
    _write(tmp_path, "docs/README.md", readme + fence)

    assert _findings(tmp_path) == []


def test_check_ignores_links_that_leave_the_folder(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    decisions = (tmp_path / ".okf/decisions/index.md").read_text()
    outside = "- [Outside](../outside.md): elsewhere.\n"
    _write(tmp_path, ".okf/decisions/index.md", decisions + outside)

    assert [f for f in _findings(tmp_path) if f["check"] == "index"] == []


def test_check_skips_hidden_pages(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    _write(tmp_path, "docs/.drafts/wip.md", "# Draft\n")
    _write(tmp_path, ".okf/decisions/.scratch/note.md", "# Note\n")

    assert _findings(tmp_path) == []


def test_check_reports_non_utf8_index(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    (tmp_path / "docs/README.md").write_bytes(b"# Docs \xe9\n")

    result = _check(tmp_path)

    assert result.exit_code == 1
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert "not UTF-8" in result.stdout


def test_check_ignores_entries_in_nested_fences(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    readme = (tmp_path / "docs/README.md").read_text()
    nested = "\n````markdown\n```\n- [Example](example.md): shown.\n```\n````\n"
    _write(tmp_path, "docs/README.md", readme + nested)

    assert _findings(tmp_path) == []


def test_check_non_utf8_root_index_is_one_finding(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    (tmp_path / ".okf/index.md").write_bytes(b'---\nokf_version: "0.2"\n---\n\xe9\n')

    findings = _findings(tmp_path)

    assert [f["file"] for f in findings] == [".okf/index.md"]


def _with_prototypes(root: Path) -> None:
    """Add a linked prototypes section to the good repository."""
    index = (root / ".okf/index.md").read_text()
    _write(
        root, ".okf/index.md", index + "- [Prototypes](prototypes/index.md): spikes.\n"
    )
    _write(
        root,
        ".okf/prototypes/index.md",
        "# Prototypes\n\n- [Speed](speed/README.md): a spike.\n",
    )
    _write(root, ".okf/prototypes/speed/README.md", CONCEPT.format(title="Speed"))


def _prototype_findings(root: Path) -> list[dict]:
    return [f for f in _findings(root) if f["check"] == "prototype"]


def test_prototype_check_passes(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    _with_prototypes(tmp_path)

    result = _check(tmp_path)

    assert result.exit_code == 0, result.output
    assert _prototype_findings(tmp_path) == []


def test_prototype_check_ignores_nested_folders(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    _with_prototypes(tmp_path)
    _write(tmp_path, ".okf/prototypes/speed/results/run.json", "{}\n")
    _write(tmp_path, ".okf/prototypes/speed/src/count.py", "print(1)\n")

    assert _prototype_findings(tmp_path) == []


def test_prototype_check_fails_without_readme(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    _with_prototypes(tmp_path)
    _write(tmp_path, ".okf/prototypes/bare/count.py", "print(1)\n")

    result = _check(tmp_path)

    assert result.exit_code == 1
    assert [f["file"] for f in _prototype_findings(tmp_path)] == [
        ".okf/prototypes/bare"
    ]


def _link_findings(root: Path) -> list[tuple[str, int]]:
    return [(f["file"], f["line"]) for f in _findings(root) if f["check"] == "link"]


def test_link_check_docs_relative(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    page = "# Install\n\nSee [self](install.md) and [readme](../README.md).\n"
    _write(tmp_path, "docs/how-to/install.md", page + "Also [gone](missing.md).\n")

    assert _link_findings(tmp_path) == [("docs/how-to/install.md", 4)]


def test_link_check_docs_root_relative(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    _write(tmp_path, "src/app.py", "x = 1\n")
    page = "# Install\n\nCode: [app](/src/app.py).\nGone: [old](/src/old.py).\n"
    _write(tmp_path, "docs/how-to/install.md", page)

    assert _link_findings(tmp_path) == [("docs/how-to/install.md", 4)]


def test_link_check_okf_links_leaving_bundle(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    _write(tmp_path, "src/app.py", "x = 1\n")
    body = "\n[app](../../src/app.py)\n[gone](../../src/gone.py)\n"
    path = tmp_path / ".okf/decisions/0001-first.md"
    path.write_text(path.read_text() + body)

    findings = _link_findings(tmp_path)
    lines = path.read_text().splitlines()
    gone_line = lines.index("[gone](../../src/gone.py)") + 1

    assert findings == [(".okf/decisions/0001-first.md", gone_line)]


def test_link_check_okf_links_inside_bundle(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    path = tmp_path / ".okf/manifesto.md"
    path.write_text(
        path.read_text()
        + "\n[first](decisions/0001-first.md) and [root](/decisions/0001-first.md)\n"
        + "[gone](decisions/0099-nope.md) and [root gone](/nope.md)\n"
    )
    gone_line = len(path.read_text().splitlines())

    assert [
        (f["file"], f["line"], f["message"])
        for f in _findings(tmp_path)
        if f["check"] == "link"
    ] == [
        (
            ".okf/manifesto.md",
            gone_line,
            "link to decisions/0099-nope.md does not exist",
        ),
        (".okf/manifesto.md", gone_line, "link to /nope.md does not exist"),
    ]


def test_link_check_leaves_okf_index_entries_to_the_index_check(
    tmp_path: Path,
) -> None:
    _good_repo(tmp_path)
    _write(
        tmp_path,
        ".okf/decisions/index.md",
        "# Decisions\n\n- [ADR 0001](0001-first.md): the first.\n"
        "- [ADR 0099](0099-gone.md): see [gone](0098-gone.md).\n",
    )

    assert [(f["check"], f["file"], f["line"]) for f in _findings(tmp_path)] == [
        ("index", ".okf/decisions/index.md", 4),
        ("link", ".okf/decisions/index.md", 4),
    ]


def test_link_check_skips_urls_and_anchors(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    page = "# Install\n\n[web](https://example.com/x) [mail](mailto:a@b.c) [top](#install)\n"
    _write(
        tmp_path, "docs/how-to/install.md", page + "```\n[fenced](nowhere.md)\n```\n"
    )

    assert _link_findings(tmp_path) == []


def test_link_check_covers_other_links_on_index_lines(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    readme = "# Docs\n\n- [Install](how-to/install.md): see [gone](../GONE.md) and [old](/src/old.py).\n"
    _write(tmp_path, "docs/README.md", readme)

    assert _link_findings(tmp_path) == [("docs/README.md", 3), ("docs/README.md", 3)]


def test_link_forms_resolve(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    _write(tmp_path, "docs/how-to/my page.md", "# My page\n")
    readme = (
        "# Docs\n\n"
        "- [Install](how-to/install.md?plain=1): install it.\n"
        "- [Mine](<how-to/my page.md>): spaced.\n"
    )
    _write(tmp_path, "docs/README.md", readme)
    page = (
        "# Install\n\n"
        "[a](my%20page.md) [b](my%20page.md?plain=1) [c](<my page.md>) "
        "[d](my%20page.md 'a title') [e](my%20page.md \"a title\")\n"
    )
    _write(tmp_path, "docs/how-to/install.md", page)
    _write(tmp_path, "docs/how-to/README.md", folder_index(tmp_path / "docs/how-to"))

    assert _findings(tmp_path) == []


def test_reference_style_links(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    page = "# Install\n\nSee [the guide][g] and [gone][x].[^1]\n\n[g]: install.md\n[x]: missing.md\n[^1]: A footnote here.\n"
    _write(tmp_path, "docs/how-to/install.md", page)
    readme = (
        tmp_path / "docs/README.md"
    ).read_text() + "- [Ref entry][g]\n\n[g]: how-to/install.md\n"
    _write(tmp_path, "docs/README.md", readme)
    _write(tmp_path, "docs/other.md", "# Other\n")
    readme2 = (
        tmp_path / "docs/README.md"
    ).read_text() + "- [Other][o]\n\n[o]: other.md\n"
    _write(tmp_path, "docs/README.md", readme2)

    findings = _findings(tmp_path)

    assert [
        (f["check"], f["file"], f["line"]) for f in findings if f["check"] == "link"
    ] == [("link", "docs/how-to/install.md", 6)]
    assert ("index", "docs/other.md") in {(f["check"], f["file"]) for f in findings}


def test_angle_bracket_with_inner_brackets_is_not_a_link(tmp_path: Path) -> None:
    _good_repo(tmp_path)
    page = "# Install\n\n[x](<a>b.md>)\n\n[r]: <a>b.md>\n"
    _write(tmp_path, "docs/how-to/install.md", page)

    assert [f for f in _findings(tmp_path) if f["check"] == "link"] == []
