"""The ``uv tool install`` line kmaudit's messages give for reinstalling it.

kmaudit installs from its folder of the kmctl repository. A release names
the tag it was built from, ``kmaudit-vX.Y.Z``, so following the hint gets
the same release back; a dev or local build has no tag, so its hint names
none and installs from the default branch.
"""

from __future__ import annotations

import re
from importlib.metadata import PackageNotFoundError, version

SOURCE = "git+https://github.com/JasperHG90/kmctl"
SUBDIRECTORY = "#subdirectory=packages/kmaudit"
#: A version the release workflow tags: X.Y.Z, or with an a, b or rc number.
_RELEASE = re.compile(r"^\d+\.\d+\.\d+(?:(?:a|b|rc)\d+)?$")


def install_hint(kmaudit_version: str, extras: str = "") -> str:
    """The command that installs kmaudit at ``kmaudit_version``, with ``extras``.

    Parameters
    ----------
    kmaudit_version :
        The version to install. A release or pre-release names its
        ``kmaudit-v`` tag; a dev, local or unreadable version names no ref.
    extras :
        Extras to install with it, comma-separated, such as ``tracing``.

    Returns
    -------
    str
        The full ``uv tool install --force`` command.
    """
    ref = f"@kmaudit-v{kmaudit_version}" if _RELEASE.match(kmaudit_version) else ""
    name = f"kmaudit[{extras}]" if extras else "kmaudit"
    return f"uv tool install --force '{name} @ {SOURCE}{ref}{SUBDIRECTORY}'"


def installed_hint(extras: str = "") -> str:
    """The install hint for the kmaudit that is running, with ``extras``."""
    try:
        return install_hint(version("kmaudit"), extras)
    except PackageNotFoundError:
        return install_hint("", extras)
