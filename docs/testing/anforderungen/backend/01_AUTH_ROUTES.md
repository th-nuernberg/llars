# Backend Testanforderungen: Authentifizierung

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Übersicht

Dieses Dokument beschreibt alle Tests für das LLARS Authentifizierungs-System.

**Architektur:** OIDC/Authentik JWT | System Admin API Key | Legacy API Keys

---

## 1. Decorators

### @authentik_required

**Datei:** `app/auth/decorators.py:148-193`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| AUTH-D01 | Kein Authorization Header | 401 Unauthorized | Unit |
| AUTH-D02 | Invalid Bearer Token | 401 Unauthorized | Unit |
| AUTH-D03 | Expired Token | 401 Unauthorized | Unit |
| AUTH-D04 | Falsches Token-Format | 401 Unauthorized | Unit |
| AUTH-D05 | Valid Token | g.authentik_user gesetzt, 200 | Unit |
| AUTH-D06 | Gelöschter User | 403 ACCOUNT_DELETED | Unit |
| AUTH-D07 | Gesperrter User | 403 ACCOUNT_LOCKED | Unit |
| AUTH-D08 | User wird auto-erstellt | User in DB nach Login | Integration |

### @admin_required

**Datei:** `app/auth/decorators.py:196-220`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| AUTH-A01 | Admin-Token | 200 OK | Unit |
| AUTH-A02 | Nicht-Admin Token | 403 Forbidden | Unit |
| AUTH-A03 | Ohne Token | 401 Unauthorized | Unit |

### @roles_required

**Datei:** `app/auth/decorators.py:223-252`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| AUTH-R01 | Eine von Rollen vorhanden | 200 OK | Unit |
| AUTH-R02 | Keine Rolle vorhanden | 403 Forbidden | Unit |
| AUTH-R03 | Mehrere Rollen, eine passt | 200 OK | Unit |

### @optional_auth

**Datei:** `app/auth/decorators.py:255-287`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| AUTH-O01 | Ohne Token | Route funktioniert, kein User | Unit |
| AUTH-O02 | Mit gültigem Token | g.authentik_user gesetzt | Unit |
| AUTH-O03 | Mit ungültigem Token | Route funktioniert trotzdem | Unit |

### @system_api_key_required

**Datei:** `app/auth/decorators.py:290-346`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| AUTH-K01 | Korrekter API Key (Header) | 200 OK | Unit |
| AUTH-K02 | Korrekter API Key (Query) | 200 OK | Unit |
| AUTH-K03 | Falscher API Key | 401 Unauthorized | Unit |
| AUTH-K04 | Kein API Key | 401 Unauthorized | Unit |
| AUTH-K05 | API Key nicht konfiguriert | 500 Server Error | Unit |

### @debug_route_protected

**Datei:** `app/auth/decorators.py:349-375`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| AUTH-B01 | Development Mode | API Key Check | Unit |
| AUTH-B02 | Production Mode | 403 Forbidden | Unit |

---

## 2. Auth Routes

### POST /auth/authentik/login

**Datei:** `app/routes/authentik_routes.py:121-403`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LOGIN-001 | Valide Credentials | access_token, llars_roles | Integration |
| LOGIN-002 | Falsches Passwort | 401 Invalid credentials | Integration |
| LOGIN-003 | Unbekannter User | 401 Invalid credentials | Integration |
| LOGIN-004 | Fehlende Felder | 400 Bad Request | Integration |
| LOGIN-005 | Rate Limit (11+ pro Minute) | 429 Too Many Requests | Integration |
| LOGIN-006 | Authentik nicht erreichbar | 503 Service Unavailable | Integration |
| LOGIN-007 | Authentik Timeout | 504 Gateway Timeout | Integration |
| LOGIN-008 | Cookie gesetzt | authentik_session Cookie | Integration |

**Request:**
```json
{
  "username": "string (required)",
  "password": "string (required)"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "optional",
  "llars_roles": ["admin", "researcher"]
}
```

