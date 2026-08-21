# Playbook — eine Human Study in LLARS durchführen

Dieser Playbook beschreibt den **generischen, wiederverwendbaren Ablauf**, mit
dem wir eine Human Study in LLARS aufsetzen und betreiben — von der
Studienkonfiguration bis zum Recruiting-Tracking. Er ist **studienunabhängig**
formuliert; als durchgehendes Beispiel dient die erste so gefahrene Studie,
[„Kann KI Beratung?"](KannKIBeratung/index.md).

Anforderungen und Annotationen aus der Fachseite werden hier neutral als
**fachliche Anmerkungen aus den Sozialwissenschaften** geführt
(siehe [Annotations-Audit](KannKIBeratung/annotations-audit.md)).

---

## Überblick — der Ablauf in 8 Schritten

```
1. Studientyp + Eval-Config festlegen   (Szenario-Typ, Aufgabentexte, Frage)
2. Daten/Items aufbereiten + Szenario anlegen
3. Referral-Links pro Recruiting-Quelle (Quellen-Tracking)
4. Consent / Anonymität / optionale E-Mail konfigurieren
5. Einladungsmail branden + (vom Server) versenden
6. Pro-N-Feedback (Gamification / Auswertungs-Popup)
7. Deploy (Blue/Green) — Textänderungen erfordern Szenario-Neuanlage
8. Recruiting- & Acceptance-Tracking auswerten
```

---

## 1 · Studientyp + Eval-Config festlegen

LLARS unterstützt mehrere Evaluationstypen (`ranking`, `rating`, `mail_rating`,
`comparison`, `communication_comparison`, `authenticity`, `labeling`). Für eine
Human Study wählt man den Typ, der zur Forschungsfrage passt, und definiert die
`eval_config` (Aufgabentexte, Bewertungsfrage, Skalen/Buckets, Optionen).

Wiederkehrende Bausteine einer `eval_config` für Studien:

| Feld | Zweck |
|------|-------|
| `welcome_markdown` (DE/EN) | **Startseiten-Briefing** (Aufgabe 1) — wird über den Item-Kacheln gerendert. |
| `task_description_markdown` (DE/EN) | **Pro-Fall-Aufgabentext** (Aufgabe 2) — wird im Bewertungs-Interface gerendert. |
| `question` (DE/EN) | Die Bewertungsfrage pro Item. |
| `item_header_template` | Kopfzeile pro Item (z. B. `{{channel_label}}`). |
| `gamification_*`, `progressive_reveal` | Feedback-/Freischalt-Logik (siehe Schritt 6). |

> **Wichtig:** Die `eval_config` eines Szenarios ist über die v1-API **nicht
> patchbar**. Spätere Text- oder Konfig-Änderungen erfordern eine **Neuanlage**
> des Szenarios (der Referral-Slug zeigt automatisch auf das neue Szenario, die
> Join-URLs bleiben stabil — siehe Schritt 7).

**Rendering in LLARS:**

- Startseiten-Briefing: `llars-frontend/src/views/Evaluation/EvaluationItemsOverview.vue`
  (Briefing-Banner, `taskMarkdown` → `LMarkdownContent`).
- Pro-Fall-Aufgabe (Comparison): `llars-frontend/src/views/Evaluation/interfaces/ComparisonInterface.vue`
  (`task_description_markdown` / Fallback-Frage).

---

## 2 · Daten/Items aufbereiten + Szenario anlegen

Items werden als JSON aufbereitet (ein Item = Kontext + zu bewertende Features)
und über die **v1-API** als Szenario angelegt:

```
POST /api/v1/scenarios          # Szenario + Items + erster Referral-Link
GET  /api/v1/scenarios/<id>     # Verifikation
```

Authentifizierung über den **System-Admin-API-Key** im `X-API-Key`-Header.
Studienkonfiguration, Item-Reihenfolge und Build sind studienspezifisch und
liegen typischerweise im jeweiligen Forschungs-Repo (Build-Skripte, Payload-Bau).

---

## 3 · Referral-Links pro Recruiting-Quelle (Quellen-Tracking)

Pro Recruiting-Quelle (Organisation, Verteiler, Kanal) wird **ein eigener
Referral-Slug** angelegt. Jede Registrierung wird der Quelle zugeordnet, über
deren Link sie kam → man sieht, woher die Rater:innen stammen.

```
POST /api/v1/scenarios/<id>/referral-link
  { "slug": "...", "label": "...", "role_name": "evaluator",
    "campaign_name": "...", "auto_enroll": true,
    "collect_email": false, "collect_display_name": false }
```

- **Idempotent per Slug:** erneutes Aufrufen patcht den Link (z. B. um
  `collect_email` umzuschalten), ohne das Szenario neu anzulegen.
- Join-URL = `https://<host>/join/<slug>`.
- Validierung: `GET /api/referral/validate/<slug>`.
- Backend: `app/routes/referral/referral_routes.py`.

> **Regel:** Niemals denselben Link für alle Quellen verschicken — sonst geht das
> Quellen-Tracking verloren. Weiterleiten **innerhalb** derselben Quelle ist ok.

---

## 4 · Consent / Anonymität / optionale E-Mail

Der Join-/Registrierungs-Flow lässt sich pro Referral-Link feinjustieren
(`app/routes/referral/referral_routes.py`, Frontend
`llars-frontend/src/views/Register.vue`):

| Einstellung | Wirkung |
|-------------|---------|
| `collect_email=false` | E-Mail-Feld ausgeblendet → **anonymer** Account (nur Username + Passwort). Es wird eine synthetische `…@noemail.invalid`-Adresse gesetzt (nicht zustellbar). |
| `collect_email=true` + `collect_email_optional=true` | E-Mail-Feld sichtbar, aber optional. |
| `collect_email=true` + `collect_email_optional=false` | E-Mail-Feld sichtbar und Pflicht (Legacy-Verhalten). |
| `collect_display_name=false` | Kein Anzeigename. |
| Study-Link | Blendet einen **Consent-Block** (Datenschutz-/Studieneinwilligung) im Register-Formular ein (`useStudyConsent`, Version + Timestamp; Infoseite `/study-consent`). |

So lassen sich anonyme, DSGVO-konforme Teilnahmen mit optionaler E-Mail
realisieren — die E-Mail wird nur dann benötigt, wenn App-Mails (Willkommen,
Reset) zugestellt werden sollen.

---

## 5 · Einladungsmail branden + versenden

Recruiting-Einladungen werden als **gebrandete HTML-Mail** verschickt. In LLARS
gibt es zwei Mailwege (Details: [Mail-Service](../entwickler/mail-service.md)
und das `MAIL_RUNBOOK.md` im Forschungs-Repo):

- **App-Mails** (Willkommen / Passwort-Reset) — automatisch durch Nutzeraktion,
  über `app/services/email_service.py` → Brevo-SMTP.
- **Einladungs-Mails** (Recruiting) — **manuell**, als gebrandetes HTML über die
  **Brevo-Transaktions-API** (ein Empfänger pro Call).

**Harte Versandregeln (gelten für beide Wege):**

1. **Senden nur vom Server, über IPv4** (`curl -4`). Brevo erlaubt API/SMTP nur
   von der Server-IPv4 — Laptop oder IPv6 → `401 unrecognised IP`.
2. **Nur von der authentifizierten (DKIM-)Sende-Subdomain** senden, sonst Spam.
3. **From-Adressen sind reine Sende-Adressen** (kein Postfach). Antworten laufen
   über die **Reply-To-Adresse**.
4. Pro Recruiting-Quelle die passende Template-Variante mit dem **richtigen
   Quellen-Link** versenden (Tracking, siehe Schritt 3).

> Branding/Wortlaut der Einladung liegen als Template + Generator im
> Forschungs-Repo; hier wird der Wortlaut zentral gepflegt, nicht in den
> generierten HTMLs.

---

## 6 · Pro-N-Feedback (Gamification / Auswertungs-Popup)

Studien profitieren von Zwischen-Feedback, um Rater:innen zu motivieren und
Bearbeitungsstrecken zu strukturieren. LLARS unterstützt für Comparison-Studien
ein **Auswertungs-Popup nach je N abgeschlossenen Fällen** plus **progressives
Freischalten** weiterer Fälle:

| Config-Feld | Wirkung |
|-------------|---------|
| `gamification_enabled` | Schaltet das Reward-/Auswertungs-Popup ein. |
| `gamification_first_milestone` | Erstes Popup nach N abgeschlossenen Fällen. |
| `gamification_recurring_milestone` | Danach alle N weiteren Fälle erneut. |
| `progressive_reveal` | Schaltet nach jedem Milestone weitere Fälle frei. |

Das Popup zeigt die bisherigen Präferenz-Anteile (studienspezifische Achsen,
z. B. „bevorzugt menschlich vs. KI"). Implementierung:

- `llars-frontend/src/composables/useComparisonEvaluation.js` (Milestone-Logik,
  `milestoneEvent`).
- `llars-frontend/src/views/Evaluation/interfaces/ComparisonRewardDialog.vue`
  (Popup-UI).
- `app/services/evaluation/comparison_preference_stats_service.py` (Aggregation
  der Präferenzen, Endpoint `GET /api/evaluation/session/:scenarioId/comparison/preferences`).

Zusätzlich gibt es eine optionale **einmalige Bestätigung nach der ersten
gespeicherten Bewertung** (siehe Annotations-Audit der Beispielstudie), die
neue Teilnehmer:innen zum „Weiter"-Button führt.

---

## 7 · Deploy (Blue/Green) — und der Neuanlage-Hinweis

Code- und Mail-Änderungen gehen über den normalen LLARS-Deploy live
(Blue/Green, siehe Projekt-Doku zu CI/CD und Deployment). Wichtig für Studien:

- **`eval_config`-Änderungen** (Aufgabentexte, Frage, Milestones) sind **nicht
  patchbar** → Szenario **neu anlegen**. Der Referral-Slug zeigt automatisch auf
  das neue Szenario, die Join-URLs bleiben stabil. Beim Re-Deploy: erst das
  **neue** Szenario anlegen (Slug re-pointet), dann das alte löschen, damit der
  Link nie bricht.
- **Test-Accounts** werden nur als bestätigter Müll (0 Bewertungen) gelöscht;
  die Live-DB ist geteilt — niemals echte Nutzer:innen oder CI-Accounts
  entfernen.

---

## 8 · Recruiting- & Acceptance-Tracking

- **Quelle pro Registrierung:** ergibt sich aus dem Referral-Slug
  (`referral_registrations`, verknüpft mit `referral_links`).
- **Acceptance/Aktivität:** abgeschlossene Fälle pro Nutzer:in
  (Comparison-Votes liegen in `item_comparison_evaluations`).
- **Demografie:** optionaler, einmaliger Demografie-Survey beim ersten Login
  (`UserDemographics`, `app/db/models/user_demographics.py`) — für
  Kohortenanalysen.

So lässt sich auswerten, über welche Quelle wie viele Rater:innen kamen und wie
aktiv sie waren.

---

## Checkliste (Kurzform)

- [ ] Studientyp + `eval_config` (Aufgabentexte DE/EN, Frage, Milestones) fest.
- [ ] Items aufbereitet, Szenario via `POST /api/v1/scenarios` angelegt.
- [ ] Pro Quelle ein Referral-Slug (`auto_enroll`, `role_name`, Consent/E-Mail).
- [ ] Consent/Anonymität/optionale E-Mail je Link konfiguriert.
- [ ] Einladungsmail gebrandet, vom Server (IPv4) versendet, richtiger Link je Quelle.
- [ ] Pro-N-Feedback (Gamification/Popup) konfiguriert und geprüft.
- [ ] Deploy via Blue/Green; bei Textänderung Szenario neu angelegt.
- [ ] Recruiting-/Acceptance-Tracking + Demografie ausgewertet.
