# IJCAI 2026 Demo

The IJCAI demo is a live-booth scenario: conference attendees scan **one** QR
code (`/join/ijcai`), instantly get a demo account, and are enrolled as an
evaluator in **one shared demo scenario per evaluation type** — plus read-only
viewer access so they can watch the live aggregated analysis across all
participants.

Seeder: `app/scripts/seed_ijcai_demo.py`. Welcome mail (English):
`app/services/email_service.py` → `render_ijcai_welcome` / `send_ijcai_welcome`.

---

## Concept

- **Shared scenarios (not per-person):** everyone who scans the QR rates the same
  20 items per type. This makes the Scenario-Manager analysis show live
  inter-rater reliability across all participants — the headline of a
  collaborative evaluation platform.
- **Seven scenarios**, one per evaluation type: `rating`, `ranking`,
  `mail_rating`, `comparison`, `communication_comparison`, `authenticity`,
  `labeling`.
- **Content in English** (international audience); the German original is kept per
  item in metadata. The evaluation **config** (task, dimensions, buckets, labels)
  is fully bilingual (de/en) and follows the language toggle.
- Owner account of all scenarios: `ijcai_demo`.

---

## Seed / re-seed

Datasets live under `app/scripts/ijcai_demo/<type>.json` (one per type). The
seeder is **idempotent**: re-running reuses existing scenarios (matched by name +
creator) and updates the referral link in place — safe to run after every deploy.

```bash
# Seed (inside the running Flask container, <color> = active blue/green color)
docker exec llars_flask_<color> python -m scripts.seed_ijcai_demo

# Rebuild from scratch (deletes + recreates the 7 scenarios)
docker exec llars_flask_<color> python -m scripts.seed_ijcai_demo --reset
```

The seeder prints the `scenario_ids`, the `link_slug` (`ijcai`), the `link_code`
and the `join_url` at the end.

**Link configuration** set by the seeder:

| Field | Value |
|-------|-------|
| `slug` | `ijcai` |
| `signup_mode` | `email` (conference default: QR → email → in) |
| `target_scenario_ids` | all 7 scenarios (assessor) |
| `viewer_scenario_ids` | all 7 scenarios (read-only viewer) |
| `role_name` | `ijcai_reviewer` |
| `expires_at` | `2026-08-29 23:59:59` (see [End of life](#end-of-life)) |

---

## How participants join

1. **Scan the QR** → `/join/ijcai`.
2. **Enter an email** (`signup_mode='email'`): a passwordless account is created,
   username derived deterministically from email + slug, and the person is logged
   in automatically.
3. **English welcome mail** (`send_ijcai_welcome`) confirms the account and links
   the evaluation hub. It is deliberately distinct from the German "Kann KI
   Beratung?" study mail (product demo, not a study).
4. **Redirect:** since the person is an assessor in multiple scenarios, they land
   in the evaluation hub (`/evaluation`) and pick an evaluation type.
5. **Returning:** scan the same QR, enter the same email → the system sends a
   one-time sign-in link (no password needed).

> The auto-enroll, signup-mode and redirect mechanics are general and described
> in the [referral & invitation system](../guides/referral-invitations.md).

---

## End of life

The demo has a defined end, in two independent stages:

**1. The link expires on 2026-08-29, 23:59:59 (Europe/Berlin).**
The conference ends on 2026-08-22; the extra week of grace covers late scans of a
printed QR code. After that `ReferralService.validate_link` rejects the link, so
**no new registrations** are possible. Accounts that already exist are
unaffected. The date lives in the constant `LINK_EXPIRES_AT` in
`app/scripts/seed_ijcai_demo.py` and is written to the DB on **every** seeder run
(config-as-code): change it there and re-seed — a manual DB edit would be
overwritten on the next run.

**2. Accounts lose all permissions 7 days after registration.**
`expire_ijcai_accounts` in `app/scripts/demo_cleanup.py` replaces every role of an
affected account with the empty `demo_expired` role (zero permissions) and
archives its scenario memberships.

- **Logging in keeps working** — `is_active` is not touched, nothing is deleted.
  But nothing is usable any more: no AI, no generation, no prompt engineering, no
  evaluation (deny-by-default).
- **Why an empty role instead of no role?**
  `auth.decorators._ensure_default_evaluator_role` auto-grants `evaluator` to any
  user with **no** `user_roles` row on their next login, so a role-less account
  would silently reactivate itself. That is why `demo_expired` is assigned
  *first* and everything else removed afterwards — the account never has zero
  roles.
- **Double safety fence:** an account is only affected if it *both* carries the
  auto-generated username pattern `demo-ijcai-*` *and* has a registration on the
  `ijcai` link. Existing users who merely redeemed the code are never touched.
- **Idempotent:** already expired accounts are only counted, not rewritten; one
  broken account never aborts the run.

**Execution:** daily at 03:30 via the systemd timer `llars-cleanup.timer`
(→ `scripts/server/llars_cleanup.sh`, step 6) inside the active blue/green Flask
container. The job also runs after every nightly deploy as the CI job
`maintenance:demo-cleanup`. Manually:

```bash
docker exec llars_flask_<color> python -m scripts.demo_cleanup
```
