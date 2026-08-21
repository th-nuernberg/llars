# LLARS v1 Scenario API

**Version:** 1.0 | **Stand:** Mai 2026

Programmatische REST-API zum Erstellen und Verwalten kompletter Szenarien — Konfiguration, Items, Bewerter und Referral-Links — in einem einzigen `POST`. Gedacht für externe Clients (CI-Seeder, Studien-Pipelines, Notebooks), die den Scenario-Wizard ohne Browser-Login von außen ansteuern.

Alle Endpunkte liegen unter `/api/v1/*`.

---

## Authentifizierung

| Methode | Header | Wann |
|---|---|---|
| Persönlicher API-Key | `X-API-Key: <key>` | Externe Clients, CI |
| System-Admin-Key | `X-API-Key: $SYSTEM_ADMIN_API_KEY` | Server-zu-Server-Calls |
| OAuth Bearer | `Authorization: Bearer <token>` | Browser-Sessions (Authentik) |

API-Keys legst du unter **Einstellungen → API-Keys** an. Ein Schlüssel wird genau einmal angezeigt — speicher ihn sofort.

### Benötigte Berechtigung zum Erstellen

`POST /api/auth/api-keys` ist gegated mit `feature:api_keys:create` (per Default Admin + Researcher). Die Sonderform `admin:*` braucht zusätzlich `feature:api_keys:admin_scope` (nur Admin).

!!! warning "Bootstrap nur per Browser-Session"
    `POST /api/auth/api-keys` selbst ist mit `@authentik_required` (OAuth) belegt — der Endpoint akzeptiert **kein** `X-API-Key`. Externe CI-Clients können sich also keine Keys via API bootstrappen, sondern brauchen einen einmaligen Browser-Login (Authentik-Session) bei einem User mit `feature:api_keys:create`. Pro Konto sind maximal **10** Keys erlaubt.

Erlaubte Scopes beim Minten: `scenario:read`, `scenario:write`, `admin:*` (siehe `ALLOWED_API_KEY_SCOPES` in `app/routes/auth/api_key_routes.py`). Andere Strings werden mit `400` abgelehnt.

---

## Scopes

API-Keys können auf eine Scope-Liste eingeschränkt werden. Leere Scope-Liste = der Schlüssel erbt die Permissions des Eigentümers (Legacy-Verhalten). OAuth-Bearer-Tokens haben keine Scopes; bei ihnen greift das normale RBAC.

| Scope | Erlaubt | RBAC-Fallback (für OAuth) |
|---|---|---|
| `scenario:read` | `GET /api/v1/scenarios*` | `feature:rating:view`, `feature:ranking:view`, `data:manage_scenarios` |
| `scenario:write` | `POST` / `PATCH` / `DELETE` auf `/api/v1/scenarios*` | `data:manage_scenarios` |
| `admin:*` | Alles. Setzt jeden anderen Scope-Check außer Kraft | `admin:permissions:manage` |

---

## Endpunkte

| Methode | Pfad | Scope | Zweck |
|---|---|---|---|
| `GET` | `/api/v1/scenarios` | `scenario:read` | Eigene Szenarien auflisten |
| `POST` | `/api/v1/scenarios` | `scenario:write` | **One-Shot-Create** (Szenario + Items + Bewerter + Ref-Link) |
| `GET` | `/api/v1/scenarios/{id}` | `scenario:read` | Einzelnes Szenario lesen |
| `PATCH` | `/api/v1/scenarios/{id}` | `scenario:write` | Name / Beschreibung / Archiv-Flag patchen |
| `DELETE` | `/api/v1/scenarios/{id}` | `scenario:write` | Hart löschen (Cascade auf Items + Memberships) |
| `POST` | `/api/v1/scenarios/{id}/archive` | `scenario:write` | Soft-Archive (toggle) |
| `POST` | `/api/v1/scenarios/{id}/items` | `scenario:write` | Weitere Items hinzufügen |
| `DELETE` | `/api/v1/scenarios/{id}/items/{item_id}` | `scenario:write` | Einzelnes Item entfernen |
| `GET` | `/api/v1/scenarios/{id}/assessors` | `scenario:read` | Bewerterliste |
| `POST` | `/api/v1/scenarios/{id}/assessors` | `scenario:write` | Bewerter einladen |
| `PATCH` | `/api/v1/scenarios/{id}/assessors/{user_id}` | `scenario:write` | Rollen patchen |
| `DELETE` | `/api/v1/scenarios/{id}/assessors/{user_id}` | `scenario:write` | Mitgliedschaft entfernen |
| `GET` | `/api/v1/scenarios/{id}/referral-link` | `scenario:read` | Aktuell verknüpften Link lesen |
| `POST` | `/api/v1/scenarios/{id}/referral-link` | `scenario:write` | Link auf Szenario syncen (idempotent über Slug) |
| `DELETE` | `/api/v1/scenarios/{id}/referral-link` | `scenario:write` | Link vom Szenario entkoppeln (Link bleibt erhalten) |
| `GET` | `/api/v1/scenarios/{id}/results` | `scenario:read` | Ergebnisexport (json/csv/jsonl, long format) |
| `GET` | `/api/v1/scenarios/{id}/metrics` | `scenario:read` | IRR-Block (Filter: `?copilot=`, `?part=`) |
| `GET` | `/api/v1/scenarios/{id}/copilot` | `scenario:read` | Co-Pilot-Status (Labeling, nur Owner) |
| `PUT` | `/api/v1/scenarios/{id}/copilot` | `scenario:write` | Co-Pilot-Config aktualisieren |
| `POST` | `/api/v1/scenarios/{id}/copilot/generate` | `scenario:write` | Vorschlagsgenerierung (re-)starten |
| `GET` | `/api/v1/scenarios/{id}/parts` | `scenario:read` | Teile-Status inkl. Fortschritt pro Bewerter (Labeling, nur Owner) |
| `PUT` | `/api/v1/scenarios/{id}/parts/{part_id}` | `scenario:write` | Teil ändern: `locked` / `copilot` / `name` / `order` |

