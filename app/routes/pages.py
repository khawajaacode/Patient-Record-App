"""
app/routes/pages.py — server-rendered HTML page routes.
"""
from flask import Blueprint, render_template

bp = Blueprint("pages", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/patient/<patient_id>")
def patient_detail(patient_id):
    return render_template("patient_detail.html", patient_id=patient_id)
