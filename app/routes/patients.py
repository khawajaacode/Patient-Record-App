"""
app/routes/patients.py — CRUD endpoints for /api/patients.
"""
import shutil
import os

from flask import Blueprint, jsonify, request

from app.backup import trigger_backup
from app.db import get_db
from app.utils import generate_patient_id, now, patient_upload_dir, uid

bp = Blueprint("patients", __name__)


@bp.route("/api/patients", methods=["GET"])
def list_patients():
    s    = request.args.get("search", "").strip()
    conn = get_db()
    try:
        if s:
            like = f"%{s}%"
            rows = conn.execute("""
                SELECT p.*, COUNT(mh.id) as visit_count
                FROM patients p
                LEFT JOIN medical_history mh ON p.id = mh.patient_id
                WHERE p.name LIKE ? OR p.phone LIKE ? OR p.blood_group LIKE ?
                   OR p.patient_id LIKE ?
                   OR EXISTS (
                       SELECT 1 FROM medical_history m2
                       WHERE m2.patient_id = p.id
                         AND (m2.disease LIKE ? OR m2.diagnosis LIKE ?)
                   )
                GROUP BY p.id ORDER BY p.patient_id ASC
            """, (like, like, like, like, like, like)).fetchall()
        else:
            rows = conn.execute("""
                SELECT p.*, COUNT(mh.id) as visit_count
                FROM patients p
                LEFT JOIN medical_history mh ON p.id = mh.patient_id
                GROUP BY p.id ORDER BY p.patient_id ASC
            """).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@bp.route("/api/patients", methods=["POST"])
def create_patient():
    data = request.get_json()
    if not data or not data.get("name", "").strip():
        return jsonify({"error": "Name required"}), 400

    internal_id = uid()
    ts          = now()
    conn        = get_db()
    try:
        short_id = generate_patient_id(conn)
        conn.execute("""
            INSERT INTO patients
              (id, patient_id, name, age, gender, blood_group, phone, email,
               address, emergency_contact, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            internal_id, short_id, data["name"].strip(),
            data.get("age"), data.get("gender", ""), data.get("blood_group", ""),
            data.get("phone", ""), data.get("email", ""),
            data.get("address", ""), data.get("emergency_contact", ""), ts, ts,
        ))
        conn.commit()
        patient_upload_dir(short_id)
        result = dict(conn.execute("SELECT * FROM patients WHERE id = ?", (internal_id,)).fetchone())
        trigger_backup("patient_added")
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@bp.route("/api/patients/<internal_id>", methods=["GET"])
def get_patient(internal_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM patients WHERE id = ?", (internal_id,)).fetchone()
        return jsonify(dict(row)) if row else (jsonify({"error": "Not found"}), 404)
    finally:
        conn.close()


@bp.route("/api/patients/<internal_id>", methods=["PUT"])
def update_patient(internal_id):
    data = request.get_json()
    if not data or not data.get("name", "").strip():
        return jsonify({"error": "Name required"}), 400

    conn = get_db()
    try:
        if not conn.execute("SELECT id FROM patients WHERE id = ?", (internal_id,)).fetchone():
            return jsonify({"error": "Not found"}), 404

        conn.execute("""
            UPDATE patients
            SET name=?, age=?, gender=?, blood_group=?, phone=?,
                email=?, address=?, emergency_contact=?, updated_at=?
            WHERE id=?
        """, (
            data["name"].strip(), data.get("age"), data.get("gender", ""),
            data.get("blood_group", ""), data.get("phone", ""), data.get("email", ""),
            data.get("address", ""), data.get("emergency_contact", ""), now(), internal_id,
        ))
        conn.commit()
        result = dict(conn.execute("SELECT * FROM patients WHERE id = ?", (internal_id,)).fetchone())
        trigger_backup("patient_updated")
        return jsonify(result)
    finally:
        conn.close()


@bp.route("/api/patients/<internal_id>", methods=["DELETE"])
def delete_patient(internal_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM patients WHERE id = ?", (internal_id,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404

        from app.config import UPLOAD_FOLDER
        pid_folder = os.path.join(UPLOAD_FOLDER, row["patient_id"])
        if os.path.exists(pid_folder):
            shutil.rmtree(pid_folder)

        conn.execute("DELETE FROM patients WHERE id = ?", (internal_id,))
        conn.commit()
        trigger_backup("patient_deleted")
        return jsonify({"message": "Deleted"})
    finally:
        conn.close()
