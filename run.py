"""
run.py — application entry point.

Run with:  python run.py
"""
import threading
import webbrowser

from app import create_app
from app.backup import trigger_backup
from app.config import BASE_DIR, DB_PATH, UPLOAD_FOLDER
from app.db import init_db


def _open_browser() -> None:
    import time
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    init_db()

    print("=" * 55)
    print("  MediRecord is starting...")
    print("=" * 55)
    print(f"  Data folder : {BASE_DIR}")
    print(f"  Database    : {DB_PATH}")
    print(f"  Uploads     : {UPLOAD_FOLDER}")
    print("=" * 55)
    print("  Browser will open automatically.")
    print("  Keep this window open while using the app.")
    print("=" * 55)

    trigger_backup("app_startup")
    threading.Thread(target=_open_browser, daemon=True).start()

    app = create_app()
    app.run(debug=False, host="127.0.0.1", port=5000, use_reloader=False)
