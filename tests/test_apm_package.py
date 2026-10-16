"""kmctl's APM package, apm/apm.yml, and the docs for installing it (ADR 0013).

apm/apm.yml depends on this repository's plugin/ and a pinned okf-skills, so a
consumer installs kmctl's skills, agent and hook with one APM entry. The tests
without a marker read files only; the ``integration`` test installs the
package into a scratch consumer with APM 0.33.0, serving this tree from a
local git server and fetching okf-skills from GitHub.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator

from kmctl.kinds import schema, skeleton
from kmctl.okf import front_matter
from scripts.release import APM_DOC, APM_FILES, DOC_FILES, MANIFEST, set_version

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "apm" / "apm.yml"
PLUGIN = ROOT / "plugin"
DECISION = ROOT / ".okf" / "decisions" / "0013-kmctl-installs-through-apm-too.md"
MANIFESTO = ROOT / ".okf" / "manifesto.md"
PAGE = ROOT / APM_DOC
INSTALL_HOW_TO = ROOT / "docs" / "how-to" / "install-the-plugin-and-the-ci-action.md"
GITHTTP = Path(__file__).parent / "fixtures" / "githttp.py"
APM_CLI = "apm-cli==0.33.0"
OKF_PIN = re.compile(r"^scaccogatto/okf-skills#[0-9a-f]{40}$")
OKF_SKILLS = ("okf", "validate", "backfill", "visualize")
FENCE = re.compile(r"^```[^\n]*\n(.*?)^```", re.MULTILINE | re.DOTALL)


def _load(path: Path) -> dict[str, Any]:
    """The YAML mapping in ``path``."""
    return yaml.safe_load(path.read_text())


def _manifest_version() -> str:
    """The version in the plugin manifest, the one version source."""
    return str(json.loads((ROOT / MANIFEST).read_text())["version"])


def _dev_items() -> list[str]:
    """The names of the dev rules and skills the root apm.yml installs here."""
    names = []
    for entry in _load(ROOT / "apm.yml")["dependencies"]["apm"]:
        path = entry.partition("#")[0]
        names.append(path.rsplit("/", 1)[1].removesuffix(".instructions.md"))
    return names


# r1: the package --------------------------------------------------------------


def test_package_names_itself_and_has_a_version() -> None:
    """apm/apm.yml has a name and a version, both of which APM requires."""
    data = _load(PACKAGE)

    assert data["name"] == "kmctl"
    assert isinstance(data["version"], str) and data["version"]


def test_package_depends_on_the_plugin_and_a_pinned_okf() -> None:
    """The only dependencies are this repository's plugin/ and okf-skills at a full commit."""
    deps = _load(PACKAGE)["dependencies"]

    assert list(deps) == ["apm"]
    plugin, okf = deps["apm"]
    assert plugin == {"git": "parent", "path": "plugin"}
    assert OKF_PIN.match(okf), okf


def test_package_leaves_no_apm_yml_in_plugin() -> None:
    """plugin/ has no apm.yml: one there makes APM drop the agent."""
    assert list(PLUGIN.rglob("apm.yml")) == []
    assert (PLUGIN / ".claude-plugin" / "plugin.json").is_file()


# r2: the version copies -------------------------------------------------------


def test_apm_version_copies_equal_the_manifest() -> None:
    """Both apm.yml files carry the plugin manifest's version."""
    versions = {rel.as_posix(): str(_load(ROOT / rel)["version"]) for rel in APM_FILES}

    assert versions == dict.fromkeys(("apm.yml", "apm/apm.yml"), _manifest_version())


# r4: the decision, the manifesto and the docs ---------------------------------


def _json_ready(value: Any) -> Any:
    """``value`` as JSON carries it: PyYAML's dates and datetimes as ISO strings."""
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_ready(v) for v in value]
    return value


def _sections(text: str) -> dict[str, str]:
    """The ``##`` headings of ``text``, heading to body, in order."""
    found: dict[str, list[str]] = {}
    body: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            body = found.setdefault(line[3:].strip(), [])
            continue
        body.append(line)
    return {heading: "\n".join(lines) for heading, lines in found.items()}


def test_docs_decision_matches_the_decision_schema() -> None:
    """Decision 0013's front matter validates and its sections are the decision skeleton."""
    validator = Draft202012Validator(schema("decision"))

    errors = [
        e.message for e in validator.iter_errors(_json_ready(front_matter(DECISION)))
    ]

    assert errors == []
    assert list(_sections(DECISION.read_text())) == skeleton("decision")


def test_docs_decision_names_the_route_it_keeps_and_what_it_skips() -> None:
    """The record keeps kmctl plugin install and names ADR 0001's version check."""
    text = " ".join(DECISION.read_text().split())
    sections = _sections(DECISION.read_text())

    assert "kmctl plugin install" in sections["Decision"]
    assert "ADR 0001" in text
    assert "version check" in text
    assert "--trust-transitive-mcp" in sections["Consequences"]


def test_docs_manifesto_parts_name_apm() -> None:
    """The manifesto's Parts section names the APM route and its decision."""
    parts = _sections(MANIFESTO.read_text())["Parts"]

    assert "APM" in parts
    assert "ADR 0013" in parts


def test_docs_page_gives_the_project_install_after_the_cli() -> None:
    """The how-to installs the CLI first, then the package at project scope, with GitHub auth."""
    text = PAGE.read_text()
    commands = "\n".join(FENCE.findall(text))
    plain = " ".join(text.split())

    cli = commands.index(
        "uv tool install git+https://github.com/JasperHG90/Knowledge-management"
    )
    apm = commands.index("apm install JasperHG90/Knowledge-management/apm#v")
    assert cli < apm
    assert "- JasperHG90/Knowledge-management/apm#v" in commands
    assert re.search(r"apm install\s+(-g|--global)\b", commands) is None
    assert "GitHub token" in plain
    assert "private" in plain
    assert "kmctl plugin install" in plain
    assert "--trust-transitive-mcp" in plain