### GET /auth/authentik/me

**Datei:** `app/routes/authentik_routes.py:49-80`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ME-001 | Valid Token | User-Info zurück | Integration |
| ME-002 | Invalid Token | 401 Unauthorized | Integration |
| ME-003 | Rate Limit (101+ pro Stunde) | 429 Too Many Requests | Integration |

**Response:**
```json
{
  "username": "string",
  "user_id": "string",
  "avatar_seed": "string",
  "avatar_url": "string",
  "roles": ["string"],
  "email": "string",
  "name": "string"
}
```

### GET /auth/authentik/validate

**Datei:** `app/routes/authentik_routes.py:83-106`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| VAL-001 | Valid Token | valid: true | Integration |
| VAL-002 | Invalid Token | 401 Unauthorized | Integration |
| VAL-003 | Expired Token | 401 Unauthorized | Integration |

### GET /auth/authentik/admin/check

**Datei:** `app/routes/authentik_routes.py:109-118`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ADM-CHK-001 | Admin User | 200 OK | Integration |
| ADM-CHK-002 | Nicht-Admin User | 403 Forbidden | Integration |

### GET /auth/authentik/health_check

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| HEALTH-001 | Ohne Auth | 200 OK, Server running | Integration |

---

## 3. Legacy Auth Routes

### POST /auth/register

**Datei:** `app/routes/auth/auth_routes.py:21-61`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| REG-001 | Neue Registration | 201, api_key zurück | Integration |
| REG-002 | Duplicate Username | 409 Conflict | Integration |
| REG-003 | Fehlende Felder | 400 Bad Request | Integration |
| REG-004 | Ungültiger API Key | 400 Bad Request | Integration |
| REG-005 | Nicht existierende Gruppe | 400 Bad Request | Integration |

### POST /auth/register_admin

**Datei:** `app/routes/auth/auth_routes.py:91-131`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| REGADM-001 | Korrekter Admin Key | 201, Admin erstellt | Integration |
| REGADM-002 | Falscher Admin Key | 401 Unauthorized | Integration |
| REGADM-003 | Fehlender Admin Key | 401 Unauthorized | Integration |

---

## 4. Token Validation

### OIDC Validator

**Datei:** `app/auth/oidc_validator.py`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| OIDC-001 | RS256 Signatur valid | Payload zurück | Unit |
| OIDC-002 | Signatur manipuliert | None zurück | Unit |
| OIDC-003 | Falsche Audience | None zurück | Unit |
| OIDC-004 | Falscher Issuer | None zurück | Unit |
| OIDC-005 | Token expired | None zurück | Unit |
| OIDC-006 | JWKS Cache (1h) | Keine neuen Requests | Unit |

### Role & Permission Checks

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ROLE-001 | has_role mit gültiger Rolle | True | Unit |
| ROLE-002 | has_role ohne Rolle | False | Unit |
| ROLE-003 | get_username Fallbacks | Username oder Fallback | Unit |
| ROLE-004 | Introspect Token (Netzwerk) | Introspection Result | Integration |

---

## 5. User Management

### get_or_create_user

**Datei:** `app/auth/decorators.py`

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| USER-001 | Neuer User | User erstellt mit Defaults | Unit |
| USER-002 | Existierender User | User geladen | Unit |
| USER-003 | Auto collab_color | Farbe generiert | Unit |
| USER-004 | Auto api_key | UUID generiert | Unit |
| USER-005 | Auto avatar_seed | Seed generiert | Unit |
| USER-006 | Default viewer Rolle | Viewer zugewiesen | Unit |
| USER-007 | Event geloggt | user.created Event | Unit |

---

## 6. Unit Test-Code

