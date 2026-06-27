"""
app/routes/history.py — CRUD endpoints for medical history records.
"""
from flask import Blueprint, jsonify, request

from app.backup import trigger_backup
from app.db import get_db
from app.utils import now, uid

bp = Blueprint("history", __name__)


@bp.route("/api/patients/<internal_id>/history", methods=["GET"])
def get_history(internal_id):
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT mh.*, COUNT(r.id) as report_count
            FROM medical_history mh
            LEFT JOIN reports r ON mh.id = r.history_id
            WHERE mh.patient_id = ?
            GROUP BY mh.id ORDER BY mh.visit_date DESC
        """, (internal_id,)).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@bp.route("/api/patients/<internal_id>/history", methods=["POST"])
def add_history(internal_id):
    data = request.get_json()
    if not data or not data.get("visit_date", "").strip():
        return jsonify({"error": "Date required"}), 400

    conn = get_db()
    try:
        if not conn.execute("SELECT id FROM patients WHERE id = ?", (internal_id,)).fetchone():
            return jsonify({"error": "Patient not found"}), 404

        hid = uid()
        conn.execute("""
            INSERT INTO medical_history
              (id, patient_id, visit_date, disease, diagnosis, prescription, notes, doctor_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            hid, internal_id, data["visit_date"].strip(),
            data.get("disease", ""), data.get("diagnosis", ""),
            data.get("prescription", ""), data.get("notes", ""),
            data.get("doctor_name", ""), now(),
        ))
        conn.execute("UPDATE patients SET updated_at=? WHERE id=?", (now(), internal_id))
        conn.commit()
        result = dict(conn.execute("SELECT * FROM medical_history WHERE id = ?", (hid,)).fetchone())
        trigger_backup("visit_added")
        return jsonify(result), 201
    finally:
        conn.close()


@bp.route("/api/history/<hid>", methods=["PUT"])
def update_history(hid):
    data = request.get_json()
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM medical_history WHERE id = ?", (hid,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404

        conn.execute("""
            UPDATE medical_history
            SET visit_date=?, disease=?, diagnosis=?, prescription=?, notes=?, doctor_name=?
            WHERE id=?
        """, (
            data.get("visit_date",   row["visit_date"]),
            data.get("disease",      row["disease"]),
            data.get("diagnosis",    row["diagnosis"]),
            data.get("prescription", row["prescription"]),
            data.get("notes",        row["notes"]),
            data.get("doctor_name",  row["doctor_name"]),
            hid,
        ))
        conn.execute("UPDATE patients SET updated_at=? WHERE id=?", (now(), row["patient_id"]))
        conn.commit()
        result = dict(conn.execute("SELECT * FROM medical_history WHERE id = ?", (hid,)).fetchone())
        trigger_backup("visit_updated")
        return jsonify(result)
    finally:
        conn.close()


@bp.route("/api/history/<hid>", methods=["DELETE"])
def delete_history(hid):
    conn = get_db()
    try:
        if not conn.execute("SELECT id FROM medical_history WHERE id = ?", (hid,)).fetchone():
            return jsonify({"error": "Not found"}), 404
        conn.execute("DELETE FROM medical_history WHERE id = ?", (hid,))
        conn.commit()
        trigger_backup("visit_deleted")
        return jsonify({"message": "Deleted"})
    finally:
        conn.close()
