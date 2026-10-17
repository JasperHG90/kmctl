"""Does a kmctl verify hint on the briefing's state line keep it under TOKEN_BUDGET?

Exits 0 when the shortest hint fits every case with at least 10 tokens to spare.
"""
import sys
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from kmctl import app
from kmctl.briefing import TOKEN_BUDGET, build_briefing, estimate_tokens, render

HINTS = {
    "short": " Checked one? kmctl verify ID --by human:ID.",
    "medium": " Once a person checks one, kmctl verify ID --by human:ID clears it.",
    "long": (
        " Once a person has checked a due concept, run kmctl verify ID "
        "--by human:ID to record it and clear it from the list."
    ),
}
#: In-place rewrites of "(kmctl review due)" rather than an appended sentence.
SWAPS = {
    "swap-verify": "(kmctl review due; kmctl verify)",
    "swap-then": "(kmctl review due, then kmctl verify ID)",
}
MARGIN = 10


def inv(*a):
    r = CliRunner().invoke(app, list(a))
    assert r.exit_code == 0, r.output
    return r


def repo(root: Path, long_title: bool) -> Path:
    inv("init", "--path", str(root))
    for t in ("Earlier work", "Latest work"):
        inv("new", "handoff", t, "--description", f"Where {t} stands.", "--path", str(root))
    if long_title:
        inv("new", "handoff", " ".join(["ab"] * 40), "--description", "x.", "--path", str(root))
    return root


def with_hint(text: str, hint: str) -> str:
    lines = text.split("\n")
    i = next(n for n, l in enumerate(lines) if l.startswith("State: "))
    lines[i] += hint
    return "\n".join(lines)


ok = True
with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
    cases = {
        "kmctl repo": Path("/home/vscode/kmctl"),
        "test_briefing_token_budget": repo(Path(a), False),
        "test_..._long_handoff_title": repo(Path(b), True),
    }
    for name, root in cases.items():
        base = render(build_briefing(root))
        cli = inv("briefing", "--path", str(root)).stdout
        print(f"{name}: render {estimate_tokens(base)} tokens, CLI stdout {estimate_tokens(cli)} / {TOKEN_BUDGET}")
        print("   ", next(l for l in base.split("\n") if l.startswith("State: ")))
        for hname, hint in HINTS.items():
            n = estimate_tokens(with_hint(cli, hint))
            fits = n <= TOKEN_BUDGET - MARGIN
            print(f"  + {hname} ({len(hint)} chars): {n} tokens, spare {TOKEN_BUDGET - n}{'' if fits else '  <-- under margin'}")
            if hname == "short" and not fits:
                ok = False
        for sname, swap in SWAPS.items():
            n = estimate_tokens(cli.replace("(kmctl review due)", swap, 1))
            print(f"  ~ {sname} {swap!r}: {n} tokens, spare {TOKEN_BUDGET - n} (test needs < {TOKEN_BUDGET})")
sys.exit(0 if ok else 1)
