"""
app/db.py — database connection and schema initialisation.
"""
import sqlite3

from app.config import DB_PATH


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    """Return an open connection with row_factory and foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create tables if they do not already exist."""
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id                TEXT PRIMARY KEY,
            patient_id        TEXT UNIQUE NOT NULL,
            name              TEXT NOT NULL,
            age               INTEGER,
            gender            TEXT,
            blood_group       TEXT,
            phone             TEXT,
            email             TEXT,
            address           TEXT,
            emergency_contact TEXT,
            created_at        TEXT NOT NULL,
            updated_at        TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS medical_history (
            id           TEXT PRIMARY KEY,
            patient_id   TEXT NOT NULL,
            visit_date   TEXT NOT NULL,
            disease      TEXT,
            diagnosis    TEXT,
            prescription TEXT,
            notes        TEXT,
            doctor_name  TEXT,
            created_at   TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id            TEXT PRIMARY KEY,
            patient_id    TEXT NOT NULL,
            history_id    TEXT,
            filename      TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_type     TEXT NOT NULL,
            report_type   TEXT,
            description   TEXT,
            uploaded_at   TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
        )
    """)

    # Sequential patient-ID counter
    c.execute("""
        CREATE TABLE IF NOT EXISTS id_counter (
            name  TEXT PRIMARY KEY,
            value INTEGER NOT NULL DEFAULT 0
        )
    """)
    c.execute("INSERT OR IGNORE INTO id_counter (name, value) VALUES ('patient', 0)")

    conn.commit()
    conn.close()
