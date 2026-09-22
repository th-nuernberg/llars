# LLARS v1 Scenario API

**Version:** 1.0 | **Last updated:** May 2026

Programmatic REST API for creating and managing complete scenarios — config, items, assessors, and referral links — in a single `POST`. Built for external clients (CI seeders, study pipelines, notebooks) that need to drive the scenario wizard from outside the browser.

All endpoints live under `/api/v1/*`.

---

## Authentication

| Method | Header | When |
|---|---|---|
| Personal API key | `X-API-Key: <key>` | External clients, CI |
| System admin key | `X-API-Key: $SYSTEM_ADMIN_API_KEY` | Server-to-server |
| OAuth bearer | `Authorization: Bearer <token>` | Browser sessions (Authentik) |

Mint API keys under **Settings → API Keys**. The key value is shown exactly once — copy it immediately.

### Permission to mint keys

`POST /api/auth/api-keys` is gated by `feature:api_keys:create` (admin + researcher by default). The `admin:*` scope additionally requires `feature:api_keys:admin_scope` (admin only).

!!! warning "Bootstrap requires a browser session"
    `POST /api/auth/api-keys` itself is decorated with `@authentik_required` (OAuth) — it does **not** accept `X-API-Key`. External CI clients therefore cannot bootstrap their own scoped keys via API key auth: they need a one-time Authentik browser session as a user holding `feature:api_keys:create`. Each account is capped at **10** keys.

Allowed scopes when minting: `scenario:read`, `scenario:write`, `admin:*` (see `ALLOWED_API_KEY_SCOPES` in `app/routes/auth/api_key_routes.py`). Anything else is rejected with `400`.

---

## Scopes

API keys can be restricted to a scope list. An empty list means the key inherits the owner's permissions (legacy behaviour). OAuth bearer tokens carry no scopes; they fall back to the regular RBAC system.

| Scope | Allows | RBAC fallback (OAuth) |
|---|---|---|
| `scenario:read` | `GET /api/v1/scenarios*` | `feature:rating:view`, `feature:ranking:view`, `data:manage_scenarios` |
| `scenario:write` | `POST` / `PATCH` / `DELETE` on `/api/v1/scenarios*` | `data:manage_scenarios` |
| `admin:*` | Everything. Overrides every other scope check | `admin:permissions:manage` |

---

## Endpoints

