# Berechtigungssystem – Status ✅

**Status:** Voll funktionsfähig  
**Datum:** 21.11.2025  
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
- 17 Permissions (feature, admin, data)
- 3 Rollen: `admin` (17), `researcher` (11), `viewer` (5)

---

## Backend-Implementierung ✅

- **Service:** `app/services/permission_service.py`  
  `check_permission()`, `grant_permission()`, `assign_role()` u. a., inkl. Audit-Logging.
- **Decorator:** `app/decorators/permission_decorator.py`  
  `@require_permission`, `@require_any_permission`, `@require_all_permissions`; liest OIDC-Token (Authentik) aus dem `Authorization`-Header und liefert 401/403 bei Verstößen.
- **Routen:** `app/routes/PermissionRoutes.py`  
  8 Endpoints (`/api/permissions/*`) geschützt mit `admin:permissions:manage`.

---

## Frontend-Implementierung ✅

- **Composable:** `llars-frontend/src/composables/usePermissions.js`  
  Lädt Permissions, `hasPermission/hasRole/isAdmin`, 5-Minuten-Caching.
- **Home-Integration:** `llars-frontend/src/components/Home.vue`  
  Kacheln werden per Permission gefiltert.
- **Admin-Dashboard:** `llars-frontend/src/components/AdminPermissions.vue`  
  Tabs für Nutzer, Rollen, Permissions; Echtzeit-Zuweisung. Route `/AdminPermissions` ist geschützt (Router-Guard + Permission-Check).

---

## Verfügbare Permissions (17)

**Feature (12):**
```
feature:mail_rating:{view,edit,delete}
feature:ranking:{view,edit}
feature:rating:{view,edit}
feature:prompt_engineering:{view,edit}
feature:comparison:{view,edit}
feature:history_generation:view
```

**Admin (3):**
```
admin:permissions:manage
admin:roles:manage
admin:users:view
```

**Data (2):**
```
data:export
data:import
```

---

## Rollen

- **admin:** alle 17 Permissions – Plattform- und Benutzerverwaltung  
- **researcher:** 11 Permissions (alle View/Edit ohne Admin/Data) – aktive Forschung  
- **viewer:** 5 View-Permissions – Lesezugriff für Reviewer

---

## Tests ✅

- 17 Permissions und 3 Rollen in der DB vorhanden
- 8 API-Routen registriert; 401 ohne Token, 403 ohne Berechtigung
- Frontend-Guards aktiv; Admin-Dashboard nur für Admins sichtbar

---

## Nutzung

### Für Administratoren
1. `/AdminPermissions` öffnen (Adminrolle nötig)  
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
