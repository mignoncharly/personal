#!/usr/bin/env bash
# Startet die App neu. Optional: ./scripts/restart.sh backend|frontend|postgres
set -euo pipefail
cd "$(dirname "$0")/.."

if [ $# -ge 1 ]; then
  docker compose restart "personal-$1"
else
  docker compose restart
fi
docker compose ps