```python
# tests/unit/auth/test_decorators.py
import pytest
from unittest.mock import MagicMock, patch
from flask import g
from app.auth.decorators import authentik_required, admin_required


class TestAuthentikRequired:
    """@authentik_required Decorator Tests"""

    def test_AUTH_D01_no_auth_header(self, client):
        """Kein Authorization Header gibt 401"""
        response = client.get('/api/users/me')
        assert response.status_code == 401
        assert response.json['error'] == 'No authorization token provided'

    def test_AUTH_D02_invalid_token(self, client):
        """Ungültiger Token gibt 401"""
        response = client.get(
            '/api/users/me',
            headers={'Authorization': 'Bearer invalid.token.here'}
        )
        assert response.status_code == 401

    def test_AUTH_D05_valid_token(self, app, client, valid_token):
        """Gültiger Token setzt g.authentik_user"""
        with app.test_request_context():
            response = client.get(
                '/api/users/me',
                headers={'Authorization': f'Bearer {valid_token}'}
            )
            assert response.status_code == 200
            assert 'username' in response.json

    def test_AUTH_D06_deleted_user(self, client, deleted_user_token):
        """Gelöschter User gibt 403 ACCOUNT_DELETED"""
        response = client.get(
            '/api/users/me',
            headers={'Authorization': f'Bearer {deleted_user_token}'}
        )
        assert response.status_code == 403
        assert 'ACCOUNT_DELETED' in response.json.get('error_type', '')

    def test_AUTH_D07_locked_user(self, client, locked_user_token):
        """Gesperrter User gibt 403 ACCOUNT_LOCKED"""
        response = client.get(
            '/api/users/me',
            headers={'Authorization': f'Bearer {locked_user_token}'}
        )
        assert response.status_code == 403
        assert 'ACCOUNT_LOCKED' in response.json.get('error_type', '')


class TestAdminRequired:
    """@admin_required Decorator Tests"""

    def test_AUTH_A01_admin_token(self, client, admin_token):
        """Admin-Token erlaubt Zugriff"""
        response = client.get(
            '/api/admin/users',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200

    def test_AUTH_A02_non_admin_token(self, client, researcher_token):
        """Nicht-Admin Token gibt 403"""
        response = client.get(
            '/api/admin/users',
            headers={'Authorization': f'Bearer {researcher_token}'}
        )
        assert response.status_code == 403


class TestSystemApiKey:
    """@system_api_key_required Decorator Tests"""

    def test_AUTH_K01_valid_header(self, client, system_api_key):
        """API Key im Header funktioniert"""
        response = client.get(
            '/debug/info',
            headers={'X-API-Key': system_api_key}
        )
        assert response.status_code == 200

    def test_AUTH_K02_valid_query(self, client, system_api_key):
        """API Key als Query Parameter funktioniert"""
        response = client.get(f'/debug/info?api_key={system_api_key}')
        assert response.status_code == 200

    def test_AUTH_K03_invalid_key(self, client):
        """Falscher API Key gibt 401"""
        response = client.get(
            '/debug/info',
            headers={'X-API-Key': 'wrong-key'}
        )
        assert response.status_code == 401
```

---

## 7. Integration Test-Code

```python
# tests/integration/auth/test_login.py
import pytest


class TestLogin:
    """Login Flow Integration Tests"""

    def test_LOGIN_001_valid_credentials(self, client):
        """Valide Credentials geben Token zurück"""
        response = client.post('/auth/authentik/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        assert response.status_code == 200
        assert 'access_token' in response.json
        assert 'llars_roles' in response.json
        assert response.json['token_type'] == 'Bearer'

    def test_LOGIN_002_wrong_password(self, client):
        """Falsches Passwort gibt 401"""
        response = client.post('/auth/authentik/login', json={
            'username': 'admin',
            'password': 'wrongpassword'
        })
        assert response.status_code == 401

    def test_LOGIN_004_missing_fields(self, client):
        """Fehlende Felder geben 400"""
        response = client.post('/auth/authentik/login', json={
            'username': 'admin'
        })
        assert response.status_code == 400

    def test_LOGIN_008_cookie_set(self, client):
        """Login setzt authentik_session Cookie"""
        response = client.post('/auth/authentik/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        assert 'authentik_session' in response.headers.get('Set-Cookie', '')


class TestTokenValidation:
    """Token Validation Tests"""

    def test_VAL_001_valid_token(self, client, valid_token):
        """Gültiger Token wird validiert"""
        response = client.get(
            '/auth/authentik/validate',
            headers={'Authorization': f'Bearer {valid_token}'}
        )
        assert response.status_code == 200
        assert response.json['valid'] is True

    def test_VAL_002_invalid_token(self, client):
        """Ungültiger Token wird abgelehnt"""
        response = client.get(
            '/auth/authentik/validate',
            headers={'Authorization': 'Bearer invalid.token'}
        )
        assert response.status_code == 401
```

