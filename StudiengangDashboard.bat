@echo off
cd /d "%~dp0" || exit /b 1

python DashboardApp.py
if errorlevel 1 (
    echo Fehler: Python-Skript fehlgeschlagen.
    pause "Drücken Sie eine beliebige Taste, um fortzufahren..."
    exit /b 1
)

echo Starte HTTP-Server...
echo Drücken Sie Strg+C, um den Server zu stoppen.
python -m http.server 8000 --directory "output"