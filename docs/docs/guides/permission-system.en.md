# Permission System – Status ✅

**Status:** Fully operational  
**Date:** 2025-11-28  
**LLARS Version:** Production

---

## System Overview

RBAC with “deny by default” across frontend and backend:
- Every feature requires an explicit permission
- Direct user permissions override roles
- Explicit deny beats grant
- Complete audit log of all changes

---

## Database ✅

**Tables (6):**
- `permissions`, `roles`, `role_permissions`
- `user_permissions`, `user_roles`
- `permission_audit_log` (change history)

**Seed data:**
- 40 permissions (feature, admin, data)
- 4 roles: `admin` (40), `researcher` (19), `chatbot_manager` (14), `evaluator` (13)

---

## Backend Implementation ✅

- **Service:** `app/services/permission_service.py`  
  `check_permission()`, `grant_permission()`, `assign_role()`, etc., including audit logging.
- **Decorator:** `app/decorators/permission_decorator.py`  
  `@require_permission`, `@require_any_permission`, `@require_all_permissions`; reads OIDC token (Authentik) from the `Authorization` header and returns 401/403 on violations.
- **Routes:** `app/routes/permissions/permission_routes.py` (plus legacy: `app/routes/PermissionRoutes.py`)  
  `/api/permissions/*` endpoints (e.g., `my-permissions`, `users-with-roles`, `audit-log`, role management) protected via `admin:*`.

---

## Frontend Implementation ✅

- **Composable:** `llars-frontend/src/composables/usePermissions.js`  
  Loads permissions + roles and provides `hasPermission/hasAnyPermission/hasAllPermissions` (shared state, no TTL cache).
- **Home integration:** `llars-frontend/src/components/Home.vue`  
  Tiles are filtered by permission.
- **Admin dashboard:** `llars-frontend/src/components/Admin/AdminDashboard.vue`  
  Permissions via tab `permissions` (`/admin?tab=permissions`).

---

## Available Permissions (38)

**Feature (28):**
```
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
feature:rag:view
feature:rag:edit
feature:rag:delete
feature:rag:share
feature:chatbots:view
feature:chatbots:edit
feature:chatbots:delete
feature:chatbots:advanced
feature:chatbots:share
feature:anonymize:view
feature:judge:view
feature:judge:edit
feature:oncoco:view
feature:oncoco:edit
feature:kaimo:view
feature:kaimo:edit
```

**Admin (6):**
```
admin:permissions:manage
admin:users:manage
admin:roles:manage
admin:system:configure
admin:kaimo:manage
admin:kaimo:results
```

**Data (3):**
```
data:export
data:import
data:delete
```

---

## Roles

- **admin:** all 40 permissions – platform + user management  
- **researcher:** 19 permissions – evaluation + prompt engineering + markdown collab + anonymization + KAIMO  
- **chatbot_manager:** 14 permissions – chatbots + RAG + prompt engineering + markdown collab  
- **evaluator:** 13 permissions – read access + selected edit rights

---

## Tests ✅

- 40 permissions and 4 roles exist in the DB
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
- New permission: add in `app/db/db.py` (`initialize_permissions`), assign to roles, restart backend.

---

## Security & Best Practices

- Always use “deny by default” + decorators
- Never rely on client checks alone – server enforcement is mandatory
- Review audit logs regularly
- Apply the principle of least privilege
- Document permission requirements for new features
