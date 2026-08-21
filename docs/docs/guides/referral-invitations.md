# Referral- & Einladungssystem

Das Referral-System erzeugt teilbare Einladungslinks (`/join/<slug>`), über die
sich Teilnehmende selbst registrieren und automatisch in die richtigen Szenarien
eingeschrieben werden. Es ist die Grundlage für Recruiting in Studien und für
Konferenz-Demos (z. B. den [IJCAI-Demo-Link](../human_studies/ijcai-demo.md)).

Code: `app/db/models/referral.py`, `app/services/referral_service.py`,
`app/routes/referral/referral_routes.py`.

---

## Aufbau

```
ReferralCampaign  (Kampagne, z. B. "KI-Konferenz 2026")
└── ReferralLink   (einzelner Einladungslink, eigener Slug + QR)
    └── ReferralRegistration  (eine Zeile pro Registrierung, Username-eindeutig)
```

- **Kampagne** gruppiert Links unter einem Thema und kann Start-/Enddatum sowie
  ein globales Registrierungslimit tragen. Status: `draft`, `active`, `paused`,
  `expired`, `archived` — ein Link funktioniert nur, wenn seine Kampagne `active`
  ist.
- **Link** hat einen automatisch erzeugten `code` und optional einen lesbaren
  `slug` (`/join/ki-konferenz-2026`). Jeder Link kann eigene Nutzungslimits,
  ein Ablaufdatum, eine zuzuweisende Rolle und Auto-Enroll-Ziele tragen.

---

## Signup-Modus pro Link

Jeder Link hat einen `signup_mode`, der bestimmt, wie viel das Registrierungs-
formular abfragt. So lässt sich die Hürde an die Zielgruppe anpassen:

| `signup_mode` | Formular | Account |
|---------------|----------|---------|
| `full` (Default) | Benutzername + Passwort (+ E-Mail je nach `collect_*`-Flags) | Vom Nutzer gewählt |
| `email` | Nur E-Mail | Username deterministisch aus E-Mail+Slug; passwortlos. Erneuter Zugang über denselben Link + E-Mail: das System schickt einen einmaligen Anmelde-Link |
| `instant` | Ein Tap, keine Eingabe | Anonymer Account, alles serverseitig generiert |

Feinsteuerung für den `full`-Modus über drei Flags am Link:

- `collect_email` — E-Mail-Feld anzeigen (Default `true`).
- `collect_email_optional` — wenn `collect_email=true`: Feld sichtbar, aber nicht
  erforderlich (leer ⇒ synthetische `…@noemail.invalid`-Adresse).
- `collect_display_name` — optionales Anzeigename-Feld (Default `true`).

!!! note "Sicherer Wiedereinstieg (`email`-Modus)"
    Da der Username deterministisch aus der E-Mail abgeleitet wird, darf eine
    *vorhandene* E-Mail beim erneuten Eintippen **kein** automatisches Login
    auslösen. Stattdessen verschickt der Server einen einmaligen Anmelde-Link
    (über den Passwort-Reset-Mechanismus) und antwortet neutral — der Account
    wird erst nach Klick auf den Link übernommen.

---

## Auto-Enroll in Szenarien

Ein Link kann Registrierte direkt in Szenarien einschreiben:

| Feld | Wirkung |
|------|---------|
| `target_scenario_id` | Einzel-Szenario, Rolle **Assessor** (Legacy) |
| `target_scenario_ids` | JSON-Liste — Registrierte werden in **alle** als **Assessor** eingeschrieben |
| `viewer_scenario_ids` | JSON-Liste — Registrierte erhalten **Viewer** (Read-only-Manager) auf diesen Szenarien |

Ein Szenario darf in beiden Listen stehen (Demo-Fall): die `ScenarioUsers`-Zeile
trägt dann `evaluation_role='assessor'` **und** `manager_role='viewer'`. Die
Einschreibung ist idempotent — eine bestehende Mitgliedschaft wird nie
überschrieben, auch nicht „hochgestuft".

**Redirect nach dem ersten Login** richtet sich nach der Anzahl der Szenarien,
in denen man Assessor ist:

