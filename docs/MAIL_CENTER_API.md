# Admin Mail-Center API

Auditierbares Versenden von Studien-**Einladungen** und **Announcements** plus
ein zentraler **Mail-Verlauf** (jede automatische *und* manuelle Mail wird
protokolliert). Ersetzt die früheren Ad-hoc-Skripte im Prod-Container.

Konzept: `.claude/plans/admin-mail-center-concept.md`.
Code: `app/services/email_service.py`, `app/services/mail/mail_center_service.py`,
`app/routes/admin/mail_admin_routes.py`, `app/db/models/email_log.py`.

## Authentifizierung & Berechtigung

**Nur Admin oder System-API-Key.** Jeder Endpoint ist mit
`@require_permission('feature:admin:mail')` gesichert. Dieser Decorator
akzeptiert **eines** von:

- **System Admin API Key** über den Header `X-API-Key` (gleiche Mechanik wie
  die `/api/v1/*`-Routen — ein gültiger Key umgeht die Per-User-Prüfung und
  agiert als `admin`). API-Keys über URL-Query werden **nicht** akzeptiert.
- **OIDC-User** (Authentik Bearer Token), der die Berechtigung
  `feature:admin:mail` hält — standardmäßig nur die Rolle `admin`.

Alle Fehler folgen dem `@handle_api_errors`-Schema (400 ValidationError,
404 NotFoundError, 401/403 Auth).

Basis-URL-Präfix: `/api` (Blueprint `data_bp`).

## Endpoints

### POST `/api/admin/mail/invite`
Versendet eine gebrandete Einladung (mit eingebettetem `/join/<slug>`-Link) an
jede Adresse und legt pro Empfänger eine `referral_invitation`-Zeile an
(`email_log` Typ `invitation`, `referral_link_id` gesetzt).

```json
{ "referral_link_id": 12, "recipients": ["a@x.com", "b@y.com"],
  "list_text": "c@z.com, d@z.com", "intro": "Optionaler Text" }
```
Antwort: `{ "success": true, "result": {sent, failed, skipped, requested, async, link_url}, "resolution": {count, skipped_invalid, skipped_duplicate, total_candidates} }`

### POST `/api/admin/mail/announce`
Versendet ein gebrandetes Announcement (freier Betreff + Markdown/Text-Body)
an einen aufgelösten Empfänger-Spec (`email_log` Typ `announcement`).

```json
{ "subject": "Update", "body": "**Markdown** erlaubt",
  "recipient_spec": { "emails": ["x@y.com"], "list_text": "...",
                      "referral_link_id": 12, "scenario_id": 492, "role": "assessor",
                      "role_name": "evaluator" } }
```

### POST `/api/admin/mail/preview`
Rendert die Mail **ohne** Versand und löst die Empfängerzahl auf.
`{"mode": "invitation"|"announcement", ...}` — für `invitation` zusätzlich
`referral_link_id` + `intro`; für `announcement` `subject` + `body`.
Antwort: `{ "success": true, "subject", "html", "text", "recipients": {...} }`.

### GET `/api/admin/mail/log`
Paginierter, filterbarer Mail-Verlauf.
Query: `type`, `recipient` (LIKE), `status`, `referral_link_id`,
`scenario_id`, `date_from`, `date_to` (ISO), `limit` (≤200), `offset`.
Antwort: `{ "success": true, "entries": [...], "total", "limit", "offset" }`.

### GET `/api/admin/referral/links/<id>/invitations`
Eingeladen/Angenommen/Offen-Funnel pro Link, inkl. ehrlichem
`registered_unmatched` (Registrierungen ohne E-Mail-Zuordnung — das
optionale E-Mail-Feld macht nicht jede Annahme matchbar).
Antwort: `{ "success": true, "stats": {invited, accepted, pending, total_registrations, registered_unmatched, invitations: [...]} }`.

## Empfänger-Resolver

`MailCenterService.resolve_recipients(spec)` kombiniert:

| Quelle | Spec-Feld | Herkunft der E-Mail |
|--------|-----------|---------------------|
| Einzeladressen | `emails[]` | direkt |
| Eingefügte/CSV-Liste | `list_text` | direkt (Komma/Semikolon/Whitespace getrennt) |
| Per Ref-Link | `referral_link_id` | `ReferralRegistration.metadata_json['email']` (LLARS-DB) |
| Per Szenario (+Rolle) | `scenario_id`, `role` | Authentik (`find_user` pro Username) |
| Per System-Rolle | `role_name` | Authentik (`find_user` pro Username) |

Dedup (case-insensitive), Format-Validierung, `@noemail.invalid` und leere
Adressen werden **übersprungen** (nie gesendet, nie gezählt).

## Datenschutz / Logging

- **Keine vollständigen Bodies.** `password_reset` enthält einen Token →
  es werden nur `mail_type`/`recipient`/`subject`/`status` geloggt, **kein**
  Body und **kein** Token (kein `meta`-Preview).
- `invitation`/`announcement` speichern optional einen ≤280-Zeichen
  Text-Preview in `meta_json` zum Wiedererkennen einer Kampagne.
- Status `skipped` (kein echtes Postfach) ist von `failed` getrennt, damit
  synthetische Referral-Signups die Fehlerrate nicht verfälschen.

## Versand-Skalierung

Kleine Listen (≤ `ASYNC_THRESHOLD = 25`) senden inline/blockierend → die UI
erhält ein wahrheitsgetreues `sent`/`failed`-Ergebnis pro Empfänger. Größere
Listen senden asynchron (fire-and-forget) und werden optimistisch als `sent`
geloggt. Ein echter Massen-Versand über eine Worker-Queue (`mail:outbox`) ist
bewusst **out of scope** (im Konzept dokumentiert).

## Annahme-Tracking

Bei Registrierung über einen Link (`referral_routes.register_via_referral`)
ruft die Route `MailCenterService.match_invitation_on_registration` auf:
liegt eine reale (nicht-synthetische) E-Mail vor und matcht eine offene
`referral_invitation(link, email)`, wird sie auf *accepted* gesetzt.
Registrierungen ohne/mit abweichender E-Mail bleiben **unmatched** und werden
in den Link-Stats transparent als `registered_unmatched` ausgewiesen.

## Migration

Tabellen `email_log` + `referral_invitation`:
`app/db/migrations/migrate_mail_center_tables.py` (idempotent,
`CREATE TABLE IF NOT EXISTS`). Läuft beim Start via
`migrate_mail_center()` in `app/main.py` und ist auch manuell ausführbar:

```bash
python -m app.db.migrations.migrate_mail_center_tables
```