---

## One-Shot Beispiel

```bash
curl -X POST https://llars.example.org/api/v1/scenarios \
  -H "X-API-Key: $LLARS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "EMNLP Pilot v4",
    "description": "Turing-Test 40 Items",
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
              {"role": "Klient", "content": "Ich kann nicht schlafen ..."},
              {"role": "Berater", "content": "Erzählen Sie mehr ..."}
            ]
          },
          "features": [
            {"type": "candidate", "content": "Empathische Antwort der Beraterin", "generated_by": "human"},
            {"type": "candidate", "content": "GPT-5 generierte Antwort",         "generated_by": "Global/OpenAI/gpt-5-nano"}
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

Antwort (`201 Created`):

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

## Curl-Quickref

```bash
# Auflisten (Pagination via ?limit=&offset=)
curl -H "X-API-Key: $K" https://llars/api/v1/scenarios?limit=20

# Einzelnes Szenario lesen
curl -H "X-API-Key: $K" https://llars/api/v1/scenarios/42

# Beschreibung aktualisieren
curl -X PATCH -H "X-API-Key: $K" -H "Content-Type: application/json" \
  -d '{"description":"Aktualisiert via API"}' \
  https://llars/api/v1/scenarios/42

# Archiv-Flag setzen
curl -X POST -H "X-API-Key: $K" -H "Content-Type: application/json" \
  -d '{"archived": true}' https://llars/api/v1/scenarios/42/archive

# Bewerter einladen
curl -X POST -H "X-API-Key: $K" -H "Content-Type: application/json" \
  -d '{"username":"evaluator","evaluation_role":"assessor"}' \
  https://llars/api/v1/scenarios/42/assessors

# Referral-Link auf neues Szenario umlenken (idempotent)
curl -X POST -H "X-API-Key: $K" -H "Content-Type: application/json" \
  -d '{"slug":"human-comparison-emnlp","auto_enroll":true}' \
  https://llars/api/v1/scenarios/42/referral-link

# Cascade-Delete
curl -X DELETE -H "X-API-Key: $K" https://llars/api/v1/scenarios/42
```

---

## Items nachträglich hinzufügen

`POST /api/v1/scenarios/{id}/items` erwartet einen **bare** `LlarsNativeEnvelope` als Body — **nicht** in einen `{"items": {...}}`-Wrapper verpackt. Das ist die häufigste Stolperfalle: ein Wrapper-Objekt wird mit `400` abgelehnt (`extra='forbid'` + Feld `schema_version` fehlt).

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
          {"type": "candidate", "content": "Antwort A", "generated_by": "human"},
          {"type": "candidate", "content": "Antwort B", "generated_by": "Global/OpenAI/gpt-5-nano"}
        ]
      }
    ]
  }'
```

Antwort (`201 Created`):

```json
{
  "success": true,
  "items_created": 1,
  "features_created": 2,
  "item_ids": [518]
}
```

`reference` ist optional und darf weggelassen werden. `items: []` (leer) ist erlaubt und liefert `200` mit `items_created: 0` zurück.

