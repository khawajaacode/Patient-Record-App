@echo off
title MediRecord
cd /d "%~dp0"
pip install -r requirements.txt --quiet --disable-pip-version-check >nul 2>&1
python app.py
