#!/usr/bin/env bash
# Arranca el servidor usando el entorno virtual del proyecto.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "Creando entorno virtual…"
  python3 -m venv .venv
  .venv/bin/pip install --quiet --upgrade pip
  .venv/bin/pip install --quiet -r requirements.txt
fi

echo "Servidor en http://127.0.0.1:5000"
exec .venv/bin/python app.py
