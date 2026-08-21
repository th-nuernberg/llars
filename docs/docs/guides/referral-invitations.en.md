# Referral & Invitation System

The referral system produces shareable invite links (`/join/<slug>`) through
which participants self-register and are automatically enrolled into the right
scenarios. It is the basis for study recruiting and for conference demos (e.g.
the [IJCAI demo link](../human_studies/ijcai-demo.md)).

Code: `app/db/models/referral.py`, `app/services/referral_service.py`,
`app/routes/referral/referral_routes.py`.

---

## Structure

```
ReferralCampaign  (campaign, e.g. "AI Conference 2026")
└── ReferralLink   (individual invite link, own slug + QR)
    └── ReferralRegistration  (one row per registration, unique by username)
```

- A **campaign** groups links under a theme and may carry start/end dates and a
  global registration cap. Status: `draft`, `active`, `paused`, `expired`,
  `archived` — a link only works while its campaign is `active`.
- A **link** has an auto-generated `code` and an optional readable `slug`
  (`/join/ai-conf-2026`). Each link can carry its own usage limits, an expiry
  date, the role to assign, and auto-enroll targets.

---

## Per-link signup mode

Every link has a `signup_mode` that controls how much the registration form
asks for, so you can tune friction to the audience:

| `signup_mode` | Form | Account |
|---------------|------|---------|
| `full` (default) | Username + password (+ email per the `collect_*` flags) | Chosen by the user |
| `email` | Email only | Username derived deterministically from email+slug; passwordless. To return via the same link + email, the system emails a one-time sign-in link |
| `instant` | One tap, nothing asked | Anonymous account, everything generated server-side |

Fine-tuning for `full` mode via three link flags:

- `collect_email` — show the email field (default `true`).
- `collect_email_optional` — when `collect_email=true`: field shown but not
  required (blank ⇒ a synthetic `…@noemail.invalid` address is synthesized).
- `collect_display_name` — optional display-name field (default `true`).

!!! note "Secure re-entry (`email` mode)"
    Because the username is derived deterministically from the email, re-typing
    an *existing* email must **not** auto-login. Instead the server sends a
    one-time sign-in link (via the password-reset mechanism) and answers
    neutrally — the account is only adopted after the link is clicked.

---

## Auto-enroll into scenarios

A link can enroll registrants straight into scenarios:

| Field | Effect |
|-------|--------|
| `target_scenario_id` | Single scenario, role **assessor** (legacy) |
| `target_scenario_ids` | JSON list — registrants are enrolled as **assessor** into all of them |
| `viewer_scenario_ids` | JSON list — registrants get **viewer** (read-only manager) access on these scenarios |

A scenario may appear in both lists (the demo case): its `ScenarioUsers` row then
carries `evaluation_role='assessor'` **and** `manager_role='viewer'`. Enrollment
is idempotent — an existing membership is never overwritten, not even to upgrade
it.

**Redirect after the first sign-in** depends on how many scenarios the user is an
assessor in:

- exactly one scenario → straight into `/scenarios/<id>/evaluate`
- multiple scenarios → the evaluation hub (`/evaluation`)
- none → home

---

## Ways to join a link

| Who | Flow | Endpoint |
|-----|------|----------|
| New person | open `/join/<slug>`, register | `POST /api/referral/register` |
| Already logged-in person | redeem a code in the UI | `POST /api/referral/redeem` |

The `redeem` path enrolls existing users into the target scenarios and attributes
them to the campaign — **without** touching their global role. (If the link role
were applied here, e.g. a researcher redeeming an evaluator-scoped study code
would be silently downgraded.) Both paths are idempotent.

---

## Security & privacy

- **Role allowlist:** because `/register` is public and creates real accounts, a
  link may only grant `evaluator`, `researcher`, `chatbot_manager` or `viewer`.
  `admin` is excluded and falls back to `evaluator` (`ALLOWED_REFERRAL_ROLES`).
- **IP anonymization:** `referral_registrations` never stores the full IP. It is
  truncated to the network prefix (IPv4 → /24, IPv6 → /48).
- **Study consent:** scenario-bound or study-detected links force the GDPR study
  consent on the form; an audit record (consent version, text SHA-256, hashed IP,
  language) is written alongside.
- **Rate limits** (on top of the global defaults, `app/main.py`):

  | Endpoint | Dev | Prod |
  |----------|-----|------|
  | `POST /register` | 60/h, 20/10 min | 20/h, 6/10 min |
  | `GET /validate` | 300/h | 120/h |

---

## Admin UI (Mail-Center / Referrals)

Admin → Mail-Center / Referrals (`admin:referral:manage`):

- Create, edit, deactivate and archive campaigns and links.
- Show a per-link **QR code** (modal) and download it as **PNG / SVG / PDF** —
  the direct artwork for posters and conference booths.
- **Funnel analytics:** every `/join` page load counts as a "click"
  (`click_count`), set against registrations ⇒ conversion rate per link /
  campaign / system-wide.

### Key endpoints

| Endpoint | Methods | Purpose |
|----------|---------|---------|
| `/api/referral/validate/<code_or_slug>` | GET | Public: validate link + form shape |
| `/api/referral/register` | POST | Public: registration |
| `/api/referral/redeem` | POST | Logged-in: redeem a code |
| `/api/referral/admin/campaigns` | GET/POST | Campaigns |
| `/api/referral/admin/campaigns/:id` | GET/PUT/DELETE | Read/update/delete campaign |
| `/api/referral/admin/campaigns/:id/links` | GET/POST | Links of a campaign |
| `/api/referral/admin/links/:id` | GET/PUT/DELETE | Manage link |
| `/api/referral/admin/analytics/overview` | GET | Funnel overview |
| `/api/referral/admin/registrations` | GET | Registrations |

Referral links can also be managed programmatically via the
[v1 Scenario API](api-v1-scenarios.md).

---

## Related pages

- [IJCAI demo](../human_studies/ijcai-demo.md) — one QR, seven demo scenarios
- [Permission system](permission-system.md) — scenario roles incl. viewer
- [Mail service](../entwickler/mail-service.md) — welcome / invitation mails
