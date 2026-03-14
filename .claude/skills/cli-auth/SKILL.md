---
name: cli-auth
description: Authenticate with LLARS API from CLI and inspect pages/API responses. Use when debugging frontend issues, checking API responses, or needing to view what a page returns.
---

# LLARS CLI Authentication & Page Inspection

Use this to authenticate and make API requests from CLI when debugging frontend issues.

## Quick Auth (System Admin API Key)

The fastest way - uses `X-API-Key` header with the system admin key from `.env`:

```bash
source .env

# Check any API endpoint as admin
curl -s http://localhost:55080/api/scenarios/14 \
  -H "X-API-Key: $SYSTEM_ADMIN_API_KEY" | jq .

# Get scenario stats
curl -s http://localhost:55080/api/scenarios/14/stats \
  -H "X-API-Key: $SYSTEM_ADMIN_API_KEY" | jq .

# Get scenario threads (data tab)
curl -s "http://localhost:55080/api/scenarios/14/threads?per_page=100" \
  -H "X-API-Key: $SYSTEM_ADMIN_API_KEY" | jq .
```

**Important:** The System Admin API Key only works on endpoints decorated with `@api_key_or_token_required`, `@require_permission`, or `@system_api_key_required`. Most scenario/evaluation routes use `@require_permission` which accepts API keys.

Routes with `@authentik_required` (strict token-only) need a Bearer token instead.

## Bearer Token Auth (Authentik Login)

For endpoints requiring a real user token:

```bash
# Login and extract token
TOKEN=$(curl -s -X POST http://localhost:55080/auth/authentik/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')

# Use token
curl -s http://localhost:55080/api/scenarios/14 \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### Available Test Users

| User | Password | Role |
|------|----------|------|
| admin | admin123 | admin |
| researcher | admin123 | researcher |
| evaluator | admin123 | evaluator |
| chatbot_manager | admin123 | chatbot_manager |

## Common Debug Endpoints

```bash
# Scenario detail (thread_count, stats, config)
/api/scenarios/{id}

# Scenario stats (rater_stats, evaluator_stats, agreement metrics)
/api/scenarios/{id}/stats

# Scenario threads (data tab items with status)
/api/scenarios/{id}/threads?per_page=100

# Current user info
/api/users/me

# Available LLM models
/api/llm/models/available
```

## Viewing Frontend Pages via CLI

Frontend pages are Vue SPA - you cannot `curl` them directly. Instead:

1. **Check API responses** that feed the page (see endpoints above)
2. **Use WebFetch tool** for static content (won't work for authenticated SPAs)
3. **Check browser console** for JS errors: user opens DevTools (F12) > Console
4. **Check Flask logs** for backend errors:
   ```bash
   docker logs --tail 50 llars_flask_service 2>&1 | grep -i error
   ```

## Debugging Workflow

When a page "doesn't display correctly":

1. **Check Flask logs** for 4xx/5xx errors on the relevant API endpoints
2. **Curl the API endpoints** that feed the page and inspect the response
3. **Check the stats cache** - invalidate if stale:
   ```sql
   docker exec llars_db_service mariadb -u dev_user -p'dev_password_change_me' database_llars \
     -e "UPDATE scenario_stats_cache SET computed_at = '2000-01-01' WHERE scenario_id = {ID};"
   ```
4. **Restart Flask** if code was changed:
   ```bash
   docker restart llars_flask_service
   ```
5. **Hard refresh** browser: Cmd+Shift+R (clears cached JS/CSS)
