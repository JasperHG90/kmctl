"""Release notes from main's first-parent history, filled into ``.github/release-notes.md`` (ADR 0012).

Most work lands on main as ``Merge loop/SLUG: SUMMARY`` commits, not pull
requests, so ``scripts/release_notes.py`` reads those merges, the pull request
merges a sync with GitHub's main brings in, and the plain commits beside them
in place of GitHub's generated pull-request list.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "release_notes.py"
TEMPLATE = ROOT / ".github" / "release-notes.md"
GIT = ["git", "-c", "user.email=o@e.com", "-c", "user.name=O"]

# Subjects on main's first-parent line that never reach the notes.
NOISE = (
    "loop: register widget",
    "loop: land widget",
    "release: v0.2.0",
    "Merge remote-tracking branch 'origin/main'",
    "Merge main into loop/widget",
    "Merge branch 'main' into loop/widget",
    "operator: manual commit",
    "operator: manual commits",
    "chore; manual commits",
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run([*GIT, "-C", str(repo), *args], check=True, capture_output=True)


def _commit(repo: Path, subject: str) -> None:
    _git(repo, "commit", "-q", "--allow-empty", "-m", subject)


def _merge(repo: Path, branch: str, subject: str, inside: str) -> None:
    """Merge a branch holding one commit, ``inside``, into main with ``subject``."""
    _git(repo, "switch", "-q", "-c", branch)
    _commit(repo, inside)
    _git(repo, "switch", "-q", "main")
    _git(repo, "merge", "-q", "--no-ff", "-m", subject, branch)


def _pull_request(repo: Path, base: str, number: int, title: str) -> None:
    """Merge a one-commit pull request into ``base`` as GitHub does, with its title in the body."""
    _git(repo, "switch", "-q", "-c", f"pr/{number}", base)
    _commit(repo, title)
    _git(repo, "switch", "-q", base)
    subject = f"Merge pull request #{number} from JasperHG90/pr/{number}"
    _git(repo, "merge", "-q", "--no-ff", "-m", f"{subject}\n\n{title}", f"pr/{number}")


def _sync(repo: Path, into: str, source: str) -> None:
    """Merge ``source`` into ``into`` as ``git pull`` does when both have moved on."""
    _git(repo, "switch", "-q", into)
    _commit(repo, "loop: stamp")
    _git(
        repo,
        "merge",
        "-q",
        "--no-ff",
        "-m",
        "Merge remote-tracking branch 'origin/main'",
        source,
    )


def _notes(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repo", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A repo with v0.1.0, then one ticket, one plain commit and noise up to v0.2.0, then more."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _commit(repo, "First change")
    _git(repo, "tag", "-a", "v0.1.0", "-m", "kmctl 0.1.0")
    _merge(
        repo,
        "loop/widget",
        "Merge loop/widget: kmctl adds a widget.",
        "Inside the widget branch",
    )
    _commit(repo, "Fix a typo in the README")
    for subject in NOISE:
        _commit(repo, subject)
    _merge(
        repo,
        "release/v0.2.0",
        "Merge pull request #2 from JasperHG90/release/v0.2.0",
        "release: v0.2.0",
    )
    _git(repo, "tag", "-a", "v0.2.0", "-m", "kmctl 0.2.0")
    _merge(repo, "loop/later", "Merge loop/later: kmctl does a later thing.", "Later")
    _commit(repo, "A commit after v0.2.0")
    _git(repo, "tag", "-a", "v0.3.0rc1", "-m", "kmctl 0.3.0rc1")
    return repo


def _section(text: str, heading: str) -> str:
    """The body of the ``## heading`` section of ``text``."""
    return text.split(f"## {heading}\n", 1)[1].split("\n## ", 1)[0]


def test_sections_hold_ticket_merges_and_plain_commits(repo: Path) -> None:
    """Ticket merges go under What changed, plain commits under Other changes, only from the range."""
    res = _notes(repo, "v0.2.0")

    assert res.returncode == 0, res.stderr
    changes = _section(res.stdout, "What changed")
    other = _section(res.stdout, "Other changes")
    assert changes.strip() == "- kmctl adds a widget. (`widget`)"
    assert other.strip() == "- Fix a typo in the README"
    for outside in ("First change", "later", "after v0.2.0", "Inside the widget"):
        assert outside not in res.stdout


def test_sections_say_none_when_empty(repo: Path) -> None:
    """A release with no plain commits says so rather than leaving the heading bare."""
    _git(repo, "tag", "-a", "v0.2.1", "-m", "kmctl 0.2.1", "v0.2.0")

    res = _notes(repo, "v0.2.1")

    assert res.returncode == 0, res.stderr
    assert _section(res.stdout, "What changed").strip() == "None."
    assert _section(res.stdout, "Other changes").strip() == "None."


