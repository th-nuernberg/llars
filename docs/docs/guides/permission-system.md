# Berechtigungssystem – Status ✅

**Status:** Voll funktionsfähig  
**Datum:** 28.11.2025  
**LLARS Version:** Production

---

## System-Überblick

RBAC mit „deny by default“ über Frontend und Backend:
- Jede Funktion benötigt eine explizite Permission
- Direkte User-Permissions überschreiben Rollen
- Explizites Deny schlägt Grant
- Vollständiges Audit-Log aller Änderungen

---

## Datenbank ✅

**Tabellen (6):**
- `permissions`, `roles`, `role_permissions`
- `user_permissions`, `user_roles`
- `permission_audit_log` (Änderungsverlauf)

**Seed-Daten:**
- 40 Permissions (feature, admin, data)
- 4 Rollen: `admin` (40), `researcher` (19), `chatbot_manager` (14), `evaluator` (13)

---

## Backend-Implementierung ✅

- **Service:** `app/services/permission_service.py`  
  `check_permission()`, `grant_permission()`, `assign_role()` u. a., inkl. Audit-Logging.
- **Decorator:** `app/decorators/permission_decorator.py`  
  `@require_permission`, `@require_any_permission`, `@require_all_permissions`; liest OIDC-Token (Authentik) aus dem `Authorization`-Header und liefert 401/403 bei Verstößen.
- **Routen:** `app/routes/permissions/permission_routes.py` (plus Legacy: `app/routes/PermissionRoutes.py`)  
  `/api/permissions/*` Endpoints (u. a. `my-permissions`, `users-with-roles`, `audit-log`, Rollenverwaltung) geschützt via `admin:*`.

---

## Frontend-Implementierung ✅

- **Composable:** `llars-frontend/src/composables/usePermissions.js`  
  Lädt Permissions + Rollen und stellt `hasPermission/hasAnyPermission/hasAllPermissions` bereit (shared state, kein TTL-Cache).
- **Home-Integration:** `llars-frontend/src/components/Home.vue`  
  Kacheln werden per Permission gefiltert.
- **Admin-Dashboard:** `llars-frontend/src/components/Admin/AdminDashboard.vue`  
  Berechtigungen via Tab `permissions` (`/admin?tab=permissions`).

---

## Verfügbare Permissions (38)

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

## Rollen

- **admin:** alle 40 Permissions – Plattform- und Benutzerverwaltung  
- **researcher:** 19 Permissions – Evaluierung + Prompt Engineering + Markdown Collab + Anonymisierung + KAIMO  
- **chatbot_manager:** 14 Permissions – Chatbots + RAG + Prompt Engineering + Markdown Collab  
- **evaluator:** 13 Permissions – Lesezugriff + ausgewählte Edit-Rechte

---

## Tests ✅

- 40 Permissions und 4 Rollen in der DB vorhanden
- API-Routen registriert; 401 ohne Token, 403 ohne Berechtigung
- Frontend-Guards aktiv; Admin-Dashboard nur für Admins sichtbar

---

## Nutzung

### Für Administratoren
1. `/admin?tab=permissions` öffnen (Adminrolle nötig)  
2. Nutzer suchen → Rolle zuweisen/entziehen  
3. Direkte Permissions vergeben/revozieren bei Bedarf

### Für Entwickler
- Backend-Routen immer mit Decorator schützen:  
  `@require_permission('feature:my_feature:view')`
- Frontend-Checks über `usePermissions()`:
```vue
<template>
  <div v-if="hasPermission('feature:my_feature:view')">
    <!-- Content -->
  </div>
</template>
```
- Neue Permission: in `app/db/db.py` (initialize_permissions) ergänzen, Rollen zuweisen, Backend neu starten.

---

## Sicherheit & Best Practices

- Immer „deny by default“ + Decorators nutzen
- Client-Checks nie allein vertrauen – Server prüft verbindlich
- Audit-Log regelmäßig prüfen
- Prinzip der minimalen Rechte anwenden
- Permission-Anforderungen für neue Features dokumentieren
