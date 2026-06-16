# Mouvin Personal – Schicht- & Rechnungssystem

Web-App für die **Mouvin Personal Dienstleistungs GmbH** zur digitalen Schichterfassung,
automatischen Berechnung (Stunden, Pausen, kumulierte Zuschläge, Fahrkosten, USt 19 %)
und PDF-Rechnungserstellung pro Kunde und Zeitraum.

Zielgröße: ~50 Pflegekräfte, ~15 Kunden (Hessen / Rheinland-Pfalz), wöchentliche & monatliche Rechnungen.

## Stack

| Schicht      | Technologie                          |
|--------------|--------------------------------------|
| Backend      | Django + Django REST Framework       |
| Frontend     | Next.js (TypeScript, Tailwind)       |
| Datenbank    | PostgreSQL                           |
| PDF          | WeasyPrint (HTML → PDF, serverseitig)|
| Auth         | E-Mail + Passwort (JWT)              |
| Hosting      | IONOS VPS (Phase 10)                 |

## Repo-Struktur

```
backend/    Django-Projekt (API, Berechnungsengine, PDF)
frontend/   Next.js-App (Admin- & Mitarbeiter-Oberfläche)
deploy/     Docker / Nginx / VPS-Konfiguration (ab Phase 10)
docs/       Konzept, Entscheidungen, Datenmodell
concept/    Ursprüngliche Skizzen, Beispielrechnung, Berechnungsbeispiele
```

## Lokale Entwicklung

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env         # Werte anpassen
python manage.py migrate
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

## Implementierungs-Phasen

1. **Projektgrundlage** ← aktuell
2. Datenmodell
3. Authentifizierung & Rollen
4. Admin-Stammdaten
5. Schichterfassung
6. Berechnungsengine
7. Admin-Prüfung
8. Rechnungsmodul
9. PDF-Rechnung
10. Deployment (IONOS VPS)

Details siehe [`docs/implementierungsplan.md`](docs/implementierungsplan.md).


## Produktion: kleine Betriebsnotizen

### Systemd-Restart

Die produktiven Dienste laufen als `personal-backend.service` und `personal-frontend.service`.
Für Deploys sollte der Benutzer `mignon` die begrenzten sudo-Rechte aus
`deploy/sudoers-personal-deploy` erhalten. Danach kann neu gestartet werden mit:

```bash
./scripts/restart-prod.sh
```

### Domain

Die einzige (kanonische) URL ist `https://personal.meinpflegeweg.com`. Die
`www.`-Variante wird bewusst **nicht** genutzt (kein DNS-Eintrag, kein Zertifikat)
– bei einer Subdomain ist `www.` unüblich und unnötig.

Die nginx-Vorlagen liegen unter `deploy/nginx-personal.meinpflegeweg.com.conf` und
`nginx/personal.meinpflegeweg.com.conf`.
