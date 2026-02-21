# Security Testanforderungen: Berechtigungen (RBAC)

**Version:** 1.1 | **Stand:** 30. Dezember 2025

**Status:** ✅ IMPLEMENTIERT - Tests in `tests/unit/services/permission/test_permission_service.py`

---

## Übersicht

Dieses Dokument beschreibt alle Tests für das LLARS Permission System (RBAC).

**Sicherheitsmodell:** Deny-by-Default | User überschreibt Rolle | Deny schlägt Grant

---

## 1. Alle Permissions (43 Total)

### Feature Permissions (26)

| Permission | Beschreibung | Rollen |
|------------|--------------|--------|
| `feature:ranking:view` | Ranking ansehen | admin, researcher, evaluator |
| `feature:ranking:edit` | Ranking bearbeiten | admin, researcher |
| `feature:rating:view` | Rating ansehen | admin, researcher, evaluator |
| `feature:rating:edit` | Rating bearbeiten | admin, researcher |
| `feature:comparison:view` | Comparison ansehen | admin, researcher, evaluator |
| `feature:comparison:edit` | Comparison bearbeiten | admin, researcher |
| `feature:authenticity:view` | Authenticity ansehen | admin, researcher, evaluator |
| `feature:authenticity:edit` | Authenticity bearbeiten | admin, researcher, evaluator |
| `feature:prompt_engineering:view` | Prompt Eng. ansehen | admin, researcher, chatbot_manager, evaluator |
| `feature:prompt_engineering:edit` | Prompt Eng. bearbeiten | admin, researcher, chatbot_manager |
| `feature:markdown_collab:view` | Markdown ansehen | admin, researcher, chatbot_manager, evaluator |
| `feature:markdown_collab:edit` | Markdown bearbeiten | admin, researcher, chatbot_manager |
| `feature:markdown_collab:share` | Markdown teilen | admin, researcher, chatbot_manager |
| `feature:latex_collab:view` | LaTeX ansehen | admin, researcher, chatbot_manager, evaluator |
| `feature:latex_collab:edit` | LaTeX bearbeiten | admin, researcher, chatbot_manager |
| `feature:latex_collab:share` | LaTeX teilen | admin, researcher, chatbot_manager |
| `feature:latex_collab:ai` | LaTeX AI nutzen | admin, researcher, chatbot_manager |
| `feature:rag:view` | RAG ansehen | admin, chatbot_manager, evaluator |
| `feature:rag:edit` | RAG bearbeiten | admin, chatbot_manager |
| `feature:rag:delete` | RAG löschen | admin, chatbot_manager |
| `feature:rag:share` | RAG teilen | admin, chatbot_manager |
| `feature:chatbots:view` | Chatbots ansehen | admin, researcher, chatbot_manager, evaluator |
| `feature:chatbots:edit` | Chatbots bearbeiten | admin, chatbot_manager |
| `feature:chatbots:delete` | Chatbots löschen | admin, chatbot_manager |
| `feature:chatbots:advanced` | Advanced Agent Modes | admin, chatbot_manager |
| `feature:chatbots:share` | Chatbots teilen | admin, chatbot_manager |
| `feature:anonymize:view` | Anonymize nutzen | admin, researcher, evaluator |
| `feature:judge:view` | Judge ansehen | admin |
| `feature:judge:edit` | Judge bearbeiten | admin |
| `feature:oncoco:view` | OnCoCo ansehen | admin |
| `feature:oncoco:edit` | OnCoCo bearbeiten | admin |
| `feature:kaimo:view` | KAIMO ansehen | admin, researcher, evaluator |
| `feature:kaimo:edit` | KAIMO bearbeiten | admin, researcher, evaluator |

### Admin Permissions (10)

| Permission | Beschreibung | Rollen |
|------------|--------------|--------|
| `admin:permissions:manage` | Permissions verwalten | admin |
| `admin:users:manage` | User verwalten | admin |
| `admin:roles:manage` | Rollen verwalten | admin |
| `admin:system:configure` | System konfigurieren | admin |
| `admin:kaimo:manage` | KAIMO Cases verwalten | admin |
| `admin:kaimo:results` | KAIMO Ergebnisse sehen | admin |

### Data Permissions (3)

| Permission | Beschreibung | Rollen |
|------------|--------------|--------|
| `data:export` | Daten exportieren | admin |
| `data:import` | Daten importieren | admin |
| `data:delete` | Daten löschen | admin |

---

## 2. Permission Check Tests

**Tests:** `tests/unit/services/permission/test_permission_service.py`

### Deny-by-Default Tests

| ID | Test | Erwartung | Art | Status |
|----|------|-----------|-----|--------|
| PERM-001 | Unbekannte Permission | Return False | Unit | ✅ |
| PERM-002 | Keine Rolle, keine Permission | Return False | Unit | ✅ |
| PERM-003 | Locked User | Return False | Unit | ✅ |
| PERM-004 | Deleted User | Return False | Unit | ✅ |

### Admin Tests

