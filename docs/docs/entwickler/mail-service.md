# Mail-Service (LLARS)

Der LLARS-Mail-Service verschickt transaktionale E-Mails (Willkommen,
Passwort-Reset) und liefert die Absender-/Reply-To-Logik für Recruiting-
Einladungen. Code: `app/services/email_service.py`. Versand läuft über
**Brevo** (SMTP für App-Mails, Transaktions-API für Einladungen).

## Mail-Typen im Überblick

| Mail-Typ | Wer löst aus | Absender (From) | Versandweg |
|----------|--------------|-----------------|------------|
| **Willkommen** | App, automatisch bei Referral-Registrierung/-Redeem mit E-Mail (`send_registration_confirmation`) | `team@llars.e-beratungsinstitut.de` | `email_service` → Brevo-SMTP |
| **IJCAI-Demo-Willkommen** | App, automatisch bei Signup über `/join/ijcai` (englisch, `send_ijcai_welcome`) | `team@llars.e-beratungsinstitut.de` | `email_service` → Brevo-SMTP |
| **Passwort-Reset** | App, „Passwort vergessen?" / Admin-Button / `email`-Mode-Wiedereinstieg | `noreply@llars.e-beratungsinstitut.de` | `email_service` → Brevo-SMTP |
| **Einladung (Recruiting)** | Admin Mail-Center *oder* manuell | `team@llars.e-beratungsinstitut.de` | Brevo-**API** vom Server (`curl -4`) |

**Reply-To + Kontaktadresse überall:** `llars@e-beratungsinstitut.de` (echtes
Weiterleitungs-Postfach auf der Root-Domain). Antworten landen also auch bei
`noreply`-Mails bei uns.

## Absender-/Reply-To-Logik

In `app/services/email_service.py` (env-überschreibbar, zur Laufzeit gelesen):

| Funktion | Default | Env-Override |
|----------|---------|--------------|
| `_from_notify()` (`:65`) | `team@llars.e-beratungsinstitut.de` | `MAIL_FROM_NOTIFY` |
| `_from_noreply()` (`:70`) | `noreply@llars.e-beratungsinstitut.de` | `MAIL_FROM_NOREPLY` |
| `_reply_to_addr()` (`:75`) | `llars@e-beratungsinstitut.de` | `MAIL_REPLY_TO` |
| `_resolve_from()` (`:51`) | hängt Display-Name (`SMTP_FROM_NAME`) an | `SMTP_FROM` / `SMTP_USERNAME` |

- **Willkommen / IJCAI-Demo** nutzt `_from_notify()` + `_reply_to_addr()`
  (`send_registration_confirmation` / `send_ijcai_welcome`).
- **Reset** nutzt `_from_noreply()` + `_reply_to_addr()`
  (`send_password_reset`).

## Versand-Mechanik (App-Mails)

- **SMTP-Send:** `_send_sync()` (`:80`) baut eine `EmailMessage` mit
  Plain-Text + HTML-Alternative, setzt `Reply-To`, loggt Erfolg/Fehler.
  Konfiguration über `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`,
  `SMTP_PASSWORD`, `SMTP_USE_TLS`/`SMTP_USE_SSL`.
- **Fire-and-forget:** `send_async()` (`:137`) startet den Versand in einem
  Daemon-Thread — blockiert die Anfrage nie und wirft nie.
- **Nicht zustellbare Adressen werden übersprungen:** `_is_real_inbox()`
  (`:162`) filtert leere Adressen und synthetische `…@noemail.invalid`-Adressen
  (für anonyme, E-Mail-lose Referral-Signups vergeben).
- **Konfig-Check:** `_is_configured()` (`:44`) — ohne `SMTP_HOST` (+ `SMTP_FROM`
  oder `SMTP_USERNAME`) wird der Versand still übersprungen (geloggt).

## Wodurch App-Mails getriggert werden

| Mail | Auslöser (Code) |
|------|-----------------|
| Willkommen | Referral-Registrierung/-Redeem mit E-Mail: `app/routes/referral/referral_routes.py` (`send_registration_confirmation`) |
| IJCAI-Demo-Willkommen | Signup über `/join/ijcai`: `app/routes/referral/referral_routes.py` (`send_ijcai_welcome`, englisch) |
| Reset (User) | „Passwort vergessen?": `app/routes/auth/password_reset_routes.py` (`send_password_reset`) |
| Reset (Admin) | Admin-Button: `app/routes/users/user_admin_routes.py` (`send_password_reset`) |
| Reset (email-Mode-Wiedereinstieg) | Bekannte E-Mail auf `email`-Mode-Link: einmaliger Anmelde-Link (`_send_referral_signin_link`) |

Beide laufen rein durch Nutzer-/Admin-Aktion; kein periodischer Versand, kein
Hintergrund-Job.

## Provider & harte Regeln (Brevo)

- **Authentifizierte Sende-Domain:** `llars.e-beratungsinstitut.de` (Subdomain,
  DKIM-signiert). **Nur von hier sauber senden** — Root- oder TH-Domain landet
  im Spam.
- **IP-Allowlist (harte Regel):** Brevo erlaubt API **und** SMTP nur von der
  **Server-IPv4**. Vom Laptop oder über IPv6 → `401 unrecognised IP`. → **Jeder
  Versand läuft über den Server, IPv4 erzwungen** (`curl -4`).
- **From = reine Sende-Adresse**, kein Postfach/MX. Empfang/Antworten nur über
  die Reply-To-Adresse.
- **.env-Werte mit Leerzeichen quoten** (z. B. `SMTP_FROM_NAME="…"`), sonst
  bricht der Prod-Smoke-Test beim `source` der .env (→ Deploy-Rollback).

Vollständige Brevo-/DNS-/Versand-Details inkl. Einladungs-Versand:
`MAIL_RUNBOOK.md` (Repo `EMNLP2026`).

## Einladungs-Mails (Recruiting)

Recruiting-Einladungen werden **nicht** vom Mail-Service verschickt, sondern als
gebrandetes HTML über die **Brevo-Transaktions-API vom Server** (ein Empfänger
pro Call). Absender/Reply-To wie oben; pro Recruiting-Quelle ein eigenes
Template mit eigenem Join-Link (Quellen-Tracking). Siehe
[Human-Studies-Playbook §5](../human_studies/playbook.md#5-einladungsmail-branden-versenden)
und `MAIL_RUNBOOK.md` (EMNLP2026).

---

## Admin Mail-Center

Das **Admin Mail-Center** (UI + `MailCenterService`,
`app/services/mail/mail_center_service.py`) versendet gebrandete Einladungen und
Ankündigungen pro Referral-Link direkt aus LLARS:

- **Empfänger auflösen** aus Referral-Link, Szenario-Rolle, System-Rolle oder
  expliziter Username-/Adressliste (`resolve_recipients`).
- **Versand** (`send_invitations` / `send_announcement`) über `email_service` →
  Brevo; pro `(link, email)` wird eine **Einladungs-Zeile** (`referral_invitation`)
  gespeichert (eine offene Einladung pro Link+E-Mail).
- **Auto-Match:** Registriert sich jemand später mit einer eingeladenen E-Mail,
  flippt die Einladung auf *accepted*
  (`match_invitation_on_registration`, aus dem Referral-`/register`- und
  `/redeem`-Flow aufgerufen).
- **Audit/Statistik:** `query_log`, `link_invitation_stats`,
  `record_engagement_event`.

Synthetische `…@noemail.invalid`-Adressen werden beim Auflösen verworfen
(`_is_synthetic_or_blank`). App-Mails (Willkommen/Reset) laufen weiterhin direkt
über `email_service`.
