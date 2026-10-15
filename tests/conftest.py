import subprocess
import sys
from pathlib import Path

VALIDATOR = Path(__file__).parent / "vendor" / "okf" / "okf_validate.py"


def okf_validate(bundle: Path) -> subprocess.CompletedProcess[str]:
    """Run the pinned okf validator in strict mode on ``bundle``."""
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(bundle), "--strict"],
        capture_output=True,
        text=True,
        check=False,
    )
