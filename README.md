# MediRecord — Patient Records System

## HOW TO START THE APP

### Windows
Double-click:  **MediRecord_Windows.vbs**
- No black window will appear
- Your browser opens automatically
- If you see a "Python not found" message, install Python from https://www.python.org/downloads/ (check "Add to PATH")

### Mac / Linux
Double-click:  **MediRecord_Mac_Linux.command**
- On first run on Mac, right-click → Open (required once for security)
- Browser opens automatically

---

## DATA STORAGE
- All patient data is saved in `patients.db` (SQLite database — stays in this folder)
- Uploaded files are saved in the `uploads/` folder
- Both survive restarts, shutdowns, and reboots automatically
- **Do NOT delete** `patients.db` or the `uploads/` folder

## BACKUP
- Set a backup folder in the app's ⚙ Settings
- Backups are ZIP files containing all data + an Excel sheet
- A backup is created automatically after every change

---
Requirements: Python 3.8+ must be installed on the computer.