- genau ein Szenario → direkt in `/scenarios/<id>/evaluate`
- mehrere Szenarien → Evaluation-Hub (`/evaluation`)
- keines → Startseite

---

## Wege, einem Link beizutreten

| Wer | Flow | Endpoint |
|-----|------|----------|
| Neue Person | `/join/<slug>` öffnen, registrieren | `POST /api/referral/register` |
| Bereits eingeloggte Person | Code im UI einlösen | `POST /api/referral/redeem` |

Der `redeem`-Pfad schreibt bestehende Nutzer zusätzlich in die Ziel-Szenarien
ein und ordnet sie der Kampagne zu — **ohne** ihre globale Rolle anzufassen.
(Würde die Link-Rolle hier angewandt, würde z. B. ein Researcher, der einen
Evaluator-Studiencode einlöst, stillschweigend herabgestuft.) Beide Pfade sind
idempotent.

---

## Sicherheit & Datenschutz

- **Rollen-Allowlist:** Da `/register` öffentlich ist und echte Accounts anlegt,
  darf ein Link nur `evaluator`, `researcher`, `chatbot_manager` oder `viewer`
  vergeben. `admin` ist ausgeschlossen und wird auf `evaluator` zurückgesetzt
  (`ALLOWED_REFERRAL_ROLES`).
- **IP-Anonymisierung:** In `referral_registrations` wird nie die volle IP
  gespeichert. Sie wird auf das Netzpräfix gekürzt (IPv4 → /24, IPv6 → /48).
- **Studien-Consent:** Scenario-gebundene oder als Studie erkannte Links
  erzwingen die DSGVO-Studieneinwilligung auf dem Formular; ein Audit-Datensatz
  (Consent-Version, Text-SHA-256, gehashte IP, Sprache) wird mitgeschrieben.
- **Rate-Limits** (zusätzlich zu den globalen Defaults, `app/main.py`):

  | Endpoint | Dev | Prod |
  |----------|-----|------|
  | `POST /register` | 60/h, 20/10 min | 20/h, 6/10 min |
  | `GET /validate` | 300/h | 120/h |

---

## Admin-UI (Mail-Center / Referrals)

Admin → Mail-Center / Referrals (`admin:referral:manage`):

- Kampagnen und Links anlegen, bearbeiten, deaktivieren, archivieren.
- Pro Link einen **QR-Code** anzeigen (Modal) und als **PNG / SVG / PDF**
  herunterladen — die direkte Vorlage für Plakate und Konferenz-Stände.
- **Funnel-Analytics:** Jeder Aufruf der `/join`-Seite zählt als „Click"
  (`click_count`), gegenübergestellt den Registrierungen ⇒ Conversion-Rate
  pro Link / Kampagne / systemweit.

### Wichtige Endpoints

| Endpoint | Methoden | Zweck |
|----------|----------|-------|
| `/api/referral/validate/<code_or_slug>` | GET | Public: Link prüfen + Formularform |
| `/api/referral/register` | POST | Public: Registrierung |
| `/api/referral/redeem` | POST | Eingeloggt: Code einlösen |
| `/api/referral/admin/campaigns` | GET/POST | Kampagnen |
| `/api/referral/admin/campaigns/:id` | GET/PUT/DELETE | Kampagne lesen/ändern/löschen |
| `/api/referral/admin/campaigns/:id/links` | GET/POST | Links einer Kampagne |
| `/api/referral/admin/links/:id` | GET/PUT/DELETE | Link verwalten |
| `/api/referral/admin/analytics/overview` | GET | Funnel-Overview |
| `/api/referral/admin/registrations` | GET | Registrierungen |

Referral-Links lassen sich auch programmatisch über die
[v1 Scenario API](api-v1-scenarios.md) verwalten.

---

## Verwandte Seiten

- [IJCAI-Demo](../human_studies/ijcai-demo.md) — ein QR, sieben Demo-Szenarien
- [Berechtigungssystem](permission-system.md) — Szenario-Rollen inkl. Viewer
- [Mail-Service](../entwickler/mail-service.md) — Willkommens-/Einladungs-Mails
