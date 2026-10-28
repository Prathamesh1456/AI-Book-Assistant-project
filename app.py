"""
Entry point at repo root. Runs backend/app.py using the project venv when available
(so `pip install -r requirements.txt` in venv is picked up even if you type `python app.py`).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_BACKEND = _ROOT / "backend" / "app.py"


def _venv_python(root: Path) -> Path | None:
    if sys.platform == "win32":
        p = root / "venv" / "Scripts" / "python.exe"
    else:
        p = root / "venv" / "bin" / "python"
    return p if p.is_file() else None


def main() -> None:
    import subprocess

    vp = _venv_python(_ROOT)
    if vp is not None and Path(sys.executable).resolve() != vp.resolve():
        raise SystemExit(
            subprocess.call(
                [str(vp.resolve()), str(_BACKEND.resolve()), *sys.argv[1:]],
                cwd=str(_ROOT),
            )
        )

    import runpy

    runpy.run_path(str(_BACKEND), run_name="__main__")


if __name__ == "__main__":
    main()
