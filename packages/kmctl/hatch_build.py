"""Ship apm/'s skills, agents and rules in kmctl's wheel (ADR 0044).

They live in the repository's apm/, two levels up, in a checkout. An sdist
holds its own copy under apm/, so a wheel built from it reads that instead.
"""

from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict) -> None:
        # An editable install reads apm/ from the checkout (plugin.py's fallback).
        if version == "editable":
            return
        root = Path(self.root)
        base = root / ".." / ".." / "apm"
        if not base.is_dir():
            base = root / "apm"
        for source, target in self.config["apm-include"].items():
            build_data["force_include"][str((base / source).resolve())] = target
