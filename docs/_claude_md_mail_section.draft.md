# DRAFT — vorgeschlagener CLAUDE.md-Abschnitt „Mail-Versand"

> Dies ist ein **Entwurf** zum Einfügen in `CLAUDE.md` (NICHT automatisch
> übernommen). Die Mail-Center-API-Teile sind als TODO markiert (separater Agent
> baut sie). Vor dem Einfügen prüfen/aktualisieren.

---

## Mail-Versand

LLARS versendet transaktionale Mails über **Brevo**. Drei Versandarten:

1. **Automatisch (App):** Willkommens- und Passwort-Reset-Mails verschickt der
   `email_service` automatisch bei Nutzeraktionen (Registrierung über
   Referral-Link mit E-Mail, „Passwort vergessen?", Admin-Reset). Fire-and-forget,
   blockiert die Anfrage nie. Code: `app/services/email_service.py`.

2. **Als Admin (UI):** *(TODO — Admin Mail-Center)* — eine Admin-Oberfläche zum
   manuellen Versand (inkl. Recruiting-Einladungen) direkt aus LLARS.

3. **Via API (API-Key):** *(TODO — Mail-Center-API)* — programmatischer Versand
   über die Mail-Center-Endpoints, authentifiziert per System-API-Key.

### Mail-Typen & Absender

| Typ | Auslöser | From | Weg |
|-----|----------|------|-----|
| Willkommen | App, bei Registrierung | `team@llars.e-beratungsinstitut.de` | Brevo-SMTP |
| Passwort-Reset | App, „Passwort vergessen?" / Admin | `noreply@llars.e-beratungsinstitut.de` | Brevo-SMTP |
| Einladung (Recruiting) | manuell (kein App-Trigger) | `team@llars.e-beratungsinstitut.de` | Brevo-API (Server, IPv4) |

**Reply-To/Kontakt überall:** `llars@e-beratungsinstitut.de`.

### Harte Regeln

- **Senden nur vom Server, IPv4** (`curl -4`) — Brevo blockt andere IPs (401).
- **Nur von der DKIM-authentifizierten Subdomain** `llars.e-beratungsinstitut.de`
  senden (sonst Spam).
- **From = reine Sende-Adresse** (kein Postfach); Empfang/Antworten nur über
  Reply-To.
- **`.env`-Werte mit Leerzeichen quoten** (z. B. `SMTP_FROM_NAME="…"`), sonst
  Prod-Smoke-Rollback.
- **Pro Recruiting-Quelle eigener Link** in der Einladung (Quellen-Tracking).

### Env (Auszug)

`MAIL_FROM_NOTIFY`, `MAIL_FROM_NOREPLY`, `MAIL_REPLY_TO` (überschreiben die
Defaults); `SMTP_HOST/PORT/USERNAME/PASSWORD`, `SMTP_USE_TLS`, `SMTP_FROM_NAME`,
`LLARS_PUBLIC_URL`; `BREVO_API_KEY` (Einladungs-API).

### Doku

- Entwickler-Doku: `docs/docs/entwickler/mail-service.md`.
- Vollständiges Runbook (Brevo/DNS/Versand): `MAIL_RUNBOOK.md` im Repo `EMNLP2026`.
- Human-Studies-Recruiting-Mails: `docs/docs/human_studies/playbook.md` §5.

### TODO — Mail-Center (UI + API)

> Ein **Admin Mail-Center** (UI) samt **API** ist in Arbeit (separater Agent).
> Sobald final, hier ergänzen: Endpoints (Pfade, Auth via API-Key, Payload),
> UI-Einstieg, Verhältnis zu `email_service`. **Bis dahin keine Endpoints
> erfinden.**
