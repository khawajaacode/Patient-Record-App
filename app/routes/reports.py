"""
app/routes/reports.py — file upload and download endpoints.
"""
import os

from flask import Blueprint, abort, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from app.backup import trigger_backup
from app.config import ALLOWED_EXTENSIONS, UPLOAD_FOLDER
from app.db import get_db
from app.utils import allowed_file, now, patient_upload_dir, uid

bp = Blueprint("reports", __name__)


@bp.route("/api/patients/<internal_id>/reports", methods=["GET"])
def get_reports(internal_id):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM reports WHERE patient_id = ? ORDER BY uploaded_at DESC",
            (internal_id,),
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@bp.route("/api/patients/<internal_id>/reports", methods=["POST"])
def upload_report(internal_id):
    conn = get_db()
    try:
        patient = conn.execute("SELECT * FROM patients WHERE id = ?", (internal_id,)).fetchone()
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": "No file selected"}), 400
        if not allowed_file(file.filename):
            return jsonify({"error": f"Type not allowed. Use: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

        short_id = patient["patient_id"]
        orig     = secure_filename(file.filename)
        ext      = orig.rsplit(".", 1)[1].lower()
        fname    = f"{uid()}.{ext}"

        save_dir = patient_upload_dir(short_id)
        file.save(os.path.join(save_dir, fname))

        rid = uid()
        conn.execute("""
            INSERT INTO reports
              (id, patient_id, history_id, filename, original_name, file_type,
               report_type, description, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rid, internal_id,
            request.form.get("history_id") or None,
            fname, orig, ext,
            request.form.get("report_type", ""),
            request.form.get("description", ""), now(),
        ))
        conn.commit()
        result = dict(conn.execute("SELECT * FROM reports WHERE id = ?", (rid,)).fetchone())
        trigger_backup("file_uploaded")
        return jsonify(result), 201
    finally:
        conn.close()


@bp.route("/api/reports/<rid>", methods=["DELETE"])
def delete_report(rid):
    conn = get_db()
    try:
        row = conn.execute("""
            SELECT r.*, p.patient_id as short_id
            FROM reports r JOIN patients p ON p.id = r.patient_id
            WHERE r.id = ?
        """, (rid,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404

        fp = os.path.join(UPLOAD_FOLDER, row["short_id"], row["filename"])
        if os.path.exists(fp):
            os.remove(fp)

        conn.execute("DELETE FROM reports WHERE id = ?", (rid,))
        conn.commit()
        trigger_backup("file_deleted")
        return jsonify({"message": "Deleted"})
    finally:
        conn.close()


@bp.route("/uploads/<short_id>/<filename>")
def serve_file(short_id, filename):
    safe_id   = secure_filename(short_id)
    safe_file = secure_filename(filename)
    folder    = os.path.join(UPLOAD_FOLDER, safe_id)
    if not os.path.exists(os.path.join(folder, safe_file)):
        abort(404)
    return send_from_directory(folder, safe_file)
