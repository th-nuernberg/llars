# Mail Service (LLARS)

The LLARS mail service sends transactional emails (welcome,
password reset) and provides the sender/reply-to logic for recruiting
invitations. Code: `app/services/email_service.py`. Sending runs through
**Brevo** (SMTP for app mails, transactional API for invitations).

## Mail Types at a Glance

| Mail Type | Who Triggers | Sender (From) | Delivery Path |
|----------|--------------|-----------------|------------|
| **Welcome** | App, automatically on referral registration/redeem with email (`send_registration_confirmation`) | `team@llars.e-beratungsinstitut.de` | `email_service` → Brevo SMTP |
| **IJCAI Demo Welcome** | App, automatically on signup via `/join/ijcai` (English, `send_ijcai_welcome`) | `team@llars.e-beratungsinstitut.de` | `email_service` → Brevo SMTP |
| **Password Reset** | App, "Forgot password?" / admin button / `email`-mode re-entry | `noreply@llars.e-beratungsinstitut.de` | `email_service` → Brevo SMTP |
| **Invitation (Recruiting)** | Admin Mail Center *or* manual | `team@llars.e-beratungsinstitut.de` | Brevo **API** from the server (`curl -4`) |

**Reply-To + contact address everywhere:** `llars@e-beratungsinstitut.de` (a real
forwarding mailbox on the root domain). So replies reach us even for
`noreply` mails.

## Sender/Reply-To Logic

In `app/services/email_service.py` (env-overridable, read at runtime):

| Function | Default | Env Override |
|----------|---------|--------------|
| `_from_notify()` (`:65`) | `team@llars.e-beratungsinstitut.de` | `MAIL_FROM_NOTIFY` |
| `_from_noreply()` (`:70`) | `noreply@llars.e-beratungsinstitut.de` | `MAIL_FROM_NOREPLY` |
| `_reply_to_addr()` (`:75`) | `llars@e-beratungsinstitut.de` | `MAIL_REPLY_TO` |
| `_resolve_from()` (`:51`) | appends display name (`SMTP_FROM_NAME`) | `SMTP_FROM` / `SMTP_USERNAME` |

- **Welcome / IJCAI Demo** uses `_from_notify()` + `_reply_to_addr()`
  (`send_registration_confirmation` / `send_ijcai_welcome`).
- **Reset** uses `_from_noreply()` + `_reply_to_addr()`
  (`send_password_reset`).

## Delivery Mechanics (App Mails)

- **SMTP send:** `_send_sync()` (`:80`) builds an `EmailMessage` with
  plain text + HTML alternative, sets `Reply-To`, logs success/failure.
  Configured via `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`,
  `SMTP_PASSWORD`, `SMTP_USE_TLS`/`SMTP_USE_SSL`.
- **Fire-and-forget:** `send_async()` (`:137`) starts the send in a
  daemon thread — never blocks the request and never throws.
- **Undeliverable addresses are skipped:** `_is_real_inbox()`
  (`:162`) filters empty addresses and synthetic `…@noemail.invalid` addresses
  (assigned for anonymous, email-less referral signups).
- **Config check:** `_is_configured()` (`:44`) — without `SMTP_HOST` (+ `SMTP_FROM`
  or `SMTP_USERNAME`), sending is silently skipped (logged).

## What Triggers App Mails

| Mail | Trigger (Code) |
|------|-----------------|
| Welcome | Referral registration/redeem with email: `app/routes/referral/referral_routes.py` (`send_registration_confirmation`) |
| IJCAI Demo Welcome | Signup via `/join/ijcai`: `app/routes/referral/referral_routes.py` (`send_ijcai_welcome`, English) |
| Reset (User) | "Forgot password?": `app/routes/auth/password_reset_routes.py` (`send_password_reset`) |
| Reset (Admin) | Admin button: `app/routes/users/user_admin_routes.py` (`send_password_reset`) |
| Reset (email-mode re-entry) | Known email on `email`-mode link: one-time sign-in link (`_send_referral_signin_link`) |

Both run purely on user/admin action; no periodic sending, no
background job.

## Provider & Hard Rules (Brevo)

- **Authenticated sending domain:** `llars.e-beratungsinstitut.de` (subdomain,
  DKIM-signed). **Only send cleanly from here** — the root or TH domain lands
  in spam.
- **IP allowlist (hard rule):** Brevo allows API **and** SMTP only from the
  **server IPv4**. From a laptop or over IPv6 → `401 unrecognised IP`. → **Every
  send runs through the server, IPv4 enforced** (`curl -4`).
- **From = pure sending address**, not a mailbox/MX. Receiving/replies only via
  the reply-to address.
- **Quote .env values containing spaces** (e.g. `SMTP_FROM_NAME="…"`), otherwise
  the prod smoke test breaks when `source`-ing the .env (→ deploy rollback).

Full Brevo/DNS/sending details including invitation sending:
`MAIL_RUNBOOK.md` (repo `EMNLP2026`).

## Invitation Mails (Recruiting)

Recruiting invitations are **not** sent by the mail service, but as
branded HTML via the **Brevo transactional API from the server** (one recipient
per call). Sender/reply-to as above; one dedicated template with its own
join link per recruiting source (source tracking). See
[Human Studies Playbook §5](../human_studies/playbook.md#5-einladungsmail-branden-versenden)
and `MAIL_RUNBOOK.md` (EMNLP2026).

---

## Admin Mail Center

The **Admin Mail Center** (UI + `MailCenterService`,
`app/services/mail/mail_center_service.py`) sends branded invitations and
announcements per referral link directly from LLARS:

- **Resolve recipients** from referral link, scenario role, system role or
  an explicit username/address list (`resolve_recipients`).
- **Sending** (`send_invitations` / `send_announcement`) via `email_service` →
  Brevo; for each `(link, email)` an **invitation row** (`referral_invitation`)
  is stored (one open invitation per link+email).
- **Auto-match:** If someone later registers with an invited email, the
  invitation flips to *accepted*
  (`match_invitation_on_registration`, called from the referral `/register` and
  `/redeem` flow).
- **Audit/statistics:** `query_log`, `link_invitation_stats`,
  `record_engagement_event`.

Synthetic `…@noemail.invalid` addresses are discarded during resolution
(`_is_synthetic_or_blank`). App mails (welcome/reset) still run directly
via `email_service`.
