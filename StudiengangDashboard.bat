@echo off
cd /d "%~dp0" || exit /b 1

python DashboardApp.py
if errorlevel 1 (
    echo Fehler: Python-Skript fehlgeschlagen.
    exit /b 1
)

echo Starte HTTP-Server...
python -m http.server 8000 --directory "output"