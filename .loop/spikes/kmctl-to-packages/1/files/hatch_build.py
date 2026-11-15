"""Ship apm/ skills, agents and rules in the wheel, from ../../apm in the repo or apm/ in an sdist."""

from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict) -> None:
        if version == "editable":
            return
        root = Path(self.root)
        base = root / "../../apm"
        if not base.is_dir():
            base = root / "apm"
        for source, target in self.config["apm-include"].items():
            build_data["force_include"][str((base / source).resolve())] = target
