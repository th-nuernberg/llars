# [Project Name] - Implementation

!!! info "🔧 Status: In Progress"
    This project is currently being **implemented**.
    See [Progress Template](progress-template.md) for details.

**Concept:** [Concept Template](konzept-template.md)  
**Created:** YYYY-MM-DD  
**Author:** [Name]

---

## Overview

This file describes the technical implementation of the concept. It contains concrete steps and placeholders for code.

### Implementation Order

1. [ ] Database migrations
2. [ ] Backend services
3. [ ] Backend routes
4. [ ] WebSocket events
5. [ ] Frontend components
6. [ ] Integration & testing

---

## Dependencies

### Python (Backend)

```bash
# If new packages are required
pip install package-name
```

Add to `requirements.txt`:
```
package-name==1.0.0
```

### JavaScript (Frontend)

```bash
cd llars-frontend
npm install package-name
```

---

## Database

### New Models

**File:** `app/db/tables.py` (or split model file)

> Add new models here and document fields, relationships, and `to_dict`.

### Migration

After adding models:

```bash
docker compose exec backend-flask-service flask db migrate -m "Add ResourceName table"
docker compose exec backend-flask-service flask db upgrade
```

---

## Backend Services

### Service Class

**File:** `app/services/resource/resource_service.py`

> Implement CRUD + business logic here. Keep routes thin.

---

## Backend Routes

**File:** `app/routes/resource/resource_routes.py`

> Add API endpoints with `@require_permission` and `@handle_api_errors`.

---

## WebSocket Events (optional)

If live updates are needed:

- Define events in `socketio_handlers`
- Document event names and payloads

---

## Frontend

### Components

**Folder:** `llars-frontend/src/components/`

> Add Vue components and keep state logic in composables.

### API Integration

**File:** `llars-frontend/src/services/`

> Add REST API calls and error handling.

---

## Testing

- Backend: `pytest tests/`
- Frontend: `npm run test:run`
- E2E: `npx playwright test`

---

## Checklist

- [ ] API endpoints implemented
- [ ] Permissions set
- [ ] Frontend wired
- [ ] Tests green
- [ ] Docs updated

---

## Notes

Document any implementation decisions, deviations, or follow‑ups here.