@pytest.mark.parametrize("subject", NOISE)
def test_skips_loop_release_and_placeholder_commits(repo: Path, subject: str) -> None:
    """loop:, release:, release PR merges, branch syncs and manual placeholders never show."""
    res = _notes(repo, "v0.2.0")

    assert res.returncode == 0, res.stderr
    assert subject not in res.stdout
    assert "Merge pull request" not in res.stdout


def test_lists_pull_requests_a_sync_brings_in(repo: Path) -> None:
    """A pull request merged on GitHub and pulled into main is a What changed bullet with its title."""
    _git(repo, "branch", "github")
    _pull_request(repo, "github", 5, "Add a gadget")
    _pull_request(repo, "github", 6, "Fix the gadget")
    _sync(repo, "main", "github")
    _git(repo, "tag", "-a", "v0.3.0", "-m", "kmctl 0.3.0")

    res = _notes(repo, "v0.3.0")

    assert res.returncode == 0, res.stderr
    assert _section(res.stdout, "What changed").strip() == (
        "- Add a gadget (#5)\n- Fix the gadget (#6)"
    )


def test_lists_pull_requests_of_a_sync_inside_a_sync(repo: Path) -> None:
    """A sync that reached GitHub's main brings its own pull requests in too, in merge order."""
    _git(repo, "branch", "github")
    _git(repo, "branch", "elsewhere")
    _pull_request(repo, "github", 5, "Add a gadget")
    _pull_request(repo, "elsewhere", 7, "Add a gizmo")
    _sync(repo, "github", "elsewhere")
    _pull_request(repo, "github", 6, "Fix the gadget")
    _sync(repo, "main", "github")
    _git(repo, "tag", "-a", "v0.3.0", "-m", "kmctl 0.3.0")

    res = _notes(repo, "v0.3.0")

    assert res.returncode == 0, res.stderr
    assert _section(res.stdout, "What changed").strip() == (
        "- Add a gadget (#5)\n- Add a gizmo (#7)\n- Fix the gadget (#6)"
    )


def test_leaves_out_pull_requests_of_the_release_before(repo: Path) -> None:
    """A sync that brings in the previous release does not list that release's pull requests again."""
    _git(repo, "branch", "github")
    _pull_request(repo, "github", 5, "Add a gadget")
    _git(repo, "tag", "-a", "v0.3.0", "-m", "kmctl 0.3.0", "github")
    _sync(repo, "main", "github")
    _pull_request(repo, "main", 6, "Fix the gadget")
    _git(repo, "tag", "-a", "v0.4.0", "-m", "kmctl 0.4.0")

    res = _notes(repo, "v0.4.0")

    assert res.returncode == 0, res.stderr
    assert _section(res.stdout, "What changed").strip() == "- Fix the gadget (#6)"


def test_lists_a_pull_request_once_when_a_sync_inside_a_sync_holds_it(
    repo: Path,
) -> None:
    """A sync inside a sync that brings back a pull request main already has lists it once."""
    _git(repo, "branch", "elsewhere")
    _pull_request(repo, "main", 5, "Add a gadget")
    _sync(repo, "elsewhere", "main")
    _sync(repo, "main", "elsewhere")
    _git(repo, "tag", "-a", "v0.3.0", "-m", "kmctl 0.3.0")

    res = _notes(repo, "v0.3.0")

    assert res.returncode == 0, res.stderr
    assert _section(res.stdout, "What changed").strip() == "- Add a gadget (#5)"


def test_lists_a_pull_request_once_when_its_commit_is_also_on_main(repo: Path) -> None:
    """A commit made on main and also merged on GitHub as a pull request shows once, as the pull request."""
    _git(repo, "branch", "github")
    _commit(repo, "License kmctl under MIT")
    _git(repo, "switch", "-q", "github")
    _git(
        repo,
        "merge",
        "-q",
        "--no-ff",
        "-m",
        "Merge pull request #30 from JasperHG90/pr/mit-license\n\nLicense kmctl under MIT",
        "main",
    )
    _sync(repo, "main", "github")
    _git(repo, "tag", "-a", "v0.3.0", "-m", "kmctl 0.3.0")

    res = _notes(repo, "v0.3.0")

    assert res.returncode == 0, res.stderr
    assert (
        _section(res.stdout, "What changed").strip()
        == "- License kmctl under MIT (#30)"
    )
    assert _section(res.stdout, "Other changes").strip() == "None."


