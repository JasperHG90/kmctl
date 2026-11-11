"""Read a repository's files, with the language Magika detects for each."""

import pathlib as plb
import subprocess
from collections.abc import Generator, Iterable
from fnmatch import fnmatch
from functools import cached_property

from magika import Magika
from pydantic import BaseModel, ConfigDict, Field


class FileMetadataModel(BaseModel):
    """What Magika says a file holds."""

    lang_name: str = Field(description="The content type's label, such as python or toml.")
    description: str = Field(description="A readable name for the content type.")
    is_text: bool = Field(description="Whether the file is text.")
    score: float = Field(description="Magika's confidence in the label, 0 to 1.")


class FileWithMedatadataModel(BaseModel):
    """One file's bytes, its path and what Magika says it holds."""

    model_config = ConfigDict(ignored_types=(cached_property,))

    content: bytes
    metadata: FileMetadataModel
    path: plb.Path

    @cached_property
    def content_str(self) -> str:
        """The content as text; bytes that are not UTF-8 become replacement characters."""
        return self.content.decode("utf-8", errors="replace")


class FileReader:
    """Read files and label each with Magika."""

    def __init__(self) -> None:
        self._language_predictor = Magika()

    @staticmethod
    def _read_bytes(file_path: plb.Path) -> bytes:
        """Return the file's bytes."""
        return file_path.read_bytes()

    def _get_file_metadata(self, content: bytes) -> FileMetadataModel:
        """Label the content with Magika."""
        metadata = self._language_predictor.identify_bytes(content)
        return FileMetadataModel(
            lang_name=metadata.output.label,
            description=metadata.output.description,
            is_text=metadata.output.is_text,
            score=metadata.score,
        )

    def read_file(self, file_path: plb.Path) -> FileWithMedatadataModel:
        """Read one file and label it."""
        content = self._read_bytes(file_path)
        metadata = self._get_file_metadata(content)
        return FileWithMedatadataModel(content=content, metadata=metadata, path=file_path)

    def read_files(self, file_paths: Iterable[plb.Path]) -> Generator[FileWithMedatadataModel, None, None]:
        """Read and label each file, one at a time."""
        for file_path in file_paths:
            yield self.read_file(file_path)


class SelectiveFileReader:
    """Read the files git does not ignore, minus skipped folders and name patterns, with the given extensions.

    Parameters
    ----------
    reader :
        Reads and labels each file.
    excluded_directories :
        Folder names to skip at any depth.
    included_extensions :
        Read only files with these suffixes, such as ``.py``.
    excluded_patterns :
        File-name globs to skip, such as ``*.pyc``.
    """

    def __init__(
        self,
        reader: FileReader,
        excluded_directories: list[str],
        included_extensions: list[str],
        excluded_patterns: list[str] | None = None,
    ) -> None:
        self._reader = reader
        self._excluded_directories = set(excluded_directories)
        self._included_extensions = set(included_extensions)
        self._excluded_patterns = list(excluded_patterns or [])

    def _create_git_cmd(self, path: plb.Path) -> list[str]:
        """Build the git command that lists tracked and untracked, not ignored, files outside skipped folders."""
        cmd = ["git", "-C", str(path), "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", "."]
        for directory in sorted(self._excluded_directories):
            cmd.append(f":(exclude,glob)**/{directory}/**")
        return cmd

    @staticmethod
    def _run_git_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
        """Run git and return its output.

        Raises
        ------
        subprocess.CalledProcessError
            If the folder is not inside a git repository.
        FileNotFoundError
            If git is not installed.
        """
        return subprocess.run(cmd, capture_output=True, text=True, check=True)

    @staticmethod
    def _parse_git_cmd_stdout(subprocess_result: subprocess.CompletedProcess[str]) -> list[str]:
        """Return git's NUL-separated output as paths, unquoted, so names with spaces or accents survive."""
        return [entry for entry in subprocess_result.stdout.split("\0") if entry]

    def _filter_file_paths(self, root_path: plb.Path, file_paths: list[str]) -> Generator[plb.Path, None, None]:
        """Yield the paths with an included extension that match no skipped pattern and still exist."""
        for line in file_paths:
            path = root_path / line
            if path.suffix not in self._included_extensions:
                continue
            if any(fnmatch(path.name, pattern) for pattern in self._excluded_patterns):
                continue
            if path.is_file():
                yield path

    def paths(self, path: plb.Path) -> list[plb.Path]:
        """Return the files the reader would read under ``path``, in git's order."""
        listed = self._parse_git_cmd_stdout(self._run_git_cmd(self._create_git_cmd(path=path)))
        return list(self._filter_file_paths(root_path=path, file_paths=listed))

    def read_files(self, path: plb.Path) -> Generator[FileWithMedatadataModel, None, None]:
        """Read and label every file under ``path`` that passes the filters."""
        return self._reader.read_files(self.paths(path))
