"""Manual launcher for the verified ALL IT collector and release validator."""
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parent
    runner = str(root / 'tools/run_daily.py')
    collected = subprocess.run([sys.executable, '-B', runner, '--sources', 'allit'], cwd=root)
    if collected.returncode:
        return collected.returncode
    return subprocess.run([sys.executable, '-B', runner, '--validate'], cwd=root).returncode


if __name__ == '__main__':
    raise SystemExit(main())
