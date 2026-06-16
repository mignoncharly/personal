#!/usr/bin/env bash
# Zeigt Logs. Optional: ./scripts/logs.sh backend|frontend|postgres
set -euo pipefail
cd "$(dirname "$0")/.."

SVC="${1:-}"
if [ -n "$SVC" ]; then
  docker compose logs -f --tail=200 "personal-$SVC"
else
  docker compose logs -f --tail=200
fi
