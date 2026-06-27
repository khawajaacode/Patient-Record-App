"""
app/routes/search.py — /api/search and /api/stats endpoints.
"""
from flask import Blueprint, jsonify, request

from app.db import get_db

bp = Blueprint("search", __name__)


@bp.route("/api/search", methods=["GET"])
def search_disease():
    kw = request.args.get("keyword", "").strip()
    if not kw:
        return jsonify([])

    like = f"%{kw}%"
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT DISTINCT p.id, p.patient_id, p.name, p.age, p.gender,
                   p.blood_group, p.phone,
                   mh.disease, mh.diagnosis, mh.visit_date, mh.doctor_name
            FROM patients p
            JOIN medical_history mh ON p.id = mh.patient_id
            WHERE mh.disease LIKE ? OR mh.diagnosis LIKE ?
               OR mh.notes LIKE ? OR mh.prescription LIKE ?
            ORDER BY p.patient_id ASC, mh.visit_date DESC
        """, (like, like, like, like)).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@bp.route("/api/stats", methods=["GET"])
def get_stats():
    conn = get_db()
    try:
        return jsonify({
            "total_patients":  conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
            "total_visits":    conn.execute("SELECT COUNT(*) FROM medical_history").fetchone()[0],
            "total_reports":   conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0],
            "recent_patients": conn.execute(
                'SELECT COUNT(*) FROM patients WHERE created_at >= date("now", "-30 days")'
            ).fetchone()[0],
        })
    finally:
        conn.close()