| Method | Path | Scope | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/scenarios` | `scenario:read` | List scenarios visible to the caller |
| `POST` | `/api/v1/scenarios` | `scenario:write` | **One-shot create** (scenario + items + assessors + referral link) |
| `GET` | `/api/v1/scenarios/{id}` | `scenario:read` | Read a single scenario |
| `PATCH` | `/api/v1/scenarios/{id}` | `scenario:write` | Patch name / description / archive flag |
| `DELETE` | `/api/v1/scenarios/{id}` | `scenario:write` | Hard delete (cascade) |
| `POST` | `/api/v1/scenarios/{id}/archive` | `scenario:write` | Soft archive (toggle) |
| `POST` | `/api/v1/scenarios/{id}/items` | `scenario:write` | Append items |
| `DELETE` | `/api/v1/scenarios/{id}/items/{item_id}` | `scenario:write` | Detach a single item |
| `GET` | `/api/v1/scenarios/{id}/assessors` | `scenario:read` | List members |
| `POST` | `/api/v1/scenarios/{id}/assessors` | `scenario:write` | Invite an assessor |
| `PATCH` | `/api/v1/scenarios/{id}/assessors/{user_id}` | `scenario:write` | Patch roles / status |
| `DELETE` | `/api/v1/scenarios/{id}/assessors/{user_id}` | `scenario:write` | Remove a membership |
| `GET` | `/api/v1/scenarios/{id}/referral-link` | `scenario:read` | Read attached link |
| `POST` | `/api/v1/scenarios/{id}/referral-link` | `scenario:write` | Sync link to scenario (idempotent on slug) |
| `DELETE` | `/api/v1/scenarios/{id}/referral-link` | `scenario:write` | Detach link (link itself stays) |
| `GET` | `/api/v1/scenarios/{id}/results` | `scenario:read` | Results export (json/csv/jsonl, long format) |
| `GET` | `/api/v1/scenarios/{id}/metrics` | `scenario:read` | IRR block (filters: `?copilot=`, `?part=`) |
| `GET` | `/api/v1/scenarios/{id}/copilot` | `scenario:read` | Co-pilot status (labeling, owner only) |
| `PUT` | `/api/v1/scenarios/{id}/copilot` | `scenario:write` | Update co-pilot config |
| `POST` | `/api/v1/scenarios/{id}/copilot/generate` | `scenario:write` | (Re-)start suggestion generation |
| `PUT` | `/api/v1/scenarios/{id}/labeling-config` | `scenario:write` | Toggle question-first labeling (`questions`) and the second choice (`second_choice`) (labeling, owner only) |
| `GET` | `/api/v1/scenarios/{id}/parts` | `scenario:read` | Parts status incl. per-assessor progress (labeling, owner only) |
| `PUT` | `/api/v1/scenarios/{id}/parts/{part_id}` | `scenario:write` | Update a part: `locked` / `copilot` / `name` / `order` |

---

## One-shot example

```bash
curl -X POST https://llars.example.org/api/v1/scenarios \
  -H "X-API-Key: $LLARS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "EMNLP Pilot v4",
    "description": "Turing-Test 40 items",
    "eval_config": {
      "type": "comparison",
      "config": {
        "question": {"de": "Welche Antwort ist besser?", "en": "Which response is better?"},
        "allow_tie": true,
        "show_source": false,
        "gamification_enabled": true,
        "gamification_first_milestone": 10,
        "gamification_recurring_milestone": 5
      }
    },
    "items": {
      "schema_version": "1.0",
      "items": [
        {
          "id": "case_001",
          "label": "Case 001",
          "source": {"type": "human"},
          "content": {
            "type": "conversation",
            "messages": [
              {"role": "Klient", "content": "I cannot sleep ..."},
              {"role": "Berater", "content": "Tell me more ..."}
            ]
          },
          "features": [
            {"type": "candidate", "content": "Empathic counsellor reply", "generated_by": "human"},
            {"type": "candidate", "content": "GPT-5 generated reply",     "generated_by": "Global/OpenAI/gpt-5-nano"}
          ]
        }
      ]
    },
    "assessors": [
      {"username": "researcher", "manager_role": "editor", "evaluation_role": "none"},
      {"username": "evaluator",  "manager_role": "none",   "evaluation_role": "assessor"}
    ],
    "referral_link": {
      "slug": "human-comparison-emnlp",
      "label": "EMNLP Turing-Test 2026",
      "auto_enroll": true
    }
  }'
```

Response (`201 Created`):

```json
{
  "success": true,
  "scenario": {
    "id": 42,
    "name": "EMNLP Pilot v4",
    "evaluation_type": "comparison",
    "function_type_id": 4,
    "item_count": 1,
    "assessor_count": 2,
    "items_imported": {
      "items_created": 1,
      "features_created": 2,
      "item_ids": [517]
    },
    "referral_link": {
      "id": 7,
      "slug": "human-comparison-emnlp",
      "code": "voVXDi0G7AJm",
      "target_scenario_id": 42
    }
  }
}
```

---

## Curl quickref

```bash
# List (?limit=&offset=)
curl -H "X-API-Key: $K" https://llars/api/v1/scenarios?limit=20

# Read a single scenario
curl -H "X-API-Key: $K" https://llars/api/v1/scenarios/42

# Update description
curl -X PATCH -H "X-API-Key: $K" -H "Content-Type: application/json" \
  -d '{"description":"Updated via API"}' \
  https://llars/api/v1/scenarios/42

# Archive
curl -X POST -H "X-API-Key: $K" -H "Content-Type: application/json" \
  -d '{"archived": true}' https://llars/api/v1/scenarios/42/archive

# Invite assessor
curl -X POST -H "X-API-Key: $K" -H "Content-Type: application/json" \
  -d '{"username":"evaluator","evaluation_role":"assessor"}' \
  https://llars/api/v1/scenarios/42/assessors

# Re-point referral link (idempotent)
curl -X POST -H "X-API-Key: $K" -H "Content-Type: application/json" \
  -d '{"slug":"human-comparison-emnlp","auto_enroll":true}' \
  https://llars/api/v1/scenarios/42/referral-link

# Cascade delete
curl -X DELETE -H "X-API-Key: $K" https://llars/api/v1/scenarios/42
```

---

## Appending items later

`POST /api/v1/scenarios/{id}/items` expects a **bare** `LlarsNativeEnvelope` as the body — **not** wrapped in `{"items": {...}}`. This is the most common stumbling block: a wrapper object is rejected with `400` (`extra='forbid'` + missing `schema_version`).

```bash
curl -X POST https://llars.example.org/api/v1/scenarios/42/items \
  -H "X-API-Key: $LLARS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "schema_version": "1.0",
    "reference": null,
    "items": [
      {
        "id": "case_002",
        "label": "Case 002",
        "source": {"type": "human"},
        "content": "Plain text content for this item.",
        "features": [
          {"type": "candidate", "content": "Reply A", "generated_by": "human"},
          {"type": "candidate", "content": "Reply B", "generated_by": "Global/OpenAI/gpt-5-nano"}
        ]
      }
    ]
  }'