def test_template_fills_version_install_and_compare(repo: Path) -> None:
    """The notes follow the template: the install line pins the tag, the link compares the previous tag."""
    res = _notes(repo, "v0.3.0rc1")

    assert res.returncode == 0, res.stderr
    for line in TEMPLATE.read_text().splitlines():
        if line.startswith("#"):
            assert line in res.stdout
    assert (
        "uv tool install git+https://github.com/JasperHG90/kmctl@v0.3.0rc1"
        "#subdirectory=packages/kmctl\n" in res.stdout
    )
    assert "- uses: JasperHG90/kmctl@v0.3.0rc1" in res.stdout
    assert (
        "https://github.com/JasperHG90/kmctl/compare/v0.2.0...v0.3.0rc1" in res.stdout
    )
    assert "$" not in res.stdout


def test_template_install_subdirectory_is_packages_kmctl() -> None:
    """The release notes template installs the tag from packages/kmctl, where releases after v0.12.2 build (ADR 0044)."""
    text = TEMPLATE.read_text()

    assert (
        "uv tool install git+https://github.com/JasperHG90/kmctl@$tag"
        "#subdirectory=packages/kmctl\n" in text
    )


def test_first_release_has_no_compare_link(repo: Path) -> None:
    """The first tag has nothing to compare against, and lists the history up to it."""
    res = _notes(repo, "v0.1.0")

    assert res.returncode == 0, res.stderr
    assert "/compare/" not in res.stdout
    assert "First release." in res.stdout
    assert "- First change" in res.stdout


def test_unknown_tag_is_refused(repo: Path) -> None:
    """A tag that does not exist exits 1 and names the tag."""
    res = _notes(repo, "v9.9.9")

    assert res.returncode == 1
    assert "v9.9.9" in res.stderr
    assert res.stdout == ""


KMAUDIT_TEMPLATE = ROOT / ".github" / "release-notes-kmaudit.md"


def _change(repo: Path, subject: str, *paths: str) -> None:
    """Commit ``subject``, writing a new line into each of ``paths``."""
    for rel in paths:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as fh:
            fh.write(f"{subject}\n")
        _git(repo, "add", rel)
    _git(repo, "commit", "-q", "-m", subject)


@pytest.fixture
def split(tmp_path: Path) -> Path:
    """A repo with kmctl's and kmaudit's commits mixed, both families tagged, and noise.

    kmaudit-v0.1.0 and v0.1.0 tag the same commit; v0.2.0 tags a kmaudit-only
    commit after it, which kmaudit's next notes still list.
    """
    repo = tmp_path / "split"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _change(repo, "kmaudit begins", "packages/kmaudit/src.py")
    _change(repo, "Start", "README.md")
    _git(repo, "tag", "-a", "v0.1.0", "-m", "kmctl 0.1.0")
    _git(repo, "tag", "-a", "kmaudit-v0.1.0", "-m", "kmaudit 0.1.0")
    _change(repo, "kmaudit adds x", "packages/kmaudit/x.py")
    _git(repo, "tag", "-a", "v0.2.0", "-m", "kmctl 0.2.0")
    _change(repo, "kmaudit adds w", "packages/kmaudit/w.py")
    _change(repo, "kmctl adds y", "packages/kmctl/y.py")
    _change(repo, "Docs change", "docs/z.md")
    _git(repo, "switch", "-q", "-c", "loop/both")
    _change(repo, "Inside both", "packages/kmaudit/a.py", "scripts/b.py")
    _git(repo, "switch", "-q", "main")
    _git(
        repo, "merge", "-q", "--no-ff", "-m", "Merge loop/both: Both move.", "loop/both"
    )
    _change(repo, "loop: land both", ".loop/state.json")
    _change(repo, "release: kmaudit-v0.1.0", "packages/kmaudit/VERSION")
    _git(repo, "switch", "-q", "-c", "release/kmaudit-v0.1.1")
    _change(repo, "Bump kmaudit", "packages/kmaudit/VERSION")
    _git(repo, "switch", "-q", "main")
    _git(
        repo,
        "merge",
        "-q",
        "--no-ff",
        "-m",
        "Merge pull request #9 from JasperHG90/release/kmaudit-v0.1.1",
        "release/kmaudit-v0.1.1",
    )
    return repo


def _draft(repo: Path, tmp_path: Path, package: str, tag: str) -> str:
    """Draft ``package``'s notes for the unpushed ``tag`` at HEAD into a file and return it."""
    out = tmp_path / "out" / f"{tag}.md"
    res = _notes(repo, "--package", package, tag, "--ref", "HEAD", "--out", str(out))
    assert res.returncode == 0, res.stderr
    assert res.stdout == ""
    return out.read_text()


