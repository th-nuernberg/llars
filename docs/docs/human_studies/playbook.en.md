# Playbook — running a human study in LLARS

This playbook describes the **generic, reusable workflow** we use to set up and
operate a human study in LLARS — from study configuration through to recruiting
tracking. It is written in a **study-independent** way; the running example is
the first study run this way,
[„Kann KI Beratung?"](KannKIBeratung/index.md).

Requirements and annotations from the domain side are handled here neutrally as
**domain notes from the social sciences**
(see [annotations audit](KannKIBeratung/annotations-audit.md)).

---

## Overview — the workflow in 8 steps

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

## 1 · Define study type + eval config

LLARS supports several evaluation types (`ranking`, `rating`, `mail_rating`,
`comparison`, `communication_comparison`, `authenticity`, `labeling`). For a
human study, you pick the type that matches the research question and define the
`eval_config` (task texts, evaluation question, scales/buckets, options).

Recurring building blocks of an `eval_config` for studies:

| Field | Purpose |
|------|-------|
| `welcome_markdown` (DE/EN) | **Start-page briefing** (task 1) — rendered above the item tiles. |
| `task_description_markdown` (DE/EN) | **Per-case task text** (task 2) — rendered in the evaluation interface. |
| `question` (DE/EN) | The evaluation question per item. |
| `item_header_template` | Header line per item (e.g. `{{channel_label}}`). |
| `gamification_*`, `progressive_reveal` | Feedback/unlock logic (see step 6). |

> **Important:** A scenario's `eval_config` is **not patchable** via the v1 API.
> Later text or config changes require **re-creating** the scenario (the referral
> slug automatically points to the new scenario, the join URLs stay stable — see
> step 7).

**Rendering in LLARS:**

- Start-page briefing: `llars-frontend/src/views/Evaluation/EvaluationItemsOverview.vue`
  (briefing banner, `taskMarkdown` → `LMarkdownContent`).
- Per-case task (comparison): `llars-frontend/src/views/Evaluation/interfaces/ComparisonInterface.vue`
  (`task_description_markdown` / fallback question).

---

## 2 · Prepare data/items + create scenario

Items are prepared as JSON (one item = context + features to be evaluated) and
created as a scenario via the **v1 API**:

```
POST /api/v1/scenarios          # Szenario + Items + erster Referral-Link
GET  /api/v1/scenarios/<id>     # Verifikation
```

Authentication via the **system admin API key** in the `X-API-Key` header. Study
configuration, item ordering, and build are study-specific and typically live in
the respective research repo (build scripts, payload construction).

---

## 3 · Referral links per recruiting source (source tracking)

For each recruiting source (organization, mailing list, channel), **its own
referral slug** is created. Every registration is attributed to the source whose
link it came through → you can see where the raters originated.

```
POST /api/v1/scenarios/<id>/referral-link
  { "slug": "...", "label": "...", "role_name": "evaluator",
    "campaign_name": "...", "auto_enroll": true,
    "collect_email": false, "collect_display_name": false }
```

- **Idempotent per slug:** calling again patches the link (e.g. to toggle
  `collect_email`) without re-creating the scenario.
- Join URL = `https://<host>/join/<slug>`.
- Validation: `GET /api/referral/validate/<slug>`.
- Backend: `app/routes/referral/referral_routes.py`.

> **Rule:** Never send the same link to all sources — otherwise source tracking
> is lost. Forwarding **within** the same source is fine.

---

## 4 · Consent / anonymity / optional email

The join/registration flow can be fine-tuned per referral link
(`app/routes/referral/referral_routes.py`, frontend
`llars-frontend/src/views/Register.vue`):

| Setting | Effect |
|-------------|---------|
| `collect_email=false` | Email field hidden → **anonymous** account (username + password only). A synthetic `…@noemail.invalid` address is set (not deliverable). |
| `collect_email=true` + `collect_email_optional=true` | Email field visible, but optional. |
| `collect_email=true` + `collect_email_optional=false` | Email field visible and required (legacy behavior). |
| `collect_display_name=false` | No display name. |
| Study link | Shows a **consent block** (data-protection/study consent) in the register form (`useStudyConsent`, version + timestamp; info page `/study-consent`). |

This enables anonymous, GDPR-compliant participation with optional email — the
email is only needed when app mails (welcome, reset) should be delivered.

---

## 5 · Brand invitation mail + send

Recruiting invitations are sent as a **branded HTML mail**. LLARS has two mail
paths (details: [mail service](../entwickler/mail-service.md) and the
`MAIL_RUNBOOK.md` in the research repo):

- **App mails** (welcome / password reset) — automatic via user action, through
  `app/services/email_service.py` → Brevo SMTP.
- **Invitation mails** (recruiting) — **manual**, as branded HTML via the
  **Brevo transactional API** (one recipient per call).

**Hard sending rules (apply to both paths):**

1. **Send only from the server, over IPv4** (`curl -4`). Brevo only allows
   API/SMTP from the server IPv4 — laptop or IPv6 → `401 unrecognised IP`.
2. **Send only from the authenticated (DKIM) sending subdomain**, otherwise spam.
3. **From addresses are pure sending addresses** (no mailbox). Replies go through
   the **Reply-To address**.
4. Per recruiting source, send the matching template variant with the **correct
   source link** (tracking, see step 3).

> The invitation's branding/wording lives as a template + generator in the
> research repo; here the wording is maintained centrally, not in the generated
> HTMLs.

---

## 6 · Per-N feedback (gamification / evaluation popup)

Studies benefit from intermediate feedback to motivate raters and structure
their workflow. For comparison studies, LLARS supports an **evaluation popup
after every N completed cases** plus **progressive unlocking** of further cases:

| Config field | Effect |
|-------------|---------|
| `gamification_enabled` | Enables the reward/evaluation popup. |
| `gamification_first_milestone` | First popup after N completed cases. |
| `gamification_recurring_milestone` | Then again every N further cases. |
| `progressive_reveal` | Unlocks further cases after each milestone. |

The popup shows the preference shares so far (study-specific axes, e.g.
„bevorzugt menschlich vs. KI"). Implementation:

- `llars-frontend/src/composables/useComparisonEvaluation.js` (milestone logic,
  `milestoneEvent`).
- `llars-frontend/src/views/Evaluation/interfaces/ComparisonRewardDialog.vue`
  (popup UI).
- `app/services/evaluation/comparison_preference_stats_service.py` (aggregation
  of preferences, endpoint `GET /api/evaluation/session/:scenarioId/comparison/preferences`).

Additionally, there is an optional **one-time confirmation after the first saved
evaluation** (see the annotations audit of the example study), which guides new
participants to the „Weiter" button.

---

## 7 · Deploy (Blue/Green) — and the re-creation note

Code and mail changes go live via the normal LLARS deploy (Blue/Green, see the
project docs on CI/CD and deployment). Important for studies:

- **`eval_config` changes** (task texts, question, milestones) are **not
  patchable** → **re-create** the scenario. The referral slug automatically
  points to the new scenario, the join URLs stay stable. On re-deploy: first
  create the **new** scenario (slug re-points), then delete the old one so the
  link never breaks.
- **Test accounts** are only deleted as confirmed junk (0 evaluations); the live
  DB is shared — never remove real users or CI accounts.

---

## 8 · Recruiting & acceptance tracking

- **Source per registration:** derived from the referral slug
  (`referral_registrations`, linked to `referral_links`).
- **Acceptance/activity:** completed cases per user (comparison votes are stored
  in `item_comparison_evaluations`).
- **Demographics:** optional, one-time demographics survey at first login
  (`UserDemographics`, `app/db/models/user_demographics.py`) — for cohort
  analyses.

This lets you evaluate how many raters came through each source and how active
they were.

---

## Checklist (short form)

- [ ] Study type + `eval_config` (task texts DE/EN, question, milestones) set.
- [ ] Items prepared, scenario created via `POST /api/v1/scenarios`.
- [ ] One referral slug per source (`auto_enroll`, `role_name`, consent/email).
- [ ] Consent/anonymity/optional email configured per link.
- [ ] Invitation mail branded, sent from the server (IPv4), correct link per source.
- [ ] Per-N feedback (gamification/popup) configured and checked.
- [ ] Deploy via Blue/Green; scenario re-created on text change.
- [ ] Recruiting/acceptance tracking + demographics evaluated.