---

## 8. Fixtures

```python
# tests/conftest.py
import pytest
import jwt
from datetime import datetime, timedelta


@pytest.fixture
def valid_token(app):
    """Generiert einen gültigen Test-Token"""
    payload = {
        'sub': 'test-user-id',
        'preferred_username': 'testuser',
        'groups': ['viewer'],
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iss': app.config['AUTHENTIK_ISSUER_URL'],
        'aud': 'llars-backend'
    }
    # Signiere mit Test-Key
    return jwt.encode(payload, 'test-secret', algorithm='HS256')


@pytest.fixture
def admin_token(app):
    """Generiert einen Admin-Token"""
    payload = {
        'sub': 'admin-user-id',
        'preferred_username': 'admin',
        'groups': ['admin', 'authentik Admins'],
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iss': app.config['AUTHENTIK_ISSUER_URL'],
        'aud': 'llars-backend'
    }
    return jwt.encode(payload, 'test-secret', algorithm='HS256')


@pytest.fixture
def deleted_user_token(app, db):
    """Token für gelöschten User"""
    from app.db.models import User
    user = User(username='deleted_user', deleted_at=datetime.now())
    db.session.add(user)
    db.session.commit()

    payload = {
        'sub': 'deleted-user-id',
        'preferred_username': 'deleted_user',
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, 'test-secret', algorithm='HS256')


@pytest.fixture
def system_api_key(app):
    """System Admin API Key"""
    return app.config.get('SYSTEM_ADMIN_API_KEY', 'test-api-key')
```

---

## 9. Checkliste für manuelle Tests

### Login Flow
- [ ] Login mit admin/admin123 funktioniert
- [ ] Token im Response enthalten
- [ ] Token im localStorage speicherbar
- [ ] Refresh Token vorhanden (wenn konfiguriert)
- [ ] Cookie gesetzt

### Token Handling
- [ ] Token wird bei jedem Request mitgesendet
- [ ] Expired Token führt zu Logout
- [ ] Invalid Token führt zu Logout
- [ ] Token Refresh funktioniert

### Account States
- [ ] Gesperrter User kann nicht einloggen
- [ ] Gelöschter User kann nicht einloggen
- [ ] Aktiver User kann einloggen

### Admin Access
- [ ] Admin sieht Admin-Bereich
- [ ] Nicht-Admin sieht keinen Admin-Bereich
- [ ] Admin-Routes nur für Admins zugänglich

---

## 10. Umgebungsvariablen

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `AUTHENTIK_ISSUER_URL` | `http://authentik-server:9000/...` | OIDC Issuer |
| `AUTHENTIK_INTERNAL_URL` | `http://authentik-server:9000` | Interne URL |
| `AUTHENTIK_BACKEND_CLIENT_ID` | `llars-backend` | OAuth Client ID |
| `AUTHENTIK_BACKEND_CLIENT_SECRET` | (leer) | OAuth Secret |
| `SYSTEM_ADMIN_API_KEY` | (leer) | Debug API Key |
| `ADMIN_REGISTRATION_KEY` | (leer) | Admin Registration |
| `FLASK_ENV` | `production` | Umgebung |

---

**Letzte Aktualisierung:** 30. Dezember 2025
