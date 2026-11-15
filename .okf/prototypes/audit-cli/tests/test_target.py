"""Tests for working out what a path names."""

import pathlib as plb

import pytest

from audit_cli.processing.target import TargetError, resolve_target


def test_a_repository_means_its_bundle(repo: plb.Path) -> None:
    """A folder holding .okf/ names that bundle, and the repository names the project."""
    target = resolve_target(repo)
    assert target.bundle == (repo / ".okf").resolve() and target.files is None
    assert target.project_root == repo.resolve()


def test_a_bundle_folder_means_itself(repo: plb.Path) -> None:
    """The bundle folder itself works too."""
    assert resolve_target(repo / ".okf").bundle == (repo / ".okf").resolve()


def test_a_concept_file_finds_its_bundle(repo: plb.Path) -> None:
    """A file names just itself, and its concept id is its path below the bundle root."""
    path = repo / ".okf" / "decisions" / "0001-use-a-queue.md"
    target = resolve_target(path)
    assert target.files == [path.resolve()] and target.concept(path) == "decisions/0001-use-a-queue"


@pytest.mark.parametrize("name", ["nowhere", "src/worker.py", "src"])
def test_other_paths_are_refused(repo: plb.Path, name: str) -> None:
    """A missing path, a file that is not markdown and a folder with no bundle are refused."""
    with pytest.raises(TargetError):
        resolve_target(repo / name)


def test_a_folder_finds_a_bundle_not_named_okf_and_a_folder_inside_it_narrows(tmp_path: plb.Path) -> None:
    """With the bundle in kb/, any folder of the repository finds it; a folder inside it narrows to its concepts."""
    import subprocess

    from audit_cli.processing.target import resolve_project

    root = tmp_path / "r"
    (root / "kb" / "decisions").mkdir(parents=True)
    (root / "src").mkdir()
    (root / "kb" / "index.md").write_text('---\nokf_version: "0.2"\n---\n\n# Index\n')
    (root / "kb" / "decisions" / "x.md").write_text("---\ntype: decision\n---\n\n# X\n\nText.\n")
    (root / "src" / "a.py").write_text("x = 1\n")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    whole = resolve_project(root / "src")
    assert (whole.bundle, whole.files) == ((root / "kb").resolve(), None)
    narrowed = resolve_project(root / "kb" / "decisions")
    assert narrowed.bundle == (root / "kb").resolve() and narrowed.files is not None
    assert [narrowed.concept(f) for f in narrowed.files] == ["decisions/x"]


def test_a_path_outside_any_repository_or_bundle_is_refused(tmp_path: plb.Path) -> None:
    """A folder with no bundle and no git repository names no claims."""
    import pytest

    from audit_cli.processing.target import TargetError, resolve_project

    (tmp_path / "loose").mkdir()
    with pytest.raises(TargetError, match="no git repository"):
        resolve_project(tmp_path / "loose")
