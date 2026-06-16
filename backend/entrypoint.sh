#!/bin/sh
set -e

echo "[entrypoint] Warte auf Datenbank & führe Migrationen aus..."
python manage.py migrate --noinput

echo "[entrypoint] Sammle statische Dateien..."
python manage.py collectstatic --noinput

echo "[entrypoint] Starte Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile -
