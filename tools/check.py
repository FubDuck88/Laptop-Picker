"""Run the offline baseline checks with the current Python and installed Node."""

import ast
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def main():
    node = shutil.which("node")
    if not node:
        print("Node.js 22 or newer is required for frontend checks.", file=sys.stderr)
        return 1

    # Parse without importing launchers or writing bytecode into the checkout.
    for path in [*ROOT.glob("*.py"), *ROOT.glob("scrapers/*.py"),
                 *ROOT.glob("tools/*.py"), *ROOT.glob("tests/*.py")]:
        ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))

    commands = [
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"],
        [node, "--test", *[str(path.relative_to(ROOT)) for path in sorted((ROOT / "tests").glob("*.test.cjs"))]],
        *[[node, "--check", str(path)] for path in sorted(ROOT.glob("js/*.js"))],
    ]
    failed = False
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, check=False)
        failed = result.returncode != 0 or failed
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
