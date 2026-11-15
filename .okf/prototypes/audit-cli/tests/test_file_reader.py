"""Tests for choosing and reading a repository's files."""

import pathlib as plb

from audit_cli.io.file_reader import FileReader, SelectiveFileReader


def test_reads_what_git_keeps_minus_skipped_folders_and_patterns(repo: plb.Path) -> None:
    """Git-ignored files, skipped folders, skipped patterns and other extensions are all left out."""
    reader = SelectiveFileReader(
        FileReader(),
        excluded_directories=[".okf", "vendor"],
        included_extensions=[".py", ".pyc"],
        excluded_patterns=["*.pyc"],
    )
    paths = sorted(p.relative_to(repo).as_posix() for p in reader.paths(repo))
    assert paths == ["src/worker.py"]


def test_labels_each_file(repo: plb.Path) -> None:
    """Each file read carries Magika's label and its text."""
    reader = SelectiveFileReader(FileReader(), excluded_directories=[".okf", "vendor"], included_extensions=[".py"])
    (only,) = list(reader.read_files(repo))
    assert only.metadata.is_text
    assert "def retry" in only.content_str


def test_names_with_spaces_and_accents_are_read(repo: plb.Path) -> None:
    """git quotes such names unless asked for NUL-separated output; the reader still finds them."""
    (repo / "src" / "café module.py").write_text("z = 3\n")
    reader = SelectiveFileReader(FileReader(), excluded_directories=[".okf", "vendor"], included_extensions=[".py"])
    assert "src/café module.py" in {p.relative_to(repo).as_posix() for p in reader.paths(repo)}
