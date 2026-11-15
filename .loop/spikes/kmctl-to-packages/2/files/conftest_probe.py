"""pytest plugin: after collection, check every test module saw its own tree's helpers.

Load with ``-p conftest_probe`` (this folder on PYTHONPATH). For each collected
module it finds every function defined in a module named ``conftest``,
``fixtures.*`` or ``test_*`` and checks that module's file lives in the same
rootless tests tree as the test file. Prints counts per tree and mismatches.
"""

from __future__ import annotations

import inspect
from collections import Counter
from pathlib import Path


def _tree(path: Path, root: Path) -> str:
    rel = path.resolve().relative_to(root)
    parts = rel.parts
    if parts[:2] == ("packages", "kmctl"):
        return "packages/kmctl/tests"
    if parts[:2] == ("packages", "kmaudit"):
        return "packages/kmaudit/tests"
    return parts[0]


def pytest_collection_finish(session) -> None:
    root = Path(session.config.rootpath).resolve()
    per_tree = Counter(_tree(Path(item.path), root) for item in session.items)
    checked, bad = 0, []
    modules = {item.module for item in session.items if getattr(item, "module", None)}
    for module in modules:
        tree = _tree(Path(module.__file__), root)
        for name, obj in vars(module).items():
            if not inspect.isfunction(obj):
                continue
            owner = obj.__module__
            if owner == module.__name__:
                continue  # defined here (possibly wrapped by a decorator)
            if not (owner == "conftest" or owner.startswith("fixtures") or owner.startswith("test_")):
                continue
            source = Path(obj.__code__.co_filename)
            checked += 1
            if _tree(source, root) != tree:
                bad.append(f"{module.__name__}.{name} from {source.relative_to(root)}")
    print(f"\nprobe: selected per tree {dict(sorted(per_tree.items()))}")
    print(f"probe: helper imports checked {checked}, from the wrong tree {len(bad)}")
    for line in bad[:20]:
        print(f"probe: WRONG {line}")
