# LLARS Agent Reference

Quick reference for AI coding assistants. See `CLAUDE.md` for full documentation.

## Project

**LLARS** = LLM Assisted Research System
**Stack:** Flask 3.0 + Vue 3.4 + Vuetify 3.5 + MariaDB 11.2 + ChromaDB

```bash
# Start
./start_llars.sh

# Clean restart (DELETES ALL DATA!)
REMOVE_LLARS_VOLUMES=True ./start_llars.sh
```

**URLs:** Frontend `localhost:55080` | API `localhost:55080/api` | Authentik `localhost:55095`

**Test Users:** admin/researcher/viewer/chatbot_manager (all: `admin123`)

---

## Critical Rules

### NEVER CHANGE
- Authentik Client-IDs: `llars-backend`, `llars-frontend`
- Flow-Slug: `llars-api-authentication`
- Authentik Port: 9000

### Backend Routes MUST Use
```python
from decorators.permission_decorator import require_permission
from decorators.error_handler import handle_api_errors, NotFoundError

@bp.route('/api/items/<int:id>')
@require_permission('feature:items:view')
@handle_api_errors(logger_name='items')
def get_item(id):
    item = Item.query.get(id)
    if not item:
        raise NotFoundError(f'Item {id} not found')
    return jsonify({'success': True, 'item': item.to_dict()})
```

### Auth User Access
```python
@authentik_required
def my_route():
    user = g.authentik_user  # User OBJECT, not string!
    user_id = user.id
```

---

## Code Patterns

### Frontend Permission Check
```vue
<script setup>
import { usePermissions } from '@/composables/usePermissions'
const { hasPermission } = usePermissions()
</script>
<template>
  <v-card v-if="hasPermission('feature:ranking:view')">...</v-card>
</template>
```

### Viewport Layout (Full-height pages)
```css
.page-container {
  height: calc(100vh - 94px);  /* 64px AppBar + 30px Footer */
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
```

### Design System Components
- `<LBtn variant="primary|secondary|accent|danger|cancel">` - Buttons
- `<LTag variant="success|info|warning|danger">` - Tags/Chips
- `<LCard>` - Entity cards
- `<LTabs>` - Tab navigation
- `<LActionGroup :actions="['view','edit','delete']">` - Action buttons

---

## Key Files

```
app/
├── auth/decorators.py          # @authentik_required
├── decorators/
│   ├── permission_decorator.py # @require_permission
│   └── error_handler.py        # @handle_api_errors
├── routes/                     # API endpoints
├── services/                   # Business logic
├── db/tables.py               # All models
└── main.py

llars-frontend/src/
├── components/common/          # LBtn, LTag, LCard, etc.
├── composables/               # useAuth, usePermissions
└── views/
```

---

## Database

```bash
# MariaDB access
docker exec -it llars_db_service mariadb -u dev_user -pdev_password_change_me database_llars

# Run SQL
docker exec llars_db_service mariadb -u dev_user -pdev_password_change_me database_llars -e "SHOW TABLES;"
```

---

## Tests

```bash
# Backend
pytest tests/

# Frontend
cd llars-frontend && npm run test:run

# E2E
cd llars-frontend && npx playwright test
```

**Test IDs:** AUTH_001, PERM_001, COMP_BTN_001 (see CLAUDE.md)

---

## Git Commits

```bash
git commit -m "$(cat <<'EOF'
<type>(<scope>): <description>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

**Types:** feat | fix | docs | refactor | chore
**Scopes:** frontend | backend | auth | judge | rag | crawler | db

---

## Common Tasks

### Add new API endpoint
1. Create route in `app/routes/<module>/`
2. Add `@require_permission` + `@handle_api_errors`
3. Register in `app/routes/registry.py`

### Add new Vue component
1. Create in `llars-frontend/src/components/`
2. Use LLARS Design System (LBtn, LTag, etc.)
3. Add test in `tests/components/`

### RAG/Embedding
```python
from services.rag.embedding_model_service import get_best_embedding_for_collection
embeddings, model_id, chroma_name, dims = get_best_embedding_for_collection(collection_id)
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Auth error | `./scripts/setup_authentik.sh` |
| 502 Bad Gateway (prod) | Set `NGINX_EXTERNAL_PORT=80` in `.env` |
| Empty ranking/rating | Check scenario date range + user role |
| Logs | `docker logs -f llars_flask_service` |
