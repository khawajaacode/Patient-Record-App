import os
import sqlite3
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload
app.config['SECRET_KEY'] = 'local-doctor-records-key'

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'dcm'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ──────────────────────────────────────────────
# DATABASE SETUP
# ──────────────────────────────────────────────

def get_db():
    db_path = os.path.join(os.path.dirname(__file__), 'patients.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            age         INTEGER,
            gender      TEXT,
            blood_group TEXT,
            phone       TEXT,
            email       TEXT,
            address     TEXT,
            emergency_contact TEXT,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        )
    ''')

    cursor.execute('''
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
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id           TEXT PRIMARY KEY,
            patient_id   TEXT NOT NULL,
            history_id   TEXT,
            filename     TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_type    TEXT NOT NULL,
            report_type  TEXT,
            description  TEXT,
            uploaded_at  TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def generate_id():
    return str(uuid.uuid4())

# ──────────────────────────────────────────────
# ROUTES – PAGES
# ──────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/patient/<patient_id>')
def patient_detail(patient_id):
    return render_template('patient_detail.html', patient_id=patient_id)

# ──────────────────────────────────────────────
# API – PATIENTS
# ──────────────────────────────────────────────

@app.route('/api/patients', methods=['GET'])
def get_patients():
    search = request.args.get('search', '').strip()
    conn = get_db()
    try:
        if search:
            rows = conn.execute('''
                SELECT p.*, COUNT(mh.id) as visit_count
                FROM patients p
                LEFT JOIN medical_history mh ON p.id = mh.patient_id
                WHERE p.name LIKE ? OR p.phone LIKE ? OR p.blood_group LIKE ?
                   OR EXISTS (
                       SELECT 1 FROM medical_history mh2
                       WHERE mh2.patient_id = p.id
                         AND (mh2.disease LIKE ? OR mh2.diagnosis LIKE ?)
                   )
                GROUP BY p.id
                ORDER BY p.updated_at DESC
            ''', (f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%')).fetchall()
        else:
            rows = conn.execute('''
                SELECT p.*, COUNT(mh.id) as visit_count
                FROM patients p
                LEFT JOIN medical_history mh ON p.id = mh.patient_id
                GROUP BY p.id
                ORDER BY p.updated_at DESC
            ''').fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()

@app.route('/api/patients', methods=['POST'])
def create_patient():
    data = request.get_json()
    if not data or not data.get('name', '').strip():
        return jsonify({'error': 'Patient name is required'}), 400

    patient_id = generate_id()
    timestamp = now()

    conn = get_db()
    try:
        conn.execute('''
            INSERT INTO patients (id, name, age, gender, blood_group, phone, email, address, emergency_contact, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient_id,
            data['name'].strip(),
            data.get('age'),
            data.get('gender', ''),
            data.get('blood_group', ''),
            data.get('phone', ''),
            data.get('email', ''),
            data.get('address', ''),
            data.get('emergency_contact', ''),
            timestamp, timestamp
        ))
        conn.commit()
        row = conn.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
        return jsonify(dict(row)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/patients/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    conn = get_db()
    try:
        row = conn.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
        if not row:
            return jsonify({'error': 'Patient not found'}), 404
        return jsonify(dict(row))
    finally:
        conn.close()

@app.route('/api/patients/<patient_id>', methods=['PUT'])
def update_patient(patient_id):
    data = request.get_json()
    if not data or not data.get('name', '').strip():
        return jsonify({'error': 'Patient name is required'}), 400

    conn = get_db()
    try:
        row = conn.execute('SELECT id FROM patients WHERE id = ?', (patient_id,)).fetchone()
        if not row:
            return jsonify({'error': 'Patient not found'}), 404

        conn.execute('''
            UPDATE patients SET name=?, age=?, gender=?, blood_group=?, phone=?,
            email=?, address=?, emergency_contact=?, updated_at=?
            WHERE id=?
        ''', (
            data['name'].strip(), data.get('age'), data.get('gender', ''),
            data.get('blood_group', ''), data.get('phone', ''),
            data.get('email', ''), data.get('address', ''),
            data.get('emergency_contact', ''), now(), patient_id
        ))
        conn.commit()
        updated = conn.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
        return jsonify(dict(updated))
    finally:
        conn.close()

@app.route('/api/patients/<patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    conn = get_db()
    try:
        row = conn.execute('SELECT id FROM patients WHERE id = ?', (patient_id,)).fetchone()
        if not row:
            return jsonify({'error': 'Patient not found'}), 404

        # Delete associated files from disk
        reports = conn.execute('SELECT filename FROM reports WHERE patient_id = ?', (patient_id,)).fetchall()
        for report in reports:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], report['filename'])
            if os.path.exists(filepath):
                os.remove(filepath)

        conn.execute('DELETE FROM patients WHERE id = ?', (patient_id,))
        conn.commit()
        return jsonify({'message': 'Patient deleted successfully'})
    finally:
        conn.close()

# ──────────────────────────────────────────────
# API – MEDICAL HISTORY
# ──────────────────────────────────────────────

@app.route('/api/patients/<patient_id>/history', methods=['GET'])
def get_history(patient_id):
    conn = get_db()
    try:
        rows = conn.execute('''
            SELECT mh.*, COUNT(r.id) as report_count
            FROM medical_history mh
            LEFT JOIN reports r ON mh.id = r.history_id
            WHERE mh.patient_id = ?
            GROUP BY mh.id
            ORDER BY mh.visit_date DESC
        ''', (patient_id,)).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()

@app.route('/api/patients/<patient_id>/history', methods=['POST'])
def add_history(patient_id):
    data = request.get_json()
    if not data or not data.get('visit_date', '').strip():
        return jsonify({'error': 'Visit date is required'}), 400

    conn = get_db()
    try:
        patient = conn.execute('SELECT id FROM patients WHERE id = ?', (patient_id,)).fetchone()
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404

        history_id = generate_id()
        conn.execute('''
            INSERT INTO medical_history (id, patient_id, visit_date, disease, diagnosis, prescription, notes, doctor_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            history_id, patient_id,
            data['visit_date'].strip(),
            data.get('disease', ''),
            data.get('diagnosis', ''),
            data.get('prescription', ''),
            data.get('notes', ''),
            data.get('doctor_name', ''),
            now()
        ))
        conn.execute('UPDATE patients SET updated_at=? WHERE id=?', (now(), patient_id))
        conn.commit()
        row = conn.execute('SELECT * FROM medical_history WHERE id = ?', (history_id,)).fetchone()
        return jsonify(dict(row)), 201
    finally:
        conn.close()

@app.route('/api/history/<history_id>', methods=['PUT'])
def update_history(history_id):
    data = request.get_json()
    conn = get_db()
    try:
        row = conn.execute('SELECT * FROM medical_history WHERE id = ?', (history_id,)).fetchone()
        if not row:
            return jsonify({'error': 'Record not found'}), 404

        conn.execute('''
            UPDATE medical_history SET visit_date=?, disease=?, diagnosis=?, prescription=?, notes=?, doctor_name=?
            WHERE id=?
        ''', (
            data.get('visit_date', row['visit_date']),
            data.get('disease', row['disease']),
            data.get('diagnosis', row['diagnosis']),
            data.get('prescription', row['prescription']),
            data.get('notes', row['notes']),
            data.get('doctor_name', row['doctor_name']),
            history_id
        ))
        conn.execute('UPDATE patients SET updated_at=? WHERE id=?', (now(), row['patient_id']))
        conn.commit()
        updated = conn.execute('SELECT * FROM medical_history WHERE id = ?', (history_id,)).fetchone()
        return jsonify(dict(updated))
    finally:
        conn.close()

@app.route('/api/history/<history_id>', methods=['DELETE'])
def delete_history(history_id):
    conn = get_db()
    try:
        row = conn.execute('SELECT * FROM medical_history WHERE id = ?', (history_id,)).fetchone()
        if not row:
            return jsonify({'error': 'Record not found'}), 404

        reports = conn.execute('SELECT filename FROM reports WHERE history_id = ?', (history_id,)).fetchall()
        for report in reports:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], report['filename'])
            if os.path.exists(filepath):
                os.remove(filepath)

        conn.execute('DELETE FROM medical_history WHERE id = ?', (history_id,))
        conn.commit()
        return jsonify({'message': 'Visit record deleted'})
    finally:
        conn.close()

