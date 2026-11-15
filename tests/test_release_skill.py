"""The repo-local release skill stays true to the workflows it drives.

`.claude/skills/release/SKILL.md` walks a release of kmctl or kmaudit through
`release.yml` and `release-tag.yml`. These tests fail when it names an input
the workflow lacks, offers a package the workflow does not release, cites a
file that is gone, or tells the reader to regenerate published notes. The
rule tests check that `.claude/rules/releases.md` points at the skill and
keeps its two constraints.
"""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude" / "skills" / "release" / "SKILL.md"
RULE = ROOT / ".claude" / "rules" / "releases.md"
RELEASE_YML = ROOT / ".github" / "workflows" / "release.yml"

PLACEHOLDER = re.compile(r"<[a-z_-]+>")


def _front_matter(text: str) -> dict:
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, "SKILL.md has no front matter"
    return yaml.safe_load(match.group(1))


def _release_inputs() -> dict:
    workflow = yaml.safe_load(RELEASE_YML.read_text())
    # PyYAML reads the bare key `on` as True.
    return workflow[True]["workflow_dispatch"]["inputs"]


def _section(text: str, heading: str) -> str:
    """The body under the `## ` heading that starts with `heading`, up to the next one."""
    match = re.search(
        rf"^## {re.escape(heading)}.*?$(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
    )
    assert match, f"no '## {heading}' section"
    return match.group(1)


def _unknown_inputs(text: str) -> list[str]:
    """Every `-f KEY=` whose KEY is not a release.yml input."""
    inputs = _release_inputs()
    return [k for k in re.findall(r"-f (\w+)=", text) if k not in inputs]


def _missing_paths(text: str) -> list[str]:
    """Backticked repo paths that do not resolve.

    A path with a `<tag>` or `<package>` placeholder matches when the folder
    before the placeholder exists, or when release.yml creates it.
    """
    roots = {p.name for p in ROOT.iterdir()}
    release_yml = RELEASE_YML.read_text()
    missing = []
    for token in re.findall(r"`([^`\s]+)`", text):
        if "/" not in token or token.split("/", 1)[0] not in roots:
            continue
        if not PLACEHOLDER.search(token):
            if not (ROOT / token).exists():
                missing.append(token)
            continue
        folder = PLACEHOLDER.split(token, maxsplit=1)[0].rsplit("/", 1)[0]
        created = f"mkdir -p {folder}" in release_yml
        if not ((ROOT / folder).is_dir() or created):
            missing.append(token)
    return missing


def _regenerates(text: str) -> list[str]:
    """Sentences that mention regenerating notes without forbidding it."""
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
    return [
        s
        for s in sentences
        if re.search(r"regenerat", s, re.IGNORECASE)
        and not re.search(
            r"\b(never|not|don't|do not)\s+(?:\w+\s+)?regenerat", s, re.IGNORECASE
        )
    ]


def _rule_constraint(name: str) -> str:
    match = re.search(
        rf'<constraint name="{name}">(.*?)</constraint>', RULE.read_text(), re.DOTALL
    )
    assert match, f"releases.md has no {name} constraint"
    return " ".join(match.group(1).split())


def test_skill_is_named_release() -> None:
    meta = _front_matter(SKILL.read_text())

    assert meta["name"] == "release"
    assert meta["description"].strip()


def test_skill_inputs_are_release_inputs() -> None:
    text = SKILL.read_text()

    assert re.findall(r"-f (\w+)=", text), "the skill passes no -f inputs"
    assert not _unknown_inputs(text)
    assert {"package", "dry_run"} <= set(re.findall(r"-f (\w+)=", text))


def test_skill_flags_a_made_up_input() -> None:
    assert _unknown_inputs("gh workflow run release.yml -f channel=beta") == ["channel"]


def test_skill_packages_match_the_package_input() -> None:
    text = SKILL.read_text()
    hint = _front_matter(text)["argument-hint"]
    offered = set(hint.strip("<>").split("|"))
    named = {v for v in re.findall(r"-f package=(\S+)", text) if v[0] != "<"}

    assert offered == set(_release_inputs()["package"]["options"])
    assert named <= offered
    for package in offered:
        assert f"/release {package}" in text


def test_skill_cites_paths_that_exist() -> None:
    assert not _missing_paths(SKILL.read_text())


def test_skill_flags_a_missing_path() -> None:
    text = "See `scripts/no_such_script.py` and `packages/nowhere/<tag>.md`."

    assert _missing_paths(text) == [
        "scripts/no_such_script.py",
        "packages/nowhere/<tag>.md",
    ]


def test_skill_accepts_the_notes_folder_release_yml_creates() -> None:
    assert not _missing_paths("`.github/release-notes/<tag>.md`")


def test_skill_explains_why_two_workflows() -> None:
    why = _section(SKILL.read_text(), "Why two workflows")

    for needed in (
        "`.github/workflows/release.yml`",
        "`.github/workflows/release-tag.yml`",
        "version pull request",
        "after",
        "tags the merge commit",
        "missing or blank",
    ):
        assert needed in why, needed


def test_skill_explains_apm_yml_is_the_kmctl_version_source() -> None:
    why = _section(SKILL.read_text(), "Why two workflows")

    for needed in (
        "`packages/kmctl/apm/apm.yml`",
        "ref: v<cli version>",
        "`vX.Y.Z`",
        "`packages/kmaudit/apm/apm.yml`",
        "`kmaudit-vX.Y.Z`",
    ):
        assert needed in why, needed
    for gone in ("`apm/apm.yml`", "`packages/kmaudit/VERSION`"):
        assert gone not in why, gone


def test_skill_watches_the_release_tag_run_after_the_merge() -> None:
    after = _section(SKILL.read_text(), "4.")

    assert "gh run list --workflow release-tag.yml" in after
    assert "gh run watch" in after
    assert "gh run view" in after
    assert "::warning::" in after
    assert "step summary" in after
    assert "gh release view" in after


def test_skill_gap_step_edits_release_and_file_and_never_regenerates() -> None:
    gap = _section(SKILL.read_text(), "5.")

    assert "gh release edit <tag> --notes-file" in gap
    assert "`.github/release-notes/<tag>.md`" in gap
    assert "`scripts/release_notes.py`" in gap
    assert "by hand" in gap
    assert not _regenerates(gap)
    assert re.search(r"Never regenerate published notes", gap)


def test_skill_gap_check_flags_regenerating() -> None:
    assert _regenerates("Fix the script. Then regenerate the notes and set them.")
    assert not _regenerates("Never regenerate published notes from the script.")
    assert _regenerates("If the notes are not complete, regenerate them.")


def test_rule_points_at_the_skill() -> None:
    assert ".claude/skills/release/" in RULE.read_text()


def test_rule_keeps_no_admin_merge() -> None:
    text = _rule_constraint("no-admin-merge")

    assert "--admin" in text
    assert "closed and reopened" in text


def test_rule_every_release_has_notes_fixed_by_hand() -> None:
    text = _rule_constraint("every-release-has-notes")

    assert "pull request" in text
    assert "gh release view" in text
    assert "gh release edit TAG --notes-file" in text
    assert "`.github/release-notes/<tag>.md`" in text
    assert "`scripts/release_notes.py`" in text
    assert "by hand" in text
    assert not _regenerates(text)
    assert "never regenerated" in text
