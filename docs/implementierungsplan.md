# Implementierungsplan

## Konzept-Erkenntnisse (aus `/concept`)

### Firmenstammdaten (Seed)
- **Mouvin Personal Dienstleistungs GmbH**, Rheinstrasse 15, 65185 Wiesbaden
- Tel. 01791449049, infos@mouvinpersonal.de
- USt-IdNr.: DE123456789
- IBAN: DE19 0000 0100 0000 0000 00, BIC: 000000XXX

### Rechnungslayout (aus `Rechnung_In Haus Mainblick.pdf`)
Feste Positionsstruktur der Rechnung:

| Nr. | Bezeichnung                   | Bezahlt (Std.) | Faktor (€)        | Betrag (€)              |
|-----|-------------------------------|----------------|-------------------|-------------------------|
| 1   | Netto Stunden ohne Pausen     | Σ bezahlte Std | Kundenstundensatz | Std × Satz              |
| 2   | Nachtarbeit Zuschlag 25 %     | Nacht-Std      | 25 % × Satz       | Std × Faktor            |
| 3   | Samstag Zuschlag 25 %         | Sa-Std         | 25 % × Satz       | Std × Faktor            |
| 4   | Sonntag Zuschlag 50 %         | So-Std         | 50 % × Satz       | Std × Faktor            |
| 5   | Feiertag Zuschlag 100 %       | Feiertag-Std   | 100 % × Satz      | Std × Faktor            |
| 6   | Fahrkosten                    | –              | –                 | Pauschale               |
|     | **Zwischensumme**             |                |                   | Σ 1–6                   |
|     | **Umsatzsteuer (19 %)**       |                |                   | Zwischensumme × 0,19    |
|     | **Gesamtbetrag Brutto**       |                |                   | Zwischensumme × 1,19    |

- **Rechnungsnummer-Format:** `RECH-{laufend}-{YYYYMMDD}`
- Beispiel verifiziert: Satz 49,00 €; Sa 25 % → 12,25 €; So 50 % → 24,50 €.

### Zuschlagslogik (bestätigt)
- **Faktor = Zuschlag-% × Kundenstundensatz** (nicht auf Lohn, sondern Kundenpreis).
- **Betrag = Zuschlagsstunden × Faktor**, additiv zur Grundstunde (kumuliert).
- Grundstunden-Position (Nr. 1) zählt **alle** bezahlten Stunden; Zuschlagspositionen
  zählen zusätzlich die Stunden im jeweiligen Fenster.

### Berechnungsbeispiele (handschriftlich, `image1`/`image6`) → Test-Fixtures
- Schicht über Mitternacht, Pause **einmal** abziehen (`-1 Pause`).
- Split in Fenster: Nacht / Samstag (ab 00:00) / Sonntag / Feiertag.
- Beispiel: Fr 20:30 → Sa 07:00, 1 h Pause = 9,5 bezahlte Std; Nacht- und Samstaganteil
  separat ausgewiesen. → als Unit-Test in Phase 6 hinterlegen.

### Schichtarten & Boni (Skizzen `image3`–`image5`)
- Schichtarten: **Frühdienst, Spätdienst, Nachtdienst**
- Boni-Auswahl: Weekend-, Nachtschicht-, Feiertags-, Spezieller Zuschlag
- Flow: Kunde → Mitarbeiter → Schichterfassung (Kalender) → Überblick → Rechnung
- Vorhandener Prototyp "Shift Management": Nav *Kundenliste · Mitarbeiterliste ·
  Schichtliste · Schichtzusammenfassung* + "Rechnung erstellen"-Button.

## Architektur-Entscheidungen
- **Greenfield** (kein Aufbau auf altem Prototyp).
- **Lokal zuerst**, Docker/VPS in Phase 10.
- PDF mit **WeasyPrint** (HTML/CSS-Template → 1:1-Nachbau des vorhandenen Layouts).
- Feiertage via **`holidays`**-Library (Hessen/RLP) + Admin-Override.
- Fahrkosten MVP: Entfernung pro Mitarbeiter-Kunde-Kombination gespeichert (stabil).

## Phasen
1. **Projektgrundlage** – Repo, Backend, Frontend, DB, env. ← aktuell
2. **Datenmodell** – User, EmployeeProfile, Customer, CustomerContract, SurchargeRule,
   TravelCostRule, Shift, ShiftCalculation, Invoice, InvoiceLine, AuditLog.
3. **Auth & Rollen** – JWT, Admin vs. Mitarbeiter (Queryset-Scoping).
4. **Admin-Stammdaten** – Kunden/Mitarbeiter/Verträge/Zuschläge/Fahrkosten.
5. **Schichterfassung** – Mitarbeiter-Dashboard, Schicht anlegen/absenden.
6. **Berechnungsengine** – Split, Pause, kumulierte Zuschläge, Fahrkosten, USt. + Tests.
7. **Admin-Prüfung** – Freigabe/Ablehnung, Korrektur, Audit-Log, Schichtzusammenfassung.
8. **Rechnungsmodul** – Gruppierung, Positionen 1–6, Doppelabrechnung verhindern.
9. **PDF-Rechnung** – WeasyPrint-Template, Nr.-Format, speichern/download.
10. **Deployment IONOS** – Docker, Nginx, Gunicorn, HTTPS, Backups, SMTP, Monitoring.
