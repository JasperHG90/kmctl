"""Ship apm/'s skills, agents and rules in kmctl's wheel (ADR 0044, ADR 0045).

They live in packages/kmctl/apm, kmctl's APM package, beside this file, and
an sdist holds the same folders under its own apm/.
"""

from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """Copy each ``apm-include`` source under ``apm/`` to its wheel path."""

    def initialize(self, version: str, build_data: dict) -> None:
        """Add the ``apm-include`` folders to the wheel's force-include, except for an editable install.

        Parameters
        ----------
        version : str
            The build version hatchling asks for; ``editable`` for an editable install.
        build_data : dict
            The build data hatchling passes; its ``force_include`` gains one entry per folder.
        """
        # An editable install reads apm/ from the checkout (plugin.py's fallback).
        if version == "editable":
            return
        base = Path(self.root) / "apm"
        for source, target in self.config["apm-include"].items():
            build_data["force_include"][str((base / source).resolve())] = target
