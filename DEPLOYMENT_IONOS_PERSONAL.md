# Deployment – „personal" auf IONOS VPS

Standalone-Deployment der App **Mouvin Personal Schicht- & Rechnungssystem**
(Django + Next.js + PostgreSQL) unter `personal.meinpflegeweg.com`.

> **Isolation:** Diese App teilt **keine** Laufzeitdienste mit `meinpflegeweg`
> oder anderen Apps. Eigene Container, eigenes venv (im Image), eigene DB,
> eigene Volumes, eigene Static-/Media-/PDF-Ordner, eigene Logs.
> An der bestehenden App wird **nichts** geändert – nur ein **neuer** Nginx-Site-Block
> kommt hinzu.

---

## 1. Server-Pfade

| Zweck | Pfad |
|---|---|
| App-Wurzel | `~/apps/personal` (`/home/mignon/apps/personal`) |
| Backend (Django) | `~/apps/personal/backend` |
| Frontend (Next.js) | `~/apps/personal/frontend` |
| Umgebungsdatei | `~/apps/personal/.env` |
| Statische Dateien | `~/apps/personal/storage/static` |
| Medien | `~/apps/personal/storage/media` |
| Rechnungs-PDFs | `~/apps/personal/storage/invoices` |
| Logs | `~/apps/personal/logs` |
| Backups | `~/apps/personal/backups` |
| Nginx-Site | `/etc/nginx/sites-available/personal.meinpflegeweg.com` |

## 2. Dienste (alle eigenständig, Präfix `personal-`)

| Dienst | Container | Port (nur lokal) | Beschreibung |
|---|---|---|---|
| Backend | `personal-backend` | `127.0.0.1:8001 → 8000` | Django + Gunicorn |
| Frontend | `personal-frontend` | `127.0.0.1:3001 → 3000` | Next.js |
| Datenbank | `personal-postgres` | (kein Host-Port) | PostgreSQL 18 |
| Volume | `personal_pgdata` | – | DB-Daten |
| Netzwerk | `personal_net` | – | internes Netz |

Die Container lauschen nur auf `127.0.0.1` – von außen erreichbar ist die App
ausschließlich über Nginx (TLS).

## 3. Umgebungsvariablen (`.env`)

Vorlage: `.env.production.example` → kopieren nach `.env` und Werte setzen.
**Keine Secrets ins Git.** Wichtigste Variablen:

- `SECRET_KEY` – langer Zufallswert
- `DEBUG=False`
- `ALLOWED_HOSTS=personal.meinpflegeweg.com`
- `POSTGRES_DB=personal_db`, `POSTGRES_USER=personal_user`, `POSTGRES_PASSWORD=…`
- `DATABASE_URL=postgres://personal_user:…@personal-postgres:5432/personal_db`
- `CORS_ALLOWED_ORIGINS` / `CSRF_TRUSTED_ORIGINS = https://personal.meinpflegeweg.com`
- `STORAGE_DIR=/app/storage`, `STATIC_ROOT`, `MEDIA_ROOT`, `INVOICE_ROOT`, `LOG_DIR=/app/logs`
- SMTP: `EMAIL_USE_CONSOLE=False`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`
- `NEXT_PUBLIC_API_URL=https://personal.meinpflegeweg.com/api`

`SECRET_KEY` erzeugen:
```bash
docker run --rm python:3.13-slim python -c "import secrets; print(secrets.token_urlsafe(64))"
```

## 4. Datenbank (separat)

PostgreSQL läuft als **eigener** Container `personal-postgres` mit eigenem Volume
`personal_pgdata`. DB/User/Passwort kommen aus `.env`. Es wird **keine** bestehende
DB verwendet. Migrationen laufen automatisch beim Backend-Start (Entrypoint).

## 5. Erstmalige Einrichtung auf dem Server

```bash
ssh mignon@217.154.166.155

# 1) Struktur prüfen (nichts löschen/überschreiben)
cd ~/apps && ls -la
ls -la ~/apps/meinpflegeweg

# 2) Projekt nach ~/apps/personal bringen (Git oder rsync)
git clone <REPO_URL> ~/apps/personal      # ODER per rsync hochladen
cd ~/apps/personal

# 3) Umgebungsdatei anlegen
cp .env.production.example .env
nano .env      # alle BITTE_…-Platzhalter ersetzen

# 4) Verzeichnisse + Build + Start
chmod +x scripts/*.sh backend/entrypoint.sh
./scripts/deploy.sh

# 5) Admin-Benutzer anlegen
docker exec -it personal-backend python manage.py createsuperuser
```

## 6. Nginx einrichten (neuer Site-Block, bestehende App unberührt)

