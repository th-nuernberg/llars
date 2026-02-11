# Permission System – Status ✅

**Status:** Fully operational  
**Date:** 2026-02-10  
**LLARS Version:** Production

---

## System Overview

RBAC with “deny by default” across frontend and backend:
- Every feature requires an explicit permission
- Direct user permissions override roles
- Explicit deny beats grant
- Complete audit log of all changes
- System Admin API Key (`X-API-Key`) can bypass permission checks for integrations

---

## Database ✅

**Tables (6):**
- `permissions`, `roles`, `role_permissions`
- `user_permissions`, `user_roles`
- `permission_audit_log` (change history)

**Seed data:**
- 53 permissions (41 feature, 8 admin, 4 data)
- 5 roles: `admin` (53), `researcher` (31), `chatbot_manager` (21), `evaluator` (20), `ijcai_reviewer` (20)
- Optional: legacy role `viewer` is auto-synced with `evaluator` if present

---

## Backend Implementation ✅

- **Service:** `app/services/permission_service.py`  
  `check_permission()`, `grant_permission()`, `assign_role()`, etc., including audit logging.
- **Decorator:** `app/decorators/permission_decorator.py`  
  `@require_permission`, `@require_any_permission`, `@require_all_permissions`; uses `Authorization: Bearer` (OIDC JWT via Authentik), checks locked/deleted accounts, and returns 401/403 on violations. `X-API-Key` can bypass checks for system integrations.
- **Routes:** `app/routes/permissions/permission_routes.py` (plus legacy: `app/routes/PermissionRoutes.py`)  
  `/api/permissions/*` endpoints (e.g., `my-permissions`, `users-with-roles`, `audit-log`, role management). Admin endpoints are protected with `admin:*`, while `my-permissions` uses `@authentik_required` only.

---

## Frontend Implementation ✅

- **Composable:** `llars-frontend/src/composables/usePermissions.js`  
  Loads permissions + roles and provides `hasPermission/hasAnyPermission/hasAllPermissions` (shared state, no TTL cache).
- **Home integration:** `llars-frontend/src/components/Home.vue`  
  Tiles are filtered by permission.
- **Admin dashboard:** `llars-frontend/src/components/Admin/AdminDashboard.vue`  
  Permissions via tab `permissions` (`/admin?tab=permissions`).

---

## Available Permissions (53)

**Feature (41):**
```
feature:mail_rating:view
feature:mail_rating:edit
feature:ranking:view
feature:ranking:edit
feature:rating:view
feature:rating:edit
feature:comparison:view
feature:comparison:edit
feature:authenticity:view
feature:authenticity:edit
feature:prompt_engineering:view
feature:prompt_engineering:edit
feature:markdown_collab:view
feature:markdown_collab:edit
feature:markdown_collab:share
feature:latex_collab:view
feature:latex_collab:edit
feature:latex_collab:share
feature:latex_collab:ai
feature:rag:view
feature:rag:edit
feature:rag:delete
feature:rag:share
feature:chatbots:view
feature:chatbots:edit
feature:chatbots:delete
feature:chatbots:advanced
feature:chatbots:share
feature:llm:view
feature:anonymize:view
feature:judge:view
feature:judge:edit
feature:oncoco:view
feature:oncoco:edit
feature:kaimo:view
feature:kaimo:edit
feature:generation:view
feature:generation:create
feature:generation:manage
feature:generation:export
feature:generation:to_scenario
```

**Admin (8):**
```
admin:permissions:manage
admin:users:manage
admin:roles:manage
admin:system:configure
admin:referral:manage
admin:field_prompts:manage
admin:kaimo:manage
admin:kaimo:results
```

**Data (4):**
```
data:export
data:import
data:manage_scenarios
data:delete
```

---

## Roles

- **admin:** all permissions (currently 53) – platform + user management  
- **researcher:** 31 permissions – evaluation, prompt engineering, batch generation, Markdown/LaTeX collab, anonymization, KAIMO, scenario import  
- **chatbot_manager:** 21 permissions – chatbots, RAG, prompt engineering, batch generation (view/create), Markdown/LaTeX collab  
- **evaluator:** 20 permissions – evaluation, read access, selected edit rights, RAG/chatbots read-only, KAIMO edit  
- **ijcai_reviewer:** 20 permissions – IJCAI demo: prompting, batch generation, scenarios, evaluation  
- **viewer (legacy):** auto-synced with `evaluator` when present

---

## Tests ✅

- 53 permissions and 5 roles exist in the DB (plus optional `viewer`)
- API routes registered; 401 without token, 403 without permission
- Frontend guards active; admin dashboard visible to admins only

---

## Usage

### For Administrators
1. Open `/admin?tab=permissions` (admin role required)  
2. Search user -> assign/remove roles  
3. Grant/revoke direct permissions as needed

### For Developers
- Always protect backend routes with a decorator:  
  `@require_permission('feature:my_feature:view')`
- Frontend checks via `usePermissions()`:
```vue
<template>
  <div v-if="hasPermission('feature:my_feature:view')">
    <!-- Content -->
  </div>
</template>
```
- New permission: add in `app/db/seeders/permissions.py`, assign to roles, restart backend.

---

## Security & Best Practices

- Always use “deny by default” + decorators
- Never rely on client checks alone – server enforcement is mandatory
- Review audit logs regularly
- Apply the principle of least privilege
- Document permission requirements for new features
