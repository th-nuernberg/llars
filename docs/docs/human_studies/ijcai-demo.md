# IJCAI 2026 Demo

Die IJCAI-Demo ist ein Live-Stand-Szenario: Konferenzbesucher:innen scannen
**einen** QR-Code (`/join/ijcai`), bekommen sofort einen Demo-Account und sind
als Bewerter:in in **je einem geteilten Demo-Szenario pro Evaluationstyp**
eingeschrieben — plus Read-only-Viewer-Zugang, um die live aggregierte Analyse
über alle Teilnehmenden hinweg zu beobachten.

Seeder: `app/scripts/seed_ijcai_demo.py`. Begrüßungsmail (Englisch):
`app/services/email_service.py` → `render_ijcai_welcome` / `send_ijcai_welcome`.

---

## Konzept

- **Geteilte Szenarien (nicht pro Person):** Alle, die den QR scannen, bewerten
  dieselben 20 Items pro Typ. Dadurch zeigt die Scenario-Manager-Analyse live die
  Inter-Rater-Reliabilität über alle Teilnehmenden — die Kernaussage einer
  kollaborativen Evaluationsplattform.
- **Sieben Szenarien**, eines je Evaluationstyp: `rating`, `ranking`,
  `mail_rating`, `comparison`, `communication_comparison`, `authenticity`,
  `labeling`.
- **Inhalt auf Englisch** (internationales Publikum); das deutsche Original
  bleibt je Item in den Metadaten erhalten. Die Evaluations-**Konfiguration**
  (Aufgabe, Dimensionen, Buckets, Labels) ist vollständig zweisprachig (de/en)
  und folgt dem Sprach-Toggle.
- Besitzer-Account aller Szenarien: `ijcai_demo`.

---

## Seeden / neu seeden

Datensätze liegen unter `app/scripts/ijcai_demo/<typ>.json` (einer pro Typ).
Der Seeder ist **idempotent**: erneutes Ausführen verwendet bestehende Szenarien
weiter (Match über Name + Ersteller) und aktualisiert den Referral-Link in place
— nach jedem Deploy sicher ausführbar.

```bash
# Seeden (im laufenden Flask-Container, <color> = aktive Blue/Green-Farbe)
docker exec llars_flask_<color> python -m scripts.seed_ijcai_demo

# Komplett neu aufbauen (löscht + erstellt die 7 Szenarien neu)
docker exec llars_flask_<color> python -m scripts.seed_ijcai_demo --reset
```

Der Seeder gibt am Ende die `scenario_ids`, den `link_slug` (`ijcai`), den
`link_code` und die `join_url` aus.

**Link-Konfiguration**, die der Seeder setzt:

| Feld | Wert |
|------|------|
| `slug` | `ijcai` |
| `signup_mode` | `email` (Konferenz-Default: QR → E-Mail → drin) |
| `target_scenario_ids` | alle 7 Szenarien (Assessor) |
| `viewer_scenario_ids` | alle 7 Szenarien (Read-only-Viewer) |
| `role_name` | `ijcai_reviewer` |
| `expires_at` | `2026-08-29 23:59:59` (siehe [Lebensende](#lebensende-der-demo)) |

---

## Wie Teilnehmende beitreten

1. **QR scannen** → `/join/ijcai`.
2. **E-Mail eingeben** (`signup_mode='email'`): Account wird passwortlos
   angelegt, Username deterministisch aus E-Mail + Slug abgeleitet, und die
   Person wird automatisch eingeloggt.
3. **Englische Begrüßungsmail** (`send_ijcai_welcome`) bestätigt den Account und
   verlinkt den Evaluation-Hub. Sie unterscheidet sich bewusst von der deutschen
   „Kann KI Beratung?"-Studienmail (Produkt-Demo statt Studie).
4. **Redirect:** Da die Person Assessor in mehreren Szenarien ist, landet sie im
   Evaluation-Hub (`/evaluation`) und wählt einen Evaluationstyp.
5. **Wiederkommen:** Denselben QR scannen, dieselbe E-Mail eingeben → das System
   schickt einen einmaligen Anmelde-Link (kein Passwort nötig).

> Die Auto-Enroll-, Signup-Mode- und Redirect-Mechanik ist allgemein und im
> [Referral- & Einladungssystem](../guides/referral-invitations.md) beschrieben.

---

## Lebensende der Demo

Die Demo hat ein definiertes Ende — in zwei voneinander unabhängigen Stufen:

**1. Der Link läuft ab: 29.08.2026, 23:59:59 (Europe/Berlin).**
Die Konferenz endet am 22.08.2026; die Woche Gnadenfrist deckt späte Scans
gedruckter QR-Codes ab. Danach lehnt `ReferralService.validate_link` den Link ab,
es sind also **keine neuen Registrierungen** mehr möglich. Bereits bestehende
Accounts bleiben davon unberührt. Das Datum steht als Konstante
`LINK_EXPIRES_AT` in `app/scripts/seed_ijcai_demo.py` und wird bei **jedem**
Seeder-Lauf neu in die DB geschrieben (Config-as-Code): Datum dort ändern und neu
seeden — eine manuelle DB-Änderung wäre beim nächsten Lauf wieder überschrieben.

**2. Accounts verlieren 7 Tage nach Registrierung alle Berechtigungen.**
`expire_ijcai_accounts` in `app/scripts/demo_cleanup.py` ersetzt bei betroffenen
Accounts sämtliche Rollen durch die leere Rolle `demo_expired` (null
Berechtigungen) und archiviert ihre Szenario-Mitgliedschaften.

- **Login bleibt möglich** — `is_active` wird nicht angefasst, nichts wird
  gelöscht. Nutzbar ist danach aber nichts mehr: keine KI, keine Generierung,
  kein Prompt Engineering, keine Evaluation (Deny-by-Default).
- **Warum eine leere Rolle statt gar keiner Rolle?**
  `auth.decorators._ensure_default_evaluator_role` weist jedem User **ohne**
  `user_roles`-Zeile beim nächsten Login automatisch wieder `evaluator` zu. Ein
  rollenloser Account würde sich also selbst reaktivieren. Deshalb wird zuerst
  `demo_expired` zugewiesen und erst danach alles andere entfernt — der Account
  hat zu keinem Zeitpunkt null Rollen.
- **Doppelter Schutzzaun:** Betroffen ist nur, wer *sowohl* das automatisch
  vergebene Username-Muster `demo-ijcai-*` trägt *als auch* eine Registrierung
  über den `ijcai`-Link hat. Bestandsnutzer:innen, die den Code lediglich
  eingelöst haben, werden nie angefasst.
- **Idempotent:** Bereits abgelaufene Accounts werden nur gezählt, nicht erneut
  bearbeitet; ein fehlerhafter Account bricht den Lauf nicht ab.

**Ausführung:** täglich um 03:30 über den systemd-Timer `llars-cleanup.timer`
(→ `scripts/server/llars_cleanup.sh`, Schritt 6) im aktiven Blue/Green-Flask-
Container. Zusätzlich läuft der Job nach jedem Nightly-Deploy als CI-Job
`maintenance:demo-cleanup`. Manuell:

```bash
docker exec llars_flask_<color> python -m scripts.demo_cleanup
```