| ID | Test | Erwartung | Art | Status |
|----|------|-----------|-----|--------|
| PERM-010 | Admin hat alle Permissions | Return True für alles | Unit | ✅ |
| PERM-011 | Admin bypass | Keine Einzel-Check nötig | Unit | ✅ |

### Role Tests

| ID | Test | Erwartung | Art | Status |
|----|------|-----------|-----|--------|
| PERM-020 | Researcher hat view Permissions | Return True | Unit | ✅ |
| PERM-021 | Researcher keine Admin Permissions | Return False | Unit | ✅ |
| PERM-022 | Evaluator nur view Permissions | Return True für view | Unit | ✅ |
| PERM-023 | Evaluator keine edit Permissions | Return False | Unit | ✅ |
| PERM-024 | Chatbot_Manager chatbot Permissions | Return True | Unit | ✅ |
| PERM-025 | Chatbot_Manager keine ranking | Return False | Unit | ✅ |

### Override Tests

| ID | Test | Erwartung | Art | Status |
|----|------|-----------|-----|--------|
| PERM-030 | User Grant > Role Deny | Return True | Unit | ✅ |
| PERM-031 | User Deny > Role Grant | Return False | Unit | ✅ |
| PERM-032 | Explicit Deny > Implicit Grant | Return False | Unit | ✅ |

### Unit Test-Code

```python
# tests/unit/services/permission/test_check_permission.py
import pytest
from app.services.permission_service import PermissionService


class TestPermissionCheck:
    """Permission Check Tests"""

    @pytest.fixture
    def service(self, app, db):
        with app.app_context():
            return PermissionService()

    # =========================================================================
    # DENY-BY-DEFAULT TESTS
    # =========================================================================

    def test_PERM_001_unknown_permission_denied(self, app, service, mock_user):
        """Unbekannte Permission wird verweigert"""
        with app.app_context():
            result = service.check_permission(mock_user, 'unknown:permission:here')
            assert result is False

    def test_PERM_003_locked_user_denied(self, app, service, db):
        """Gesperrter User wird verweigert"""
        from app.db.models import User

        locked_user = User(username='locked', is_active=False)
        db.session.add(locked_user)
        db.session.commit()

        with app.app_context():
            result = service.check_permission(locked_user, 'feature:ranking:view')
            assert result is False

    def test_PERM_004_deleted_user_denied(self, app, service, db):
        """Gelöschter User wird verweigert"""
        from app.db.models import User
        from datetime import datetime

        deleted_user = User(username='deleted', deleted_at=datetime.now())
        db.session.add(deleted_user)
        db.session.commit()

        with app.app_context():
            result = service.check_permission(deleted_user, 'feature:ranking:view')
            assert result is False

    # =========================================================================
    # ADMIN TESTS
    # =========================================================================

    def test_PERM_010_admin_has_all_permissions(self, app, service, admin_user):
        """Admin hat alle Permissions"""
        permissions_to_test = [
            'feature:ranking:view',
            'feature:chatbots:edit',
            'admin:permissions:manage',
            'admin:system:configure',
            'unknown:random:permission'  # Auch unbekannte!
        ]

        with app.app_context():
            for perm in permissions_to_test:
                assert service.check_permission(admin_user, perm) is True

    # =========================================================================
    # ROLE TESTS
    # =========================================================================

    def test_PERM_020_researcher_has_view_permissions(self, app, service, researcher_user):
        """Researcher hat view Permissions"""
        with app.app_context():
            assert service.check_permission(researcher_user, 'feature:ranking:view') is True
            assert service.check_permission(researcher_user, 'feature:rating:view') is True
            assert service.check_permission(researcher_user, 'feature:prompt_engineering:view') is True

    def test_PERM_021_researcher_no_admin_permissions(self, app, service, researcher_user):
        """Researcher hat keine Admin Permissions"""
        with app.app_context():
            assert service.check_permission(researcher_user, 'admin:permissions:manage') is False
            assert service.check_permission(researcher_user, 'admin:users:manage') is False

    def test_PERM_023_evaluator_no_edit_permissions(self, app, service, mock_user):
        """Evaluator hat keine edit Permissions"""
        with app.app_context():
            assert service.check_permission(mock_user, 'feature:ranking:edit') is False
            assert service.check_permission(mock_user, 'feature:rating:edit') is False
```

---

## 3. API Route Protection Tests

**Tests:** `tests/integration/api/test_route_protection.py`

### Auth Decorator Tests

| ID | Test | Erwartung | Art | Status |
|----|------|-----------|-----|--------|
| ROUTE-001 | Kein Auth Header | 401 Unauthorized | Integration | ✅ |
| ROUTE-002 | Invalid Token | 401 Unauthorized | Integration | ✅ |
| ROUTE-003 | Expired Token | 401 Unauthorized | Integration | ✅ |
| ROUTE-004 | Valid Token | 200 OK | Integration | ✅ |
| ROUTE-005 | System API Key | Bypass, 200 OK | Integration | ✅ |

### Permission Decorator Tests