def test_docs_install_how_to_links_the_apm_page() -> None:
    """The plugin install how-to links to the APM how-to."""
    assert "(install-kmctl-with-apm.md)" in INSTALL_HOW_TO.read_text()


def test_docs_release_set_moves_the_page_pins(tmp_path: Path) -> None:
    """``scripts/release.py set`` points the page's package and CLI lines at the new tag."""
    for rel in (MANIFEST, *APM_FILES, APM_DOC, *DOC_FILES):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, tmp_path / rel)

    set_version(tmp_path, "9.8.7")

    text = (tmp_path / APM_DOC).read_text()
    pins = re.findall(r"JasperHG90/Knowledge-management/apm(#\S*)?", text)
    assert pins and set(pins) == {"#v9.8.7"}
    assert "Knowledge-management@v9.8.7\n" in text


# r3: a real consumer ----------------------------------------------------------


def _free_port() -> int:
    """A TCP port on 127.0.0.1 that nothing listens on now."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _git(*args: str, cwd: Path) -> None:
    """Run git in ``cwd``, failing the test with its stderr."""
    res = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    assert res.returncode == 0, res.stderr


@pytest.fixture
def served(tmp_path: Path) -> Iterator[str]:
    """This tree's files (not git-ignored ones) served as kmctl.git; yields its URL."""
    files = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout.split(b"\0")
    work = tmp_path / "kmctl"
    for name in filter(None, files):
        src = ROOT / os.fsdecode(name)
        if src.is_file():
            (work / os.fsdecode(name)).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, work / os.fsdecode(name))
    _git("init", "-q", "-b", "main", cwd=work)
    _git("add", "-A", cwd=work)
    _git(
        "-c",
        "user.email=t@e.invalid",
        "-c",
        "user.name=t",
        "commit",
        "-qm",
        "tree",
        cwd=work,
    )
    # APM wants an owner/repo path, as on GitHub.
    srv = tmp_path / "srv"
    bare = srv / "o" / "kmctl.git"
    bare.parent.mkdir(parents=True)
    _git("clone", "-q", "--bare", str(work), str(bare), cwd=tmp_path)
    _git("update-server-info", cwd=bare)
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-I", str(GITHTTP), str(srv), str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                break
            except OSError:
                time.sleep(0.1)
        yield f"http://127.0.0.1:{port}/o/kmctl.git"
    finally:
        proc.terminate()
        proc.wait()


def _uv_cache() -> str:
    """The uv cache dir of the real HOME, so the isolated HOME reuses downloads."""
    return subprocess.run(
        ["uv", "cache", "dir"], capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.mark.integration
def test_consumer_gets_the_plugin_and_okf_but_no_dev_items(
    tmp_path: Path, served: str
) -> None:
    """``apm install`` of the apm subfolder writes kmctl's plugin and okf, not the dev items."""
    home = tmp_path / "home"
    home.mkdir()
    consumer = tmp_path / "consumer"
    consumer.mkdir()
    _git("init", "-q", cwd=consumer)
    (consumer / "apm.yml").write_text(
        "name: consumer\nversion: 0.1.0\ntargets: [claude]\n"
        "dependencies:\n  apm:\n"
        f"    - git: {served}\n      path: apm\n      allow_insecure: true\n"
    )
    env = {
        **os.environ,
        "HOME": str(home),
        "UV_CACHE_DIR": os.environ.get("UV_CACHE_DIR") or _uv_cache(),
    }
    env.pop("VIRTUAL_ENV", None)

    res = subprocess.run(
        [
            *("uvx", "--python", sys.executable, "--from", APM_CLI),
            *("apm", "install", "--allow-insecure"),
        ],
        cwd=consumer,
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )

    assert res.returncode == 0, res.stdout + res.stderr
    claude = consumer / ".claude"
    for skill in sorted((PLUGIN / "skills").iterdir()):
        got = claude / "skills" / skill.name
        want_files = sorted(
            p.relative_to(skill) for p in skill.rglob("*") if p.is_file()
        )
        got_files = sorted(p.relative_to(got) for p in got.rglob("*") if p.is_file())
        assert got_files == want_files, skill.name
        for rel in want_files:
            assert (got / rel).read_bytes() == (skill / rel).read_bytes(), rel
    assert len(list((PLUGIN / "skills").iterdir())) == 7
    agent = claude / "agents" / "kmctl-auditor.md"
    assert agent.read_bytes() == (PLUGIN / "agents" / "kmctl-auditor.md").read_bytes()
    settings = json.loads((claude / "settings.json").read_text())
    commands = [
        hook["command"]
        for group in settings["hooks"]["SessionStart"]
        for hook in group["hooks"]
    ]
    assert any("kmctl briefing" in c for c in commands), commands
    assert any((claude / "skills" / s / "SKILL.md").is_file() for s in OKF_SKILLS)
    dev = set(_dev_items())
    assert len(dev) == 16
    written = [p.relative_to(consumer).parts for p in consumer.rglob("*")]
    assert [
        "/".join(parts)
        for parts in written
        if parts[0] not in {".git", "apm_modules"}
        and (set(parts[:-1]) & dev or parts[-1].split(".")[0] in dev)
    ] == []
    assert "jasperhg90/skills" not in (consumer / "apm.lock.yaml").read_text().lower()