---

## Teile / Phasen (Labeling)

Labeling-Szenarien (`type: "labeling"`) können optional in **geordnete Teile**
gegliedert werden — das Studien-Gate für Kalibrierungs-Designs (P1 → IRR +
Alignment → P2 freischalten → …). Für Bewerter:innen ist die Teilung
**unsichtbar**: gesperrte Teile existieren für sie schlicht (noch) nicht,
die `parts`-Sektion wird aus jeder an Assessoren ausgelieferten Config
serverseitig entfernt.

Anlegen über die `parts`-Sektion in `eval_config.config` — **die Items müssen
im selben Request liegen**, weil `size`-Specs („die nächsten N Items in
Upload-Reihenfolge", letzter Teil ohne `size` = Rest) in derselben Transaktion
in Item-IDs aufgelöst werden:

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
        {"name": "Kalibrierung 1", "size": 100, "order": "sequential", "copilot": false},
        {"name": "Kalibrierung 2", "size": 50,  "order": "sequential", "copilot": false, "locked": true},
        {"name": "Hauptphase",                   "order": "sequential", "copilot": true,  "locked": true}
      ]
    }
  }
}
```

Feld-Semantik pro Teil: `order` (`sequential` = für alle Rater identische
Reihenfolge, `random` = deterministischer Per-User-Shuffle), `copilot`
(Teil-Override unter dem Master-Schalter `copilot.enabled` — der Runner
generiert nur für Co-Pilot-Teile), `locked` (nicht ausgeliefert, bis der
Owner freischaltet).

```bash
# Status inkl. Fortschritt pro Bewerter
curl -H "X-API-Key: $K" https://llars/api/v1/scenarios/42/parts

# Phase freischalten (das IRR-Gate zwischen Kalibrierungsphasen)
curl -X PUT -H "X-API-Key: $K" -H "Content-Type: application/json" \
  -d '{"locked": false}' https://llars/api/v1/scenarios/42/parts/p2

# Items nachladen: part_id ist bei aktiven Teilen PFLICHT
curl -X POST -H "X-API-Key: $K" -H "Content-Type: application/json" \
  -d '{"schema_version": "1.0", "part_id": "p3", "items": [...]}' \
  https://llars/api/v1/scenarios/42/items

# IRR pro Phase (kombinierbar mit ?copilot=with|without)
curl -H "X-API-Key: $K" "https://llars/api/v1/scenarios/42/metrics?part=p1"
```

Der Results-Export (`GET .../results`) trägt auf jeder Zeile die Spalte
`part`; `copilot_metrics` wird zusätzlich pro Teil aggregiert (`per_part`).
`item_ids` bestehender Teile sind über PUT **nicht** änderbar
(Partition-Invariante + Audit-Trail); Umverteilung vor Studienstart =
Szenario neu anlegen.

---

## Validierung & Fehler

Fehlgeschlagene Requests folgen dem LLARS-Standard-Envelope:

```json
{
  "error": "Invalid request body — eval_config.config: ...",
  "details": {"errors": [{"loc": ["eval_config", "config"], "msg": "...", "type": "value_error"}]}
}
```

| Status | Bedingung |
|---|---|
| 400 | Body verletzt das Schema (z.B. `type=rating` mit `SimpleRankingConfig`) |
| 401 | Kein gültiger API-Key / Token |
| 403 | Scope reicht nicht (z.B. `scenario:read`-Key versucht POST) |
| 404 | Szenario / User / Slug nicht gefunden |
| 409 | Owner-Konflikt (Bewerter ist schon Mitglied; letzter Owner darf nicht entfernt werden) |

`eval_config.config` muss zum `eval_config.type` passen (`rating` ↔ `RatingConfig`, `comparison` ↔ `ComparisonConfig`, …). Das Schema kreuzvalidiert beides.

---

## Hinweise

- Items folgen dem **LLARS-Native-Format** (`schema_version: "1.0"`). Reference + Item-Struktur sind in `app/schemas/evaluation_data_schemas.py` ground-truth dokumentiert.
- Der API-Key-Eigentümer wird beim One-Shot-Create automatisch als `manager_role='owner'` gesetzt — er hat danach Vollzugriff über UI und API.
- `referral_link.slug` ist die **Idempotenz-Achse**: derselbe Slug verschoben über mehrere Szenarien hinweg behält die externe URL stabil.
- `DELETE /scenarios/{id}` räumt verwaiste `EvaluationItems` (inkl. Features + Messages) auf — Items, die noch in anderen Szenarien hängen, bleiben erhalten.