| ID | Test | Erwartung | Art | Status |
|----|------|-----------|-----|--------|
| ROUTE-010 | Permission granted | 200 OK | Integration | ✅ |
| ROUTE-011 | Permission denied | 403 Forbidden | Integration | ✅ |
| ROUTE-012 | Admin override | 200 OK | Integration | ✅ |

### Integration Test-Code

```python
# tests/integration/api/test_route_protection.py
import pytest


class TestRouteProtection:
    """Route Protection Tests"""

    def test_ROUTE_001_no_auth_header(self, client):
        """Kein Auth Header gibt 401"""
        response = client.get('/api/users/me')
        assert response.status_code == 401

    def test_ROUTE_002_invalid_token(self, client):
        """Ungültiger Token gibt 401"""
        response = client.get(
            '/api/users/me',
            headers={'Authorization': 'Bearer invalid-token'}
        )
        assert response.status_code == 401

    def test_ROUTE_004_valid_token(self, authenticated_client):
        """Gültiger Token erlaubt Zugriff"""
        response = authenticated_client.get('/api/users/me')
        assert response.status_code == 200

    def test_ROUTE_011_permission_denied(self, authenticated_client_evaluator):
        """Fehlende Permission gibt 403"""
        # Evaluator versucht Admin-Route
        response = authenticated_client_evaluator.get('/api/admin/users')
        assert response.status_code == 403

    def test_ROUTE_012_admin_override(self, authenticated_client_admin):
        """Admin hat immer Zugriff"""
        response = authenticated_client_admin.get('/api/admin/users')
        assert response.status_code == 200
```

---

## 4. Frontend Permission Check Tests

### hasPermission Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| FE-PERM-001 | hasPermission(granted) | Return True | Unit |
| FE-PERM-002 | hasPermission(denied) | Return False | Unit |
| FE-PERM-003 | hasAnyPermission OR | Return True wenn einer | Unit |
| FE-PERM-004 | hasAllPermissions AND | Return True wenn alle | Unit |
| FE-PERM-005 | hasRole(granted) | Return True | Unit |
| FE-PERM-006 | hasRole(denied) | Return False | Unit |
| FE-PERM-007 | isAdmin computed | Return True für Admin | Unit |

### Unit Test-Code

```javascript
// llars-frontend/src/composables/__tests__/usePermissions.test.js
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { usePermissions } from '../usePermissions'

describe('usePermissions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('hasPermission', () => {
    it('FE-PERM-001: returns true for granted permission', () => {
      // Mock permissions
      const { hasPermission } = usePermissions()
      // Setup: User hat 'feature:ranking:view'

      expect(hasPermission('feature:ranking:view')).toBe(true)
    })

    it('FE-PERM-002: returns false for denied permission', () => {
      const { hasPermission } = usePermissions()

      expect(hasPermission('admin:permissions:manage')).toBe(false)
    })
  })

  describe('hasAnyPermission', () => {
    it('FE-PERM-003: returns true if any permission granted', () => {
      const { hasAnyPermission } = usePermissions()

      expect(hasAnyPermission('feature:ranking:view', 'admin:permissions:manage')).toBe(true)
    })
  })

  describe('hasAllPermissions', () => {
    it('FE-PERM-004: returns true only if all granted', () => {
      const { hasAllPermissions } = usePermissions()

      expect(hasAllPermissions('feature:ranking:view', 'feature:rating:view')).toBe(true)
      expect(hasAllPermissions('feature:ranking:view', 'admin:permissions:manage')).toBe(false)
    })
  })
})
```

---

## 5. Permission Grant/Revoke Tests

### Grant Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| GRANT-001 | Permission grant | User hat Permission | Integration |
| GRANT-002 | Grant mit Audit Log | Log-Eintrag erstellt | Integration |
| GRANT-003 | Duplicate Grant | Kein Fehler | Integration |

### Revoke Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| REVOKE-001 | Permission revoke | User hat keine Permission | Integration |
| REVOKE-002 | Revoke mit Audit Log | Log-Eintrag erstellt | Integration |
| REVOKE-003 | Revoke non-existent | Kein Fehler | Integration |

### Role Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ROLE-001 | Role assign | User hat Rolle | Integration |
| ROLE-002 | Role unassign | User hat keine Rolle | Integration |
| ROLE-003 | Multiple Roles | Alle Permissions kombiniert | Integration |

---

## Checkliste für manuelle Tests

### Permission System
- [ ] Deny-by-Default funktioniert
- [ ] Admin hat alle Permissions
- [ ] User Deny > Role Grant
- [ ] Locked User wird verweigert
- [ ] Deleted User wird verweigert

### Route Protection
- [ ] Alle Routes mit @authentik_required
- [ ] Alle kritischen Routes mit @require_permission
- [ ] 401 bei fehlendem Token
- [ ] 403 bei fehlender Permission

### Frontend
- [ ] hasPermission funktioniert
- [ ] v-if="hasPermission(...)" blendet Elemente aus
- [ ] Router Guards prüfen Permissions

### Audit Log
- [ ] Grant wird geloggt
- [ ] Revoke wird geloggt
- [ ] Role Assign wird geloggt

---

**Letzte Aktualisierung:** 30. Dezember 2025
