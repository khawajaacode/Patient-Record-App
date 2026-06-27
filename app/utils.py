"""
app/utils.py — small, stateless helper functions used across the app.
"""
import os
import uuid
from datetime import datetime

from app.config import ALLOWED_EXTENSIONS, UPLOAD_FOLDER


def now() -> str:
    """Current timestamp as a formatted string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def uid() -> str:
    """New random UUID string."""
    return str(uuid.uuid4())


def allowed_file(filename: str) -> bool:
    """Return True if the file extension is in the allowed set."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_patient_id(conn) -> str:
    """Atomically increment the counter and return the next P-XXXX id."""
    conn.execute("UPDATE id_counter SET value = value + 1 WHERE name = 'patient'")
    row = conn.execute("SELECT value FROM id_counter WHERE name = 'patient'").fetchone()
    return f"P-{row['value']:04d}"


def patient_upload_dir(short_id: str) -> str:
    """Return (and create) the upload directory for a patient."""
    folder = os.path.join(UPLOAD_FOLDER, short_id)
    os.makedirs(folder, exist_ok=True)
    return folder