# ──────────────────────────────────────────────
# API – REPORTS / FILE UPLOAD
# ──────────────────────────────────────────────

@app.route('/api/patients/<patient_id>/reports', methods=['GET'])
def get_reports(patient_id):
    conn = get_db()
    try:
        rows = conn.execute('''
            SELECT * FROM reports WHERE patient_id = ? ORDER BY uploaded_at DESC
        ''', (patient_id,)).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()

@app.route('/api/patients/<patient_id>/reports', methods=['POST'])
def upload_report(patient_id):
    conn = get_db()
    try:
        patient = conn.execute('SELECT id FROM patients WHERE id = ?', (patient_id,)).fetchone()
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404

        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

        original_name = secure_filename(file.filename)
        ext = original_name.rsplit('.', 1)[1].lower()
        unique_filename = f"{generate_id()}.{ext}"

        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))

        report_id = generate_id()
        conn.execute('''
            INSERT INTO reports (id, patient_id, history_id, filename, original_name, file_type, report_type, description, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report_id, patient_id,
            request.form.get('history_id') or None,
            unique_filename, original_name, ext,
            request.form.get('report_type', ''),
            request.form.get('description', ''),
            now()
        ))
        conn.commit()
        row = conn.execute('SELECT * FROM reports WHERE id = ?', (report_id,)).fetchone()
        return jsonify(dict(row)), 201
    finally:
        conn.close()

@app.route('/api/reports/<report_id>', methods=['DELETE'])
def delete_report(report_id):
    conn = get_db()
    try:
        row = conn.execute('SELECT * FROM reports WHERE id = ?', (report_id,)).fetchone()
        if not row:
            return jsonify({'error': 'Report not found'}), 404

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], row['filename'])
        if os.path.exists(filepath):
            os.remove(filepath)

        conn.execute('DELETE FROM reports WHERE id = ?', (report_id,))
        conn.commit()
        return jsonify({'message': 'Report deleted'})
    finally:
        conn.close()

@app.route('/uploads/<filename>')
def serve_file(filename):
    safe_filename = secure_filename(filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    if not os.path.exists(filepath):
        abort(404)
    return send_from_directory(app.config['UPLOAD_FOLDER'], safe_filename)

# ──────────────────────────────────────────────
# API – SEARCH (Disease / Keyword Filter)
# ──────────────────────────────────────────────

@app.route('/api/search', methods=['GET'])
def search_by_disease():
    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return jsonify([])

    conn = get_db()
    try:
        rows = conn.execute('''
            SELECT DISTINCT p.id, p.name, p.age, p.gender, p.blood_group, p.phone,
                   mh.disease, mh.diagnosis, mh.visit_date, mh.doctor_name
            FROM patients p
            JOIN medical_history mh ON p.id = mh.patient_id
            WHERE mh.disease LIKE ? OR mh.diagnosis LIKE ? OR mh.notes LIKE ? OR mh.prescription LIKE ?
            ORDER BY mh.visit_date DESC
        ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%')).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()

# ──────────────────────────────────────────────
# API – STATS
# ──────────────────────────────────────────────

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    try:
        total_patients = conn.execute('SELECT COUNT(*) as c FROM patients').fetchone()['c']
        total_visits = conn.execute('SELECT COUNT(*) as c FROM medical_history').fetchone()['c']
        total_reports = conn.execute('SELECT COUNT(*) as c FROM reports').fetchone()['c']
        recent_patients = conn.execute(
            'SELECT COUNT(*) as c FROM patients WHERE created_at >= date("now", "-30 days")'
        ).fetchone()['c']
        return jsonify({
            'total_patients': total_patients,
            'total_visits': total_visits,
            'total_reports': total_reports,
            'recent_patients': recent_patients
        })
    finally:
        conn.close()

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    print("\n✅ Doctor Patient Record System is running!")
    print("🌐 Open your browser and go to: http://127.0.0.1:5000\n")
    app.run(debug=False, host='127.0.0.1', port=5000)