```

Response (`201 Created`):

```json
{
  "success": true,
  "items_created": 1,
  "features_created": 2,
  "item_ids": [518]
}
```

`reference` is optional and may be omitted. An empty `items: []` is accepted and returns `200` with `items_created: 0`.

---

## Parts / Phases (labeling)

Labeling scenarios (`type: "labeling"`) can optionally be partitioned into
**ordered parts** — the study gate for calibration designs (P1 → IRR +
alignment meeting → unlock P2 → …). The partitioning is **invisible to
raters**: locked parts simply don't exist for them yet, and the `parts`
section is stripped server-side from every config delivered to assessors.

Create via the `parts` section inside `eval_config.config` — **the items must
be part of the same request**, because `size` specs ("the next N items in
upload order", last part without `size` = rest) are resolved into item ids in
the same transaction:

```json
"eval_config": {
  "type": "labeling",
  "config": {
    "mode": "single",
    "labels": [{"id": "disclosure", "label": {"de": "Disclosure", "en": "Disclosure"}}],
    "copilot": {"enabled": true, "model_id": "Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506", "hidden_control_ratio": 0.2},
    "parts": {
      "enabled": true,
      "list": [
        {"name": "Calibration 1", "size": 100, "order": "sequential", "copilot": false},
        {"name": "Calibration 2", "size": 50,  "order": "sequential", "copilot": false, "locked": true},
        {"name": "Main phase",                  "order": "sequential", "copilot": true,  "locked": true}
      ]
    }
  }
}
```

Per-part semantics: `order` (`sequential` = identical order for every rater,
`random` = deterministic per-user shuffle), `copilot` (per-part override under
the `copilot.enabled` master switch — the runner only generates for co-pilot
parts), `locked` (not delivered until the owner unlocks).

```bash
# Status incl. per-assessor progress
curl -H "X-API-Key: $K" https://llars/api/v1/scenarios/42/parts

# Unlock a phase (the IRR gate between calibration phases)
curl -X PUT -H "X-API-Key: $K" -H "Content-Type: application/json" \
  -d '{"locked": false}' https://llars/api/v1/scenarios/42/parts/p2

# Add items later: part_id is REQUIRED while parts are active
curl -X POST -H "X-API-Key: $K" -H "Content-Type: application/json" \
  -d '{"schema_version": "1.0", "part_id": "p3", "items": [...]}' \
  https://llars/api/v1/scenarios/42/items

# IRR per phase (combinable with ?copilot=with|without)
curl -H "X-API-Key: $K" "https://llars/api/v1/scenarios/42/metrics?part=p1"
```

The results export (`GET .../results`) carries a `part` column on every row;
`copilot_metrics` is additionally aggregated per part (`per_part`).
`item_ids` of existing parts are **not** editable via PUT (partition
invariant + audit trail); redistributing before study start = recreate the
scenario.

---

## Validation & errors

Failed requests follow the LLARS standard envelope:

```json
{
  "error": "Invalid request body — eval_config.config: ...",
  "details": {"errors": [{"loc": ["eval_config", "config"], "msg": "...", "type": "value_error"}]}
}
```

| Status | Trigger |
|---|---|
| 400 | Body violates schema (e.g. `type=rating` with `SimpleRankingConfig`) |
| 401 | Missing / invalid API key or token |
| 403 | Scope insufficient (`scenario:read` key tries POST) |
| 404 | Scenario / user / slug not found |
| 409 | Owner conflict (member already exists; cannot demote last owner) |

`eval_config.config` must match `eval_config.type` (`rating` ↔ `RatingConfig`, `comparison` ↔ `ComparisonConfig`, …). The schema cross-validates both.

---

## Notes

- Items follow the **LLARS-Native format** (`schema_version: "1.0"`). Reference + item structure are documented in `app/schemas/evaluation_data_schemas.py`.
- The API key owner is automatically added as `manager_role='owner'` when one-shot-creating a scenario.
- `referral_link.slug` is the **idempotency axis**: the same slug repointed across re-seedings keeps the external URL stable.
- `DELETE /scenarios/{id}` cleans up orphan `EvaluationItems` (and their features + messages); items still linked to other scenarios are preserved.
