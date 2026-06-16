#!/usr/bin/env bash
# Baut und startet die standalone App "personal" (Backend, Frontend, Postgres).
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Code aktualisieren (falls Git-Repo)"
git pull --ff-only 2>/dev/null || echo "   (übersprungen)"

echo "==> Storage-/Log-Verzeichnisse sicherstellen"
mkdir -p storage/static storage/media storage/invoices logs backups

if [ ! -f .env ]; then
  echo "FEHLER: .env fehlt. Bitte 'cp .env.production.example .env' und Werte setzen."
  exit 1
fi

echo "==> Images bauen und Container starten"
docker compose up -d --build

echo "==> Migrationen & collectstatic laufen automatisch im Backend-Entrypoint."
sleep 3
docker compose ps
echo "==> Fertig. Logs: ./scripts/logs.sh backend"
