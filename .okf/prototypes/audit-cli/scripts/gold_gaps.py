"""Count the saved gold results that lack a verdict for some sentence: the answers the CLI now counts as failed.

Run from the audit-cli folder: uv run python scripts/gold_gaps.py
"""

import json
import pathlib as plb

from audit_cli.claims.models import ChunkResult
from audit_cli.processing.chunker import BundleChunker, SentenceSplitter

HERE = plb.Path(__file__).resolve().parent.parent


def main() -> None:
    """Print, per prompt folder and run, the gold sections whose saved answer has a gap."""
    chunks = {c.extraction_key: c for c in BundleChunker(SentenceSplitter()).chunks(HERE.parents[2] / ".okf")}
    found = []
    for path in sorted((HERE / "results" / "gold").glob("*/*/*/*.json")):
        chunk = chunks.get(path.stem)
        if chunk is None:
            continue
        result = ChunkResult.model_validate_json(path.read_text())
        missing = sorted(set(range(1, len(chunk.sentences) + 1)) - {v.n for v in result.verdicts})
        if missing:
            found.append(
                {
                    "file": str(path.relative_to(HERE)),
                    "chunk": chunk.id,
                    "missing": len(missing),
                    "of": len(chunk.sentences),
                }
            )
    print(json.dumps(found, indent=1))
    print(f"{len(found)} saved answers with a gap")


if __name__ == "__main__":
    main()
