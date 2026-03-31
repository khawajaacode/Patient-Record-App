# MediRecord – Doctor Patient Record System

A local, offline patient record management system built with Python + Flask + SQLite.

## Features
- Add / Edit / Delete patients with full info
- Medical history & visit notes per patient
- Upload and view CT scans, MRIs, PDFs, images
- Keyword search for disease/diagnosis research
- Runs 100% offline on your laptop

## Requirements
- Python 3.8 or higher
- No internet needed after setup

## How to Run

### Windows
Double-click `run_windows.bat`  
Or in terminal: `python app.py`

### Mac / Linux
```bash
chmod +x run_mac_linux.sh
./run_mac_linux.sh
```
Or: `python3 app.py`

### Manual
```bash
pip install flask werkzeug
python app.py
```
Then open: http://127.0.0.1:5000

## File Structure
```
patient_records/
├── app.py              ← Main Flask application
├── requirements.txt    ← Python dependencies
├── patients.db         ← SQLite database (auto-created)
├── uploads/            ← Uploaded files (auto-created)
├── templates/
│   ├── index.html      ← Patient list dashboard
│   └── patient_detail.html  ← Patient detail page
├── run_windows.bat     ← Windows quick-start
└── run_mac_linux.sh    ← Mac/Linux quick-start
```

## Data Storage
- All data is stored locally in `patients.db` (SQLite)
- Uploaded files are stored in the `uploads/` folder
- No cloud, no internet, fully private

## Notes
- Max file upload size: 50MB
- Supported file types: PDF, PNG, JPG, JPEG, GIF, BMP, TIFF
