"""
app/routes/settings.py — /api/settings and /api/backup/now endpoints.

Settings are persisted as JSON in BASE_DIR/settings.json.
"""
import json
import os

from flask import Blueprint, jsonify, request

from app.config import SETTINGS_FILE
from app.backup import trigger_backup

bp = Blueprint("settings", __name__)


# ---------------------------------------------------------------------------
# Settings helpers (also imported by backup.py)
# ---------------------------------------------------------------------------

def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"backup_folder": ""}


def save_settings(s: dict) -> None:
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(s, f, indent=2)
    except Exception as e:
        print(f"[Settings] Save failed: {e}")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@bp.route("/api/settings", methods=["GET"])
def get_settings():
    return jsonify(load_settings())


@bp.route("/api/settings", methods=["POST"])
def post_settings():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    folder = data.get("backup_folder", "").strip()
    if folder:
        try:
            os.makedirs(folder, exist_ok=True)
        except Exception as e:
            return jsonify({"error": f"Cannot create folder: {e}"}), 400

    s = load_settings()
    s["backup_folder"] = folder
    save_settings(s)
    trigger_backup("folder_set")
    return jsonify({"message": "Saved", "backup_folder": folder})


@bp.route("/api/backup/now", methods=["POST"])
def manual_backup():
    if not load_settings().get("backup_folder", "").strip():
        return jsonify({"error": "No backup folder set. Open ⚙ Settings first."}), 400
    trigger_backup("manual")
    return jsonify({"message": "Backup started in background."})
