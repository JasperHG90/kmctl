"""The kmctl-read Hermes plugin: three read tools, confined to the repository root (I2)."""

import ast
import importlib.util
import json
import os
import time
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "action" / "hermes" / "kmctl-read"
TOOLS = {"kmctl_read_file", "kmctl_search_files", "kmctl_list_files"}


class _Ctx:
    """Records what the plugin registers, the way Hermes' PluginContext would."""

    def __init__(self) -> None:
        self.tools: dict[str, dict] = {}

    def register_tool(self, name: str, toolset: str, schema: dict, handler, **kw):
        self.tools[name] = {"toolset": toolset, "schema": schema, "handler": handler}


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "kmctl_read_plugin", PLUGIN / "__init__.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    """The registered handlers, with a repository root and an outside folder."""
    repo = tmp_path / "repo"
    (repo / "src" / "pkg").mkdir(parents=True)
    (repo / "src" / "pkg" / "greet.py").write_text("def greet():\n    return 'Hi'\n")
    (repo / "README.md").write_text("Hello world\nsecond line\n")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("KMKEY=bfkey-secret\n")
    (repo / "linkdir").symlink_to(outside)
    (repo / "linkfile.txt").symlink_to(outside / "secret.txt")
    monkeypatch.setenv("KMCTL_READ_ROOT", str(repo))
    monkeypatch.setenv("KMKEY", "bfkey-secret")
    ctx = _Ctx()
    _load().register(ctx)
    calls = {name: entry["handler"] for name, entry in ctx.tools.items()}
    return {"repo": repo, "outside": outside, **calls}


def _text(result: object) -> str:
    return result if isinstance(result, str) else json.dumps(result)


def test_registers_only_the_three_read_tools() -> None:
    ctx = _Ctx()
    _load().register(ctx)

    assert set(ctx.tools) == TOOLS
    assert {entry["toolset"] for entry in ctx.tools.values()} == {"kmctl_read"}
    for name, entry in ctx.tools.items():
        assert entry["schema"]["name"] == name
        assert entry["schema"]["parameters"]["type"] == "object"
    manifest = (PLUGIN / "plugin.yaml").read_text()
    assert "name: kmctl-read" in manifest


def test_every_result_is_text(tools: dict) -> None:
    # Hermes 0.19.0 sends a str to the model and rejects a dict (spike r8).
    calls = [
        ("kmctl_read_file", {"path": "README.md"}),
        ("kmctl_read_file", {"path": "/proc/self/environ"}),
        ("kmctl_read_file", {"path": "nope.txt"}),
        ("kmctl_search_files", {"pattern": ""}),
        ("kmctl_search_files", {"pattern": "Hello"}),
        ("kmctl_list_files", {"path": "/etc"}),
        ("kmctl_list_files", {}),
    ]
    for name, args in calls:
        assert isinstance(tools[name](args), str), (name, args)


def test_plugin_starts_no_program() -> None:
    tree = ast.parse((PLUGIN / "__init__.py").read_text())
    banned = {"subprocess", "pty", "shlex", "pexpect", "multiprocessing"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not {a.name.split(".")[0] for a in node.names} & banned
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "os"
        ):
            assert node.attr not in {"system", "popen", "fork", "forkpty"}
            assert not node.attr.startswith(("exec", "spawn"))


def test_reads_inside_the_root(tools: dict) -> None:
    out = _text(tools["kmctl_read_file"]({"path": "README.md"}))
    absolute = _text(
        tools["kmctl_read_file"]({"path": str(tools["repo"] / "src/pkg/greet.py")})
    )

    assert "1|Hello world" in out and "2|second line" in out
    assert "2|    return 'Hi'" in absolute


def test_read_says_when_cut(tools: dict) -> None:
    big = tools["repo"] / "big.txt"
    big.write_bytes(b"x" * 100 + b"\n" + (b"y" * 1000 + b"\n") * 400)
    out = _text(tools["kmctl_read_file"]({"path": "big.txt"}))
    binary = tools["repo"] / "blob.bin"
    binary.write_bytes(bytes(range(256)) * 4)

    assert "cut" in out and "offset=" in out
    assert len(out) < 300_000
    assert "error" not in _text(tools["kmctl_read_file"]({"path": "blob.bin"}))


def test_lists_files_by_name_inside_the_root(tools: dict) -> None:
    every = _text(tools["kmctl_list_files"]({"path": "."}))
    named = _text(tools["kmctl_list_files"]({"path": "src", "contains": "greet"}))
    by_ext = _text(tools["kmctl_list_files"]({"contains": ".py"}))

    assert "src/pkg/greet.py" in every and "README.md" in every
    assert "src/pkg/greet.py" in named and "README.md" not in named
    assert "src/pkg/greet.py" in by_ext


def test_search_finds_plain_text(tools: dict) -> None:
    out = _text(tools["kmctl_search_files"]({"pattern": "Hi'"}))
    folded = _text(
        tools["kmctl_search_files"]({"pattern": "HELLO", "ignore_case": True})
    )

    assert "src/pkg/greet.py:2:" in out
    assert "README.md:1:" in folded
    assert "README.md" not in _text(tools["kmctl_search_files"]({"pattern": "HELLO"}))


def test_search_and_read_agree_on_line_numbers(tools: dict) -> None:
    (tools["repo"] / "odd.txt").write_bytes(b"a\x0cb\nc\rd\ntarget\n")
    found = _text(tools["kmctl_search_files"]({"pattern": "target"}))
    read = _text(tools["kmctl_read_file"]({"path": "odd.txt"}))

    assert "odd.txt:3:" in found, "form feeds and lone CRs do not start a line"
    assert "3|target" in read


def test_every_tool_refuses_paths_outside_the_root(tools: dict, tmp_path: Path) -> None:
    outside = tools["outside"]
    home = tmp_path / "home"
    (home / ".hermes").mkdir(parents=True)
    (home / ".hermes" / "config.yaml").write_text("api_key: bfkey-secret\n")
    paths = [
        str(outside / "secret.txt"),
        str(outside),
        "../outside/secret.txt",
        "linkdir/secret.txt",
        "linkdir",
        "linkfile.txt",
        str(home / ".hermes" / "config.yaml"),
        str(home),
        "/proc/self/environ",
        f"/proc/{os.getpid()}/environ",
        "/proc/self",
        "/etc",
    ]
    for path in paths:
        results = [
            tools["kmctl_read_file"]({"path": path}),
            tools["kmctl_search_files"]({"pattern": "KMKEY=bfkey", "path": path}),
            tools["kmctl_search_files"]({"pattern": "=", "path": path}),
            tools["kmctl_list_files"]({"path": path}),
        ]
        for result in results:
            text = _text(result)
            assert "bfkey" not in text, (path, text)
            assert "outside the repository" in text, (path, text)


def test_walk_skips_symlinks_out_of_the_root(tools: dict) -> None:
    search = _text(tools["kmctl_search_files"]({"pattern": "KMKEY"}))
    listing = _text(tools["kmctl_list_files"]({"path": "."}))

    assert "bfkey" not in search and "linkfile" not in search
    assert "linkdir" not in listing and "linkfile" not in listing


def test_pattern_is_only_text(tools: dict) -> None:
    repo = tools["repo"]
    before = sorted(p.name for p in repo.rglob("*"))
    (repo / "dashes.txt").write_text("run --pre=rm here\n")
    for pattern in ("--pre=rm", "-L", "--follow", "-e", "--pre=/bin/sh"):
        tools["kmctl_search_files"]({"pattern": pattern, "path": "."})
    out = _text(tools["kmctl_search_files"]({"pattern": "--pre=rm"}))

    assert sorted(p.name for p in repo.rglob("*")) == sorted([*before, "dashes.txt"])
    assert "dashes.txt:1:" in out


def test_regex_shaped_pattern_returns_at_once(tools: dict) -> None:
    (tools["repo"] / "aaa.txt").write_text("a" * 40 + "b\n")
    start = time.monotonic()
    out = _text(tools["kmctl_search_files"]({"pattern": "(a+)+$"}))

    assert time.monotonic() - start < 1
    assert "aaa.txt" not in out
    (tools["repo"] / "lit.txt").write_text("x (a+)+$ y\n")
    assert "lit.txt:1:" in _text(tools["kmctl_search_files"]({"pattern": "(a+)+$"}))


def test_results_say_when_capped(tools: dict) -> None:
    many = tools["repo"] / "many"
    many.mkdir()
    for i in range(600):
        (many / f"f{i:03}.txt").write_text("needle\n")
    search = _text(tools["kmctl_search_files"]({"pattern": "needle"}))
    listing = _text(tools["kmctl_list_files"]({"path": "many"}))

    assert "stopped after" in search
    assert "stopped after" in listing


def test_no_root_refuses_everything(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KMCTL_READ_ROOT", raising=False)
    ctx = _Ctx()
    _load().register(ctx)

    for name, entry in ctx.tools.items():
        args = {"path": ".", "pattern": "x"}
        assert "KMCTL_READ_ROOT" in _text(entry["handler"](args)), name
