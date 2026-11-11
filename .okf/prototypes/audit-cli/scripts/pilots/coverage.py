"""Count the claims the settle step found lines for, which a one-call check can be written from.

Run from the audit-cli folder: uv run python scripts/pilots/coverage.py
"""

import json
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pilots import common  # the scripts folder is not a package on the path

EMPTY = "(the settle step found nothing to show)"


def main() -> None:
    """Print how many claims, of all and of the graded 19, have lines to show, and their average size."""
    claims = common.claims()
    graded = set(common.graded_ids())
    shown = {c.claim_id: common.snippets(c) for c in claims}
    with_lines = [cid for cid, s in shown.items() if s != EMPTY]
    out = {
        "claims": len(claims),
        "with_lines": len(with_lines),
        "graded_with_lines": sum(cid in graded for cid in with_lines),
        "graded": len(graded),
        "mean_chars_shown": round(sum(len(shown[c]) for c in with_lines) / len(with_lines)),
    }
    (common.OUT / "coverage.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
