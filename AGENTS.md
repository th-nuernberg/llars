# LLARS AI Agent Reference

**Version:** 3.0 | **Stand:** 3. Januar 2026

Kompakte Referenz für AI-Coding-Assistenten. Vollständige Dokumentation: `CLAUDE.md`

---

## Quick Start

```bash
cp .env.template.development .env
./start_llars.sh

# Clean restart (LÖSCHT ALLE DATEN!)
REMOVE_LLARS_VOLUMES=True ./start_llars.sh
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:55080 |
| Backend API | http://localhost:55080/api |
| Authentik | http://localhost:55095 |

| User | Passwort | Rolle |
|------|----------|-------|
| admin | admin123 | admin |
| researcher | admin123 | researcher |
| evaluator | admin123 | evaluator |

---

## Kritische Regeln

### NIEMALS ÄNDERN

| Invariante | Wert |
|------------|------|
| Authentik Client-IDs | `llars-backend`, `llars-frontend` |
| Flow-Slug | `llars-api-authentication` |
| Authentik Port | 9000 |

**Bei Änderung:** Login bricht komplett ab!

### Backend Routes MÜSSEN verwenden

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

### Auth User Zugriff

```python
@authentik_required
def my_route():
    user = g.authentik_user  # User-OBJEKT (nicht String!)
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

### Viewport Layout (Fullscreen-Seiten)

```css
.page-container {
  height: calc(100vh - 94px);  /* 64px AppBar + 30px Footer */
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
```

### Design System Komponenten

```vue
<LBtn variant="primary|secondary|accent|danger|cancel">
<LTag variant="success|info|warning|danger">
<LCard title="Titel" icon="mdi-robot">
<LTabs v-model="tab" :tabs="[...]" />
<LActionGroup :actions="['view','edit','delete']" />
```

---

## Wichtige Dateien

```
app/
├── auth/decorators.py          # @authentik_required
├── decorators/
│   ├── permission_decorator.py # @require_permission
│   └── error_handler.py        # @handle_api_errors
├── routes/                     # API Endpoints
├── services/                   # Business Logic
└── db/tables.py               # Alle Models

llars-frontend/src/
├── components/common/          # LBtn, LTag, LCard, etc.
├── composables/               # useAuth, usePermissions
└── views/
```

---

## Datenbank

```bash
# MariaDB Zugriff
docker exec -it llars_db_service mariadb -u dev_user -pdev_password_change_me database_llars

# SQL ausführen
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

## Workflow für komplexe Tasks

```
1. Problem analysieren → Unabhängige Teilaufgaben identifizieren
2. TodoWrite nutzen bei >2 Schritten
3. Agents parallelisieren für unabhängige Tasks
4. Nach Ausführung validieren: Dateien existieren? Änderungen korrekt?
5. CLAUDE.md aktualisieren bei signifikanten Änderungen
```

---

## Häufige Aufgaben

### Neue API Route hinzufügen

1. Route in `app/routes/<module>/` erstellen
2. `@require_permission` + `@handle_api_errors` hinzufügen
3. In `app/routes/registry.py` registrieren

### Neue Vue Komponente hinzufügen

1. In `llars-frontend/src/components/` erstellen
2. LLARS Design System nutzen (LBtn, LTag, etc.)
3. Test in `tests/components/` hinzufügen

### RAG/Embedding

```python
from services.rag.embedding_model_service import get_best_embedding_for_collection
embeddings, model_id, chroma_name, dims = get_best_embedding_for_collection(collection_id)
```

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| Auth-Fehler | `./scripts/setup_authentik.sh` |
| 502 Bad Gateway (Prod) | `NGINX_EXTERNAL_PORT=80` in `.env` |
| Ranking/Rating leer | Zeitraum + User-Rolle prüfen |
| Logs | `docker logs -f llars_flask_service` |

---

**Vollständige Dokumentation:** `CLAUDE.md`
