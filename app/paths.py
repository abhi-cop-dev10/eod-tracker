"""
Centralised path resolution that works both in source and PyInstaller EXE.

When frozen (running as .exe):
  - sys._MEIPASS  = read-only bundle dir  (assets, templates)
  - exe_dir       = folder next to the .exe (user data: db, exports)

When running from source:
  - Both point to the project root.
"""
import sys
from pathlib import Path


def _exe_dir() -> Path:
    """Writable directory — next to the .exe, or project root in dev."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


def _bundle_dir() -> Path:
    """Read-only resource directory — _MEIPASS in EXE, project root in dev."""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent


def data_dir() -> Path:
    """Where the SQLite database is stored (must be writable)."""
    p = _exe_dir() / "data"
    p.mkdir(parents=True, exist_ok=True)
    return p


def assets_dir() -> Path:
    """Bundled assets (icons, images) — read from bundle dir."""
    return _bundle_dir() / "assets"


def templates_dir() -> Path:
    """Default templates dir — read from bundle dir."""
    return _bundle_dir() / "templates"


def db_path() -> Path:
    return data_dir() / "tasks.db"
