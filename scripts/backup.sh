#!/usr/bin/env bash
# Tägliches Backup: PostgreSQL-Dump + Rechnungs-PDFs. Aufbewahrung 30 Tage.
set -euo pipefail
cd "$(dirname "$0")/.."

set -a; . ./.env; set +a
TS=$(date +%Y%m%d_%H%M%S)
mkdir -p backups

echo "==> Datenbank-Dump (${POSTGRES_DB})"
docker exec personal-postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "backups/db_${TS}.sql.gz"

echo "==> Rechnungs-PDFs sichern"
if [ -d storage/invoices ]; then
  tar -czf "backups/invoices_${TS}.tar.gz" -C storage invoices
fi

echo "==> Backups älter als 30 Tage entfernen"
find backups -name '*.gz' -mtime +30 -delete || true

echo "==> Aktuelle Backups:"
ls -lh backups | tail -n 6
