"""Work out what a path given to the CLI names: a whole OKF bundle, or one concept file in one."""

import pathlib as plb
import subprocess
from dataclasses import dataclass

import frontmatter


class TargetError(ValueError):
    """The path names no bundle and no concept file."""


@dataclass(frozen=True)
class Target:
    """What to extract.

    Attributes
    ----------
    bundle : pathlib.Path
        The bundle's root folder; concept ids are paths relative to it.
    files : list[pathlib.Path] | None
        The one concept file to extract, or None for the whole bundle.
    project_root : pathlib.Path
        The repository that holds the bundle (git's top level, else the bundle's parent); it names the database.
    """

    bundle: plb.Path
    files: list[plb.Path] | None
    project_root: plb.Path

    def concept(self, path: plb.Path) -> str:
        """Return the concept id of a file in the bundle: its path below the bundle root, without .md."""
        return path.resolve().relative_to(self.bundle).with_suffix("").as_posix()


def _is_bundle_root(folder: plb.Path) -> bool:
    """Whether the folder holds an index.md whose front matter carries okf_version."""
    index = folder / "index.md"
    if not index.is_file():
        return False
    try:
        return "okf_version" in frontmatter.loads(index.read_text()).metadata
    except (ValueError, UnicodeDecodeError):
        return False


def _bundle_of(file: plb.Path) -> plb.Path:
    """Return the bundle a concept file sits in: the nearest folder above it that is a bundle root.

    A folder named ``.okf`` counts too, so a bundle without okf_version is still found.
    """
    for folder in file.parents:
        if _is_bundle_root(folder) or folder.name == ".okf":
            return folder
    raise TargetError(f"{file} is not inside an OKF bundle (no folder above it has an index.md with okf_version)")


def _project_root(bundle: plb.Path) -> plb.Path:
    """Return git's top level for the bundle, or the bundle's parent outside a repository."""
    try:
        result = subprocess.run(
            ["git", "-C", str(bundle), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return bundle.parent
    return plb.Path(result.stdout.strip()).resolve()


def resolve_target(path: plb.Path) -> Target:
    """Return what ``path`` names: a concept file, a bundle folder, or a repository with a ``.okf`` bundle.

    Raises
    ------
    TargetError
        If the path does not exist, is not markdown, or is a folder that is neither a bundle nor holds ``.okf``.
    """
    path = path.resolve()
    if path.is_file():
        if path.suffix != ".md":
            raise TargetError(f"{path} is not a markdown concept file")
        bundle = _bundle_of(path).resolve()
        return Target(bundle=bundle, files=[path], project_root=_project_root(bundle))
    if path.is_dir():
        if (path / ".okf").is_dir():
            path = path / ".okf"
        elif not (_is_bundle_root(path) or path.name == ".okf"):
            raise TargetError(f"{path} is not an OKF bundle (no index.md with okf_version) and holds no .okf folder")
        return Target(bundle=path, files=None, project_root=_project_root(path))
    raise TargetError(f"{path} does not exist")


def _bundles(root: plb.Path) -> list[plb.Path]:
    """Return the repository's OKF bundles: folders whose tracked index.md carries okf_version, shallowest first."""
    try:
        listed = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--", "index.md", "*/index.md"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    folders = [(root / f).parent for f in listed.split("\0") if f]
    for depth in range(3):  # a bundle not committed yet: index.md files on disk, a few folders down
        folders += [i.parent for i in root.glob("/".join(["*"] * depth + ["index.md"])) if ".git" not in i.parts]
    found = list(dict.fromkeys(f.resolve() for f in folders if _is_bundle_root(f)))
    if (root / ".okf").is_dir() and (root / ".okf").resolve() not in found:
        found.append((root / ".okf").resolve())
    return sorted(found, key=lambda f: (len(f.relative_to(root.resolve()).parts), f.name != ".okf"))


def resolve_project(path: plb.Path) -> Target:
    """Return what ``path`` names for a stage that works on stored claims, which need no bundle at the path.

    A concept file or bundle narrows the scope as for extraction. A folder inside a bundle narrows it to the concepts
    under that folder. Any other folder or file inside a git repository means all of that repository's claims, with
    its bundle found by its index.md (the shallowest when there are several), so each concept's text can be read.

    Raises
    ------
    TargetError
        If the path does not exist, or is neither in an OKF bundle nor in a git repository.
    """
    try:
        return resolve_target(path)
    except TargetError:
        resolved = path.resolve()
        if not resolved.exists():
            raise
        folder = resolved if resolved.is_dir() else resolved.parent
        try:
            result = subprocess.run(
                ["git", "-C", str(folder), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as error:
            raise TargetError(
                f"{resolved} is in no git repository and no OKF bundle: give the repository whose claims to check"
            ) from error
        root = plb.Path(result.stdout.strip()).resolve()
        bundles = _bundles(root)
        inside = next((b for b in bundles if resolved == b or b in resolved.parents), None)
        if inside is not None and resolved.is_dir():
            return Target(bundle=inside, files=sorted(resolved.rglob("*.md")), project_root=root)
        bundle = bundles[0] if bundles else root
        return Target(bundle=bundle, files=None, project_root=root)
