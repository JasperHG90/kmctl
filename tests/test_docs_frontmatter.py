"""Generated docs/ folder indexes, optional front matter on docs pages, and the kmctl-check hook."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner, Result

from kmctl import app
from kmctl.checks import run_checks
from kmctl.docs import GENERATED

ROOT = Path(__file__).resolve().parents[1]


def _write(root: Path, rel: str, text: str) -> None:
    """Write ``text`` to ``root / rel``, making its folders."""
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _check(root: Path, *args: str) -> Result:
    """Run ``kmctl check`` on ``root``."""
    return CliRunner().invoke(app, ["check", "--path", str(root), *args])


def _findings(root: Path, level: str) -> list[dict]:
    """The findings at ``level`` that ``kmctl check --json`` reports for ``root``."""
    return [f for f in json.loads(_check(root, "--json").stdout) if f["level"] == level]


def _docs(root: Path) -> None:
    """A docs/ with two how-to pages, one with a description, and a root index linking the folder."""
    _write(root, "docs/README.md", "# Docs\n\n- [How-to guides](how-to/README.md)\n")
    _write(
        root,
        "docs/how-to/install.md",
        '---\ndescription: "Install it."\n---\n\n# Install it\n',
    )
    _write(root, "docs/how-to/upgrade.md", "# Upgrade it\n")


def _snapshot(root: Path) -> dict[str, str]:
    """Every file under ``root`` and its text."""
    return {
        p.relative_to(root).as_posix(): p.read_text()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_check_fix_writes_folder_index(tmp_path: Path) -> None:
    _docs(tmp_path)
    _write(tmp_path, ".okf/index.md", '---\nokf_version: "0.2"\n---\n')
    before = _snapshot(tmp_path)

    result = _check(tmp_path, "--fix")

    assert result.exit_code == 0, result.output
    index = (tmp_path / "docs/how-to/README.md").read_text()
    assert index.splitlines()[0] == GENERATED
    assert "- [Install it](install.md): Install it.\n" in index
    assert "- [Upgrade it](upgrade.md)\n" in index
    after = _snapshot(tmp_path)
    assert {k: v for k, v in after.items() if k != "docs/how-to/README.md"} == before


def test_check_fix_second_run_changes_nothing(tmp_path: Path) -> None:
    _docs(tmp_path)
    _check(tmp_path, "--fix")
    before = _snapshot(tmp_path)

    result = _check(tmp_path, "--fix")

    assert result.exit_code == 0, result.output
    assert _snapshot(tmp_path) == before
    assert "fixed" not in result.output


def test_stale_folder_index_missing_readme(tmp_path: Path) -> None:
    _docs(tmp_path)

    result = _check(tmp_path)
    errors = _findings(tmp_path, "error")

    assert result.exit_code == 1
    assert len(errors) == 1, errors
    assert errors[0]["file"] == "docs/how-to"
    assert "kmctl check --fix" in errors[0]["message"]


def test_stale_folder_index_out_of_date(tmp_path: Path) -> None:
    _docs(tmp_path)
    _check(tmp_path, "--fix")
    _write(tmp_path, "docs/how-to/remove.md", "# Remove it\n")

    result = _check(tmp_path)
    errors = _findings(tmp_path, "error")

    assert result.exit_code == 1
    assert len(errors) == 1, errors
    assert errors[0]["file"] == "docs/how-to/README.md"
    assert "kmctl check --fix" in errors[0]["message"]


def test_stale_folder_index_page_outside_folders_must_be_in_root(
    tmp_path: Path,
) -> None:
    _docs(tmp_path)
    _check(tmp_path, "--fix")
    _write(tmp_path, "docs/faq.md", "# FAQ\n")
    _write(tmp_path, "docs/guides/extra.md", "# Extra\n")

    errors = _findings(tmp_path, "error")

    assert {e["file"] for e in errors} == {"docs/faq.md", "docs/guides/extra.md"}


def test_root_missing_folder_link_warns(tmp_path: Path) -> None:
    _docs(tmp_path)
    _write(tmp_path, "docs/README.md", "# Docs\n")
    _check(tmp_path, "--fix")

    result = _check(tmp_path)
    warnings = _findings(tmp_path, "warning")

    assert result.exit_code == 0, result.output
    assert _findings(tmp_path, "error") == []
    assert len(warnings) == 1, warnings
    assert warnings[0]["file"] == "docs/README.md"
    assert "how-to" in warnings[0]["message"]
    assert "warning" in result.output


def test_hand_written_folder_index_is_left_alone(tmp_path: Path) -> None:
    _docs(tmp_path)
    hand = "# My how-tos\n\n- [Install](install.md)\n- [Upgrade](upgrade.md)\n"
    _write(tmp_path, "docs/how-to/README.md", hand)

    fixed = _check(tmp_path, "--fix")
    CliRunner().invoke(
        app, ["new", "doc", "how-to", "Remove it", "--path", str(tmp_path)]
    )
    CliRunner().invoke(app, ["update", "--path", str(tmp_path)])

    assert (tmp_path / "docs/how-to/README.md").read_text() == hand
    (tmp_path / "docs/how-to/remove-it.md").unlink()
    result = _check(tmp_path)
    warnings = _findings(tmp_path, "warning")
    assert fixed.exit_code == 0, fixed.output
    assert result.exit_code == 0, result.output
    assert [w["file"] for w in warnings] == ["docs/how-to/README.md"]
    assert "does not manage" in warnings[0]["message"]


def test_new_doc_front_matter(tmp_path: Path) -> None:
    CliRunner().invoke(app, ["init", "--path", str(tmp_path)])

    result = CliRunner().invoke(
        app,
        [
            "new",
            "doc",
            "how-to",
            "Install it",
            "--description",
            "Install kmctl.",
            "--path",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    text = (tmp_path / "docs/how-to/install-it.md").read_text()
    meta = yaml.safe_load(text.split("---\n")[1])
    assert meta["description"] == "Install kmctl."
    assert meta["sources"] == []
    assert "verified" not in meta
    from datetime import UTC, datetime

    from kmctl.concepts import stale_after_time

    expected = stale_after_time("3m", datetime.now(UTC)).date()
    assert meta["stale_after"] == expected
    index = (tmp_path / "docs/how-to/README.md").read_text()
    assert "- [Install it](install-it.md): Install kmctl.\n" in index
    root = (tmp_path / "docs/README.md").read_text()
    assert "how-to/README.md" in root
    assert "install-it.md" not in root
    assert _check(tmp_path).exit_code == 0
    assert _findings(tmp_path, "warning") == []


def test_update_folder_indexes(tmp_path: Path) -> None:
    root_index = "# Docs\n\n- [Install](how-to/install.md)\n"
    _write(tmp_path, "docs/README.md", root_index)
    _write(tmp_path, "docs/how-to/install.md", "# Install\n")
    _write(tmp_path, "docs/reference/commands.md", "# Commands\n")

    result = CliRunner().invoke(app, ["update", "--path", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    created = json.loads(result.stdout)["created"]
    assert "docs/how-to/README.md" in created
    assert "docs/reference/README.md" in created
    assert (tmp_path / "docs/README.md").read_text() == root_index
    assert _findings(tmp_path, "error") == []
    assert {w["file"] for w in _findings(tmp_path, "warning")} == {"docs/README.md"}


@pytest.mark.parametrize(
    ("front", "field"),
    [
        ("description: [a, b]\n", "description"),
        ("stale_after: soon\n", "stale_after"),
        ("verified: yesterday\n", "verified"),
        ("verified:\n  - {by: 'human:j', at: never}\n", "verified"),
        ("sources: src/app.py\n", "sources"),
        ("sources:\n  - {id: x}\n", "sources"),
    ],
)
def test_field_shape_is_checked(tmp_path: Path, front: str, field: str) -> None:
    _docs(tmp_path)
    _write(tmp_path, "docs/how-to/upgrade.md", f"---\n{front}---\n\n# Upgrade it\n")
    _check(tmp_path, "--fix")

    errors = _findings(tmp_path, "error")

    assert len(errors) == 1, errors
    assert errors[0]["file"] == "docs/how-to/upgrade.md"
    assert field in errors[0]["message"]


def test_field_shape_good_and_absent_pass(tmp_path: Path) -> None:
    _docs(tmp_path)
    _write(
        tmp_path,
        "docs/how-to/upgrade.md",
        "---\ndescription: Up.\nstale_after: 2027-01-17\n"
        "verified:\n  - {by: 'human:j', at: 2026-10-01}\n"
        "sources:\n  - src/app.py\n  - resource: src\n---\n\n# Upgrade it\n",
    )
    _write(tmp_path, "docs/how-to/plain.md", "# Plain\n")
    _check(tmp_path, "--fix")

    assert _findings(tmp_path, "error") == []


def test_this_repo_docs_are_migrated() -> None:
    findings = run_checks(ROOT)
    bad = [f for f in findings if f.level in ("error", "warning")]
    assert bad == []
    docs = ROOT / "docs"
    assert not (docs / "log.md").exists()
    root_text = (docs / "README.md").read_text()
    for folder in ("tutorials", "how-to", "reference", "explanation"):
        index = docs / folder / "README.md"
        assert index.read_text().splitlines()[0] == GENERATED
        assert f"{folder}/README.md" in root_text
    for page in docs.rglob("*.md"):
        if page.name == "README.md":
            continue
        text = page.read_text()
        assert text.startswith("---\n"), page
        meta = yaml.safe_load(text.split("---\n")[1])
        assert isinstance(meta.get("description"), str) and meta["description"], page
        assert "type" not in meta and "okf_version" not in meta, page


def test_docs_pages_follow() -> None:
    decisions = sorted((ROOT / ".okf/decisions").glob("*docs*front-matter*.md"))
    assert decisions, "no decision records docs front matter"
    adr = decisions[-1].read_text()
    assert "0006" in adr
    assert "kmctl check --fix" in adr
    assert "kmctl-check" in adr
    manifesto = (ROOT / ".okf/manifesto.md").read_text()
    i4 = manifesto.split("**I4.", 1)[1].split("- **", 1)[0]
    assert "docs/" in i4
    assert "kmctl check --fix" in manifesto
    for rel in (
        ".claude/rules/docs-layout.md",
        "docs/reference/commands.md",
    ):
        text = (ROOT / rel).read_text()
        assert "kmctl check --fix" in text, rel
        assert "stale_after" in text, rel
        assert "each page listed in docs/README.md" not in text, rel
    commands = (ROOT / "docs/reference/commands.md").read_text()
    assert "warning" in commands
    from kmctl.briefing import ROUTING

    assert "--fix" in ROUTING
    assert "each page listed in docs/README.md" not in ROUTING


def test_pre_commit_hook_shape() -> None:
    hooks = yaml.safe_load((ROOT / ".pre-commit-hooks.yaml").read_text())
    hook = next(h for h in hooks if h["id"] == "kmctl-check")
    assert hook["entry"] == "kmctl check"
    assert hook["language"] == "python"
    assert hook["pass_filenames"] is False


def _git(cwd: Path, *args: str) -> str:
    env = os.environ | {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
    }
    return subprocess.run(
        ["git", *args], cwd=cwd, env=env, check=True, capture_output=True, text=True
    ).stdout.strip()


def _prek(repo: Path, home: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uvx", "prek", "run", "kmctl-check", "--all-files"],
        cwd=repo,
        env=os.environ | {"PREK_HOME": str(home)},
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.integration
def test_pre_commit_hook_runs_from_another_repo(tmp_path: Path) -> None:
    source = tmp_path / "kmctl"
    shutil.copytree(
        ROOT,
        source,
        ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", "*.pyc"),
    )
    _git(source, "init", "-q", "-b", "main")
    _git(source, "add", "-A")
    _git(source, "commit", "-q", "-m", "snapshot")
    rev = _git(source, "rev-parse", "HEAD")
    repo = tmp_path / "consumer"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _docs(repo)

    def config(args: str) -> None:
        _write(
            repo,
            ".pre-commit-config.yaml",
            f"repos:\n  - repo: {source}\n    rev: {rev}\n"
            f"    hooks:\n      - id: kmctl-check\n{args}",
        )
        _git(repo, "add", "-A")

    home = tmp_path / "prek-home"
    config("")
    failed = _prek(repo, home)
    config("        args: [--fix]\n")
    fixed = _prek(repo, home)
    _git(repo, "add", "-A")
    again = _prek(repo, home)

    assert failed.returncode != 0, failed.stdout + failed.stderr
    assert (repo / "docs/how-to/README.md").is_file(), fixed.stdout + fixed.stderr
    assert again.returncode == 0, again.stdout + again.stderr


def test_own_pre_commit_runs_kmctl_check() -> None:
    config = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text())
    hooks = [h for repo in config["repos"] for h in repo["hooks"]]
    hook = next(h for h in hooks if h["id"] == "kmctl-check")
    assert "kmctl check" in hook["entry"]


AGENT_INSTRUCTIONS = (
    "apm/claude/.apm/instructions/docs-layout.instructions.md",
    "apm/antigravity/.apm/instructions/docs-layout.instructions.md",
    "apm/.apm/skills/write-docs/SKILL.md",
    "apm/.apm/agents/kmctl-auditor.md",
    "apm/.apm/skills/audit/SKILL.md",
)


@pytest.mark.parametrize("rel", AGENT_INSTRUCTIONS)
def test_agent_instructions_name_front_matter_and_fix(rel: str) -> None:
    text = (ROOT / rel).read_text()
    assert "kmctl check --fix" in text, rel
    assert "stale_after" in text, rel
    assert "each page listed in docs/README.md" not in text, rel


def test_agent_instructions_init_block() -> None:
    from kmctl.scaffold import BLOCK

    assert "kmctl check --fix" in BLOCK
    assert "stale_after" in BLOCK
    assert "each page listed in `docs/README.md`" not in BLOCK
