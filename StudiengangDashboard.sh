#!/bin/bash

cd "$(dirname "$0")" || exit 1

if python3 DashboardApp.py; then
    echo "Starte HTTP-Server..."
    exec python3 -m http.server 8000 --directory "./output"
else
    echo "Fehler: Python-Skript fehlgeschlagen."
    exit 1
fi