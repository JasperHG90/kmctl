"""Stand-ins for the uvx, claude and uv commands, so tests never run the real APM or claude.

``FakeTools`` writes small Python scripts into a ``bin`` folder. Each one logs
its arguments, its working folder and the apm.yml there at that moment, then
answers from the rules a test gave it: print this, exit with that, write
these files. A command no rule matches prints nothing and exits 0.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

_SCRIPT = """#!{python}
import json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
cwd = pathlib.Path.cwd()
manifest = cwd / "apm.yml"
with open({log!r}, "a") as log:
    log.write(json.dumps({{"tool": name, "args": args, "cwd": str(cwd),
        "apm_yml": manifest.read_text() if manifest.is_file() else None}}) + "\\n")
line = " ".join(args)
for rule in json.loads(pathlib.Path({rules!r}).read_text()).get(name, []):
    if rule["match"] in line:
        for rel, text in rule.get("write", {{}}).items():
            target = cwd / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        sys.stdout.write(rule.get("stdout", ""))
        sys.stderr.write(rule.get("stderr", ""))
        sys.exit(rule.get("exit", 0))
"""


@dataclass(frozen=True)
class Call:
    """One run of a fake tool.

    Attributes
    ----------
    tool : str
        The command name: uvx, claude or uv.
    args : list[str]
        Its arguments.
    cwd : str
        The folder it ran in.
    apm_yml : str | None
        The text of apm.yml in that folder when it ran, or None.
    """

    tool: str
    args: list[str]
    cwd: str
    apm_yml: str | None


class FakeTools:
    """A bin folder of fake tools and the log of their runs.

    Parameters
    ----------
    root :
        A scratch folder to hold the bin folder, the rules and the log.
    tools :
        The commands to fake; leave one out to have it missing from PATH.
    """

    def __init__(self, root: Path, tools: tuple[str, ...] = ("uvx", "claude")):
        self.bin = root / "fake-bin"
        self.bin.mkdir(parents=True, exist_ok=True)
        self._log = root / "fake-calls.jsonl"
        self._rules = root / "fake-rules.json"
        self._rules.write_text("{}")
        for tool in tools:
            self.add(tool)

    def add(self, tool: str) -> None:
        """Put a fake ``tool`` on the bin folder."""
        script = self.bin / tool
        script.write_text(
            _SCRIPT.format(
                python=sys.executable, log=str(self._log), rules=str(self._rules)
            )
        )
        script.chmod(0o755)

    def on(
        self,
        tool: str,
        match: str,
        *,
        stdout: str = "",
        stderr: str = "",
        exit: int = 0,
        write: dict[str, str] | None = None,
    ) -> None:
        """Answer a run of ``tool`` whose joined arguments contain ``match``; first rule wins."""
        rules = json.loads(self._rules.read_text())
        rules.setdefault(tool, []).append(
            {
                "match": match,
                "stdout": stdout,
                "stderr": stderr,
                "exit": exit,
                "write": write or {},
            }
        )
        self._rules.write_text(json.dumps(rules))

    def calls(self, tool: str | None = None) -> list[Call]:
        """The runs so far, oldest first, of ``tool`` or of every tool."""
        if not self._log.is_file():
            return []
        found = [
            Call(**json.loads(line)) for line in self._log.read_text().splitlines()
        ]
        return [c for c in found if tool is None or c.tool == tool]

    @property
    def path(self) -> str:
        """A PATH holding the fakes and the system folders, without the user's own tools."""
        return f"{self.bin}:/usr/bin:/bin"
