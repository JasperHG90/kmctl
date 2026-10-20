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
        in res.stdout
    )
    assert "- uses: JasperHG90/kmctl@v0.3.0rc1" in res.stdout
    assert (
        "https://github.com/JasperHG90/kmctl/compare/v0.2.0...v0.3.0rc1" in res.stdout
    )
    assert "$" not in res.stdout


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