def test_package_kmaudit_drafts_its_own_commits_for_an_unpushed_tag(
    split: Path, tmp_path: Path
) -> None:
    """kmaudit's draft starts at kmaudit-v0.1.0, not v0.2.0, and lists only commits touching packages/kmaudit/."""
    text = _draft(split, tmp_path, "kmaudit", "kmaudit-v0.2.0")

    assert _section(text, "What changed").strip() == "- Both move. (`both`)"
    assert _section(text, "Other changes").strip() == (
        "- kmaudit adds x\n- kmaudit adds w"
    )
    for outside in ("kmctl adds y", "Docs change", "Start", "begins", "release"):
        assert outside not in text


def test_package_kmctl_drafts_its_own_commits_for_an_unpushed_tag(
    split: Path, tmp_path: Path
) -> None:
    """kmctl's draft starts at v0.2.0 and leaves out the commit touching only packages/kmaudit/."""
    text = _draft(split, tmp_path, "kmctl", "v0.3.0")

    assert _section(text, "What changed").strip() == "- Both move. (`both`)"
    assert _section(text, "Other changes").strip() == ("- kmctl adds y\n- Docs change")
    assert "kmaudit adds" not in text
    assert "https://github.com/JasperHG90/kmctl/compare/v0.2.0...v0.3.0" in text


def test_package_kmaudit_first_draft_walks_the_whole_history(
    split: Path, tmp_path: Path
) -> None:
    """With no kmaudit-v* tag, the draft lists every commit that touched packages/kmaudit/."""
    _git(split, "tag", "-d", "kmaudit-v0.1.0")

    text = _draft(split, tmp_path, "kmaudit", "kmaudit-v0.1.0")

    assert _section(text, "Other changes").strip() == (
        "- kmaudit begins\n- kmaudit adds x\n- kmaudit adds w"
    )
    assert "First release." in text
    assert "/compare/" not in text


def test_package_kmaudit_template_installs_from_its_subdirectory(
    split: Path, tmp_path: Path
) -> None:
    """kmaudit's notes follow its own template: the install line pins the tag and the subdirectory."""
    text = _draft(split, tmp_path, "kmaudit", "kmaudit-v0.2.0")

    for line in KMAUDIT_TEMPLATE.read_text().splitlines():
        if line.startswith("#"):
            assert line in text
    assert (
        "uv tool install 'kmaudit @ git+https://github.com/JasperHG90/kmctl"
        "@kmaudit-v0.2.0#subdirectory=packages/kmaudit'\n" in text
    )
    assert "uses: JasperHG90/kmctl" not in text
    assert (
        "https://github.com/JasperHG90/kmctl/compare/kmaudit-v0.1.0...kmaudit-v0.2.0"
        in text
    )
    assert "$" not in text


@pytest.mark.parametrize(
    ("package", "tag"), [("kmaudit", "v0.3.0"), ("kmctl", "kmaudit-v0.2.0")]
)
def test_package_refuses_the_other_family_s_tag(
    split: Path, package: str, tag: str
) -> None:
    """A tag from the other family is refused, naming the tag."""
    res = _notes(split, "--package", package, tag, "--ref", "HEAD")

    assert res.returncode == 1
    assert tag in res.stderr


def test_package_draft_prints_to_stdout_without_out(split: Path) -> None:
    """Without --out the draft goes to stdout, as a tagged release's notes do."""
    res = _notes(split, "--package", "kmaudit", "kmaudit-v0.2.0", "--ref", "HEAD")

    assert res.returncode == 0, res.stderr
    assert "- kmaudit adds w" in res.stdout


def test_a_bookkeeping_only_commit_is_in_neither_package_s_notes(
    split: Path, tmp_path: Path
) -> None:
    """A commit touching only .okf/ and uv.lock ships nothing; one with a shipped path counts for its owner."""
    _change(split, "Bundle and lock only", ".okf/summary.md", "uv.lock")
    _change(split, "Bundle and kmaudit", ".okf/log.md", "packages/kmaudit/q.py")
    _change(split, "Rule and docs", ".claude/rules/r.md", "docs/r.md")

    kmctl = _draft(split, tmp_path, "kmctl", "v0.3.0")
    kmaudit = _draft(split, tmp_path, "kmaudit", "kmaudit-v0.2.0")

    assert "Bundle and lock only" not in kmctl + kmaudit
    assert "Bundle and kmaudit" in kmaudit
    assert "Bundle and kmaudit" not in kmctl
    assert "Rule and docs" in kmctl
    assert "Rule and docs" not in kmaudit
