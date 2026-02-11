# Berechtigungssystem – Status ✅

**Status:** Voll funktionsfähig  
**Datum:** 10.02.2026  
**LLARS Version:** Production

---

## System-Überblick

RBAC mit „deny by default“ über Frontend und Backend:
- Jede Funktion benötigt eine explizite Permission
- Direkte User-Permissions überschreiben Rollen
- Explizites Deny schlägt Grant
- Vollständiges Audit-Log aller Änderungen
- System Admin API Key (`X-API-Key`) kann Permission-Checks für Integrationen umgehen

---

## Datenbank ✅

**Tabellen (6):**
- `permissions`, `roles`, `role_permissions`
- `user_permissions`, `user_roles`
- `permission_audit_log` (Änderungsverlauf)

**Seed-Daten:**
- 53 Permissions (41 feature, 8 admin, 4 data)
- 5 Rollen: `admin` (53), `researcher` (31), `chatbot_manager` (21), `evaluator` (20), `ijcai_reviewer` (20)
- Optional: Legacy-Rolle `viewer` wird bei Bedarf automatisch mit `evaluator` synchronisiert

---

## Backend-Implementierung ✅

- **Service:** `app/services/permission_service.py`  
  `check_permission()`, `grant_permission()`, `assign_role()` u. a., inkl. Audit-Logging.
- **Decorator:** `app/decorators/permission_decorator.py`  
  `@require_permission`, `@require_any_permission`, `@require_all_permissions`; nutzt `Authorization: Bearer` (OIDC JWT via Authentik), prüft gesperrte/gelöschte Accounts und liefert 401/403 bei Verstößen. `X-API-Key` kann die Prüfung für System-Integrationen umgehen.
- **Routen:** `app/routes/permissions/permission_routes.py` (plus Legacy: `app/routes/PermissionRoutes.py`)  
  `/api/permissions/*` Endpoints (u. a. `my-permissions`, `users-with-roles`, `audit-log`, Rollenverwaltung). Admin-Endpunkte sind über `admin:*` geschützt, `my-permissions` nutzt nur `@authentik_required`.

---

## Frontend-Implementierung ✅

- **Composable:** `llars-frontend/src/composables/usePermissions.js`  
  Lädt Permissions + Rollen und stellt `hasPermission/hasAnyPermission/hasAllPermissions` bereit (shared state, kein TTL-Cache).
- **Home-Integration:** `llars-frontend/src/components/Home.vue`  
  Kacheln werden per Permission gefiltert.
- **Admin-Dashboard:** `llars-frontend/src/components/Admin/AdminDashboard.vue`  
  Berechtigungen via Tab `permissions` (`/admin?tab=permissions`).

---

## Verfügbare Permissions (53)

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

## Rollen

- **admin:** alle Permissions (aktuell 53) – Plattform- und Benutzerverwaltung  
- **researcher:** 31 Permissions – Evaluierung, Prompt Engineering, Batch Generation, Markdown/LaTeX Collab, Anonymisierung, KAIMO, Szenarien-Import  
- **chatbot_manager:** 21 Permissions – Chatbots, RAG, Prompt Engineering, Batch Generation (view/create), Markdown/LaTeX Collab  
- **evaluator:** 20 Permissions – Evaluierung, Lesen, ausgewählte Edit-Rechte, RAG/Chatbots read-only, KAIMO bearbeiten  
- **ijcai_reviewer:** 20 Permissions – IJCAI-Demo: Prompting, Batch Generation, Szenarien, Evaluation
- **viewer (legacy):** wird bei Existenz automatisch mit `evaluator` synchronisiert

---

## Tests ✅

- 53 Permissions und 5 Rollen in der DB vorhanden (plus optional `viewer`)
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
- Neue Permission: in `app/db/seeders/permissions.py` ergänzen, Rollen zuweisen, Backend neu starten.

---

## Sicherheit & Best Practices

- Immer „deny by default“ + Decorators nutzen
- Client-Checks nie allein vertrauen – Server prüft verbindlich
- Audit-Log regelmäßig prüfen
- Prinzip der minimalen Rechte anwenden
- Permission-Anforderungen für neue Features dokumentieren