```bash
sudo cp ~/apps/personal/nginx/personal.meinpflegeweg.com.conf \
        /etc/nginx/sites-available/personal.meinpflegeweg.com
sudo ln -s /etc/nginx/sites-available/personal.meinpflegeweg.com \
           /etc/nginx/sites-enabled/personal.meinpflegeweg.com

# ACME-Webroot (falls noch nicht vorhanden)
sudo mkdir -p /var/www/certbot

sudo nginx -t && sudo systemctl reload nginx
```

> Die bestehende Seite `meinpflegeweg.com` hat ihren eigenen Site-Block und wird
> hierdurch nicht verändert.

## 7. HTTPS mit Let's Encrypt / Certbot

DNS-Voraussetzung: `personal.meinpflegeweg.com` zeigt per A/AAAA auf `217.154.166.155`.

```bash
sudo certbot --nginx -d personal.meinpflegeweg.com
# oder Webroot-Variante:
# sudo certbot certonly --webroot -w /var/www/certbot -d personal.meinpflegeweg.com
sudo nginx -t && sudo systemctl reload nginx
```

Auto-Renewal prüfen: `sudo certbot renew --dry-run`.

## 8. Befehle im Alltag

| Aktion | Befehl |
|---|---|
| Deployen / Update | `./scripts/deploy.sh` |
| Neustart (alle) | `./scripts/restart.sh` |
| Neustart (eins) | `./scripts/restart.sh backend` \| `frontend` \| `postgres` |
| Logs (alle) | `./scripts/logs.sh` |
| Logs (eins) | `./scripts/logs.sh backend` \| `frontend` \| `postgres` |
| Backup | `./scripts/backup.sh` |
| Migration manuell | `docker exec personal-backend python manage.py migrate` |
| Static manuell | `docker exec personal-backend python manage.py collectstatic --noinput` |
| Superuser | `docker exec -it personal-backend python manage.py createsuperuser` |

## 9. Tägliches Backup (Cron)

`backup.sh` sichert DB-Dump (`db_*.sql.gz`) **und** Rechnungs-PDFs
(`invoices_*.tar.gz`) nach `~/apps/personal/backups` (Aufbewahrung 30 Tage).

Cron (z. B. täglich 02:30):
```bash
crontab -e
30 2 * * * cd /home/mignon/apps/personal && ./scripts/backup.sh >> logs/backup.log 2>&1
```

Restore (Beispiel):
```bash
gunzip -c backups/db_YYYYMMDD_HHMMSS.sql.gz | \
  docker exec -i personal-postgres psql -U personal_user -d personal_db
tar -xzf backups/invoices_YYYYMMDD_HHMMSS.tar.gz -C storage
```

## 10. Logs prüfen

- App-Container: `./scripts/logs.sh backend` (Gunicorn/Django), `logs.sh frontend`, `logs.sh postgres`
- Django-Datei-Log: `~/apps/personal/logs/backend.log`
- Nginx: `~/apps/personal/logs/nginx-access.log`, `nginx-error.log`

## 11. Konflikte mit `meinpflegeweg` vermeiden

- Eigener Ordner `~/apps/personal` (nichts in `~/apps/meinpflegeweg` anfassen).
- Eigene Container-/Volume-/Netz-Namen mit Präfix `personal-` / `personal_`.
- Eigene Host-Ports **8001/3001** (nur `127.0.0.1`) – prüfen, dass diese frei sind:
  `sudo ss -tlnp | grep -E ':8001|:3001'`. Falls belegt, in `docker-compose.yml`
  und `nginx/personal.meinpflegeweg.com.conf` auf freie Ports ändern.
- Eigene DB `personal_db` im eigenen Container (kein Zugriff auf andere DBs).
- Eigener Nginx-Site-Block, eigenes Zertifikat nur für die Subdomain.
- Eigene Static-/Media-/PDF-/Log-/Backup-Ordner unter `storage/` bzw. `logs/`, `backups/`.

## 12. Verifikations-Checkliste

```bash
# HTTPS erreichbar
curl -I https://personal.meinpflegeweg.com            # 200/301, gültiges Zertifikat
curl -s https://personal.meinpflegeweg.com/api/health/ # {"status":"ok",...}

# Container laufen
docker compose -p personal ps                          # 3x Up (postgres healthy)

# DB ist separat
docker exec personal-postgres psql -U personal_user -d personal_db -c "\l"

# PDFs separat gespeichert
docker exec personal-backend ls -la /app/storage/invoices

# SMTP gesetzt
docker exec personal-backend printenv | grep EMAIL_

# Alte App unberührt
curl -I https://meinpflegeweg.com                      # weiterhin erreichbar
```

Manuell:
- [ ] `https://personal.meinpflegeweg.com` lädt das Frontend
- [ ] Login über `/api/auth/token/` funktioniert
- [ ] Django-Admin unter `/admin/` erreichbar
- [ ] Rechnungs-PDF (`/api/invoices/{id}/pdf/`) wird erzeugt und liegt in `storage/invoices`
- [ ] `meinpflegeweg.com` funktioniert unverändert
