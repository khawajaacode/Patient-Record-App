"""
app/config.py — centralised configuration.
All path resolution lives here so every other module just imports from config.
"""
import os
import sys


def _base_dir() -> str:
    """Runtime data / writable directory (next to the executable or source file)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    # Walk up from app/ to the project root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resource_dir() -> str:
    """Read-only template / static directory (unpacked by PyInstaller or source root)."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BASE_DIR     = _base_dir()
RESOURCE_DIR = _resource_dir()

DB_PATH           = os.path.join(BASE_DIR, "patients.db")
UPLOAD_FOLDER     = os.path.join(BASE_DIR, "uploads")
SETTINGS_FILE     = os.path.join(BASE_DIR, "settings.json")
MAX_UPLOAD_BYTES  = 50 * 1024 * 1024          # 50 MB
SECRET_KEY        = "local-medirecord-offline-key"
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "gif", "bmp", "tiff"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
