#!/usr/bin/env bash
# Taegliches Backup (NATIV, ohne Docker): PostgreSQL-Dump + Rechnungs-PDFs.
# Aufbewahrung 30 Tage. DB-Zugang aus ../.env.
set -euo pipefail
cd "$(dirname "$0")/.."

set -a; . ./.env; set +a
TS=$(date +%Y%m%d_%H%M%S)
mkdir -p backups

# DB-Host/Port aus DATABASE_URL bzw. Default 127.0.0.1:5432
DB_HOST="${PGHOST:-127.0.0.1}"
DB_PORT="${PGPORT:-5432}"

echo "==> Datenbank-Dump (${POSTGRES_DB})"
PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" "$POSTGRES_DB" \
  | gzip > "backups/db_${TS}.sql.gz"

echo "==> Rechnungs-PDFs sichern"
if [ -d storage/invoices ] && [ -n "$(ls -A storage/invoices 2>/dev/null)" ]; then
  tar -czf "backups/invoices_${TS}.tar.gz" -C storage invoices
fi

echo "==> Backups aelter als 30 Tage entfernen"
find backups -name '*.gz' -mtime +30 -delete || true

echo "==> Aktuelle Backups:"
ls -lh backups | tail -n 6
