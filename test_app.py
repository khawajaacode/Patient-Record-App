#!/usr/bin/env python3
"""Smoke tests for the Patient Record App.

Run with:
    python test_app.py
"""

import io
import os
import shutil
import sys
import tempfile
from contextlib import suppress

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from app import create_app
import app.config as app_config
import app.db as db_module


def main() -> int:
    temp_dir = tempfile.mkdtemp(prefix="patientapp-test-", dir=ROOT)
    temp_db = os.path.join(temp_dir, "patients.db")
    temp_uploads = os.path.join(temp_dir, "uploads")
    os.makedirs(temp_uploads, exist_ok=True)

    # Point the app to a temporary database/uploads folder for isolated testing.
    app_config.DB_PATH = temp_db
    app_config.UPLOAD_FOLDER = temp_uploads
    db_module.DB_PATH = temp_db

    try:
        db_module.init_db()
        app = create_app()
        app.config.update(TESTING=True)
        client = app.test_client()

        print("[1/8] Checking home page...")
        home_resp = client.get("/")
        assert home_resp.status_code == 200, home_resp.status_code

        print("[2/8] Checking stats endpoint...")
        stats_resp = client.get("/api/stats")
        assert stats_resp.status_code == 200, stats_resp.status_code
        stats = stats_resp.get_json()
        assert isinstance(stats, dict), stats

        print("[3/8] Creating patient...")
        patient_payload = {
            "name": "Test Patient",
            "age": 35,
            "gender": "Female",
            "blood_group": "O+",
            "phone": "1234567890",
            "email": "patient@example.com",
            "address": "123 Main Street",
            "emergency_contact": "9999999999",
        }
        create_resp = client.post("/api/patients", json=patient_payload)
        assert create_resp.status_code == 201, create_resp.get_data(as_text=True)
        patient = create_resp.get_json()
        patient_id = patient["id"]
        assert patient["name"] == patient_payload["name"], patient

        print("[4/8] Fetching patient detail...")
        get_patient_resp = client.get(f"/api/patients/{patient_id}")
        assert get_patient_resp.status_code == 200, get_patient_resp.get_data(as_text=True)

        print("[5/8] Adding medical history...")
        history_payload = {
            "visit_date": "2026-06-27",
            "disease": "Flu",
            "diagnosis": "Seasonal influenza",
            "prescription": "Rest and hydration",
            "notes": "Mild symptoms",
            "doctor_name": "Dr. Test",
        }
        history_resp = client.post(f"/api/patients/{patient_id}/history", json=history_payload)
        assert history_resp.status_code == 201, history_resp.get_data(as_text=True)
        history = history_resp.get_json()
        history_id = history["id"]

        print("[6/8] Uploading test report...")
        report_data = {
            "file": (io.BytesIO(b"fake pdf content"), "test-report.pdf"),
            "description": "Routine report",
            "report_type": "Lab",
        }
        upload_resp = client.post(
            f"/api/patients/{patient_id}/reports",
            data=report_data,
            content_type="multipart/form-data",
        )
        assert upload_resp.status_code == 201, upload_resp.get_data(as_text=True)
        report = upload_resp.get_json()
        report_id = report["id"]

        print("[7/8] Running search and file-serving checks...")
        search_resp = client.get("/api/search?keyword=influenza")
        assert search_resp.status_code == 200, search_resp.get_data(as_text=True)
        assert search_resp.get_json(), search_resp.get_json()

        file_resp = client.get(f"/uploads/{patient['patient_id']}/{report['filename']}")
        assert file_resp.status_code == 200, file_resp.status_code

        print("[8/8] Updating and cleaning up test data...")
        update_resp = client.put(
            f"/api/patients/{patient_id}",
            json={"name": "Updated Test Patient", "age": 36},
        )
        assert update_resp.status_code == 200, update_resp.get_data(as_text=True)

        delete_report_resp = client.delete(f"/api/reports/{report_id}")
        assert delete_report_resp.status_code == 200, delete_report_resp.get_data(as_text=True)

        delete_history_resp = client.delete(f"/api/history/{history_id}")
        assert delete_history_resp.status_code == 200, delete_history_resp.get_data(as_text=True)

        delete_patient_resp = client.delete(f"/api/patients/{patient_id}")
        assert delete_patient_resp.status_code == 200, delete_patient_resp.get_data(as_text=True)

        print("All app smoke tests passed.")
        return 0
    except AssertionError as exc:
        print(f"Smoke test failed: {exc}")
        return 1
    finally:
        with suppress(Exception):
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    sys.exit(main())
