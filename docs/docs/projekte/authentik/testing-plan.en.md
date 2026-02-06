# LLARS Authentik Testing & Setup Plan

**Date:** November 25, 2025
**Status:** COMPLETED

---

## 1. Analysis: Why were changes necessary?

### Original issues (security-critical)

The original authentication code had several **critical security problems**:

| Problem | Description | Risk |
|---------|--------------|--------|
| **Direct DB access** | Login endpoint accessed Authentik's PostgreSQL directly | Bypassing OIDC, no token validation |
| **HS256 tokens** | Custom JWT tokens signed with HS256 | Shared secret instead of asymmetric crypto |
| **Hardcoded password** | `admin123` always accepted in dev mode | Massive security gap |
| **Dev/Prod gap** | Different auth logic in development vs production | Inconsistent behavior |

### Implemented solution

```
Frontend (Vue.js)
      │
      │ POST /auth/authentik/login {username, password}
      ▼
Backend (Flask)
      │
      │ 1. Start Flow (GET /api/v3/flows/executor/llars-api-authentication/)
      │ 2. Submit Username (POST with uid_field)
      │ 3. Submit Password (POST with password)
      │ 4. OAuth2 Authorization Request
      │ 5. Exchange Code for Token
      ▼
Authentik (OIDC Provider)
      │
      │ RS256-signed JWT Token
      ▼
Backend → Frontend
```

### Are these changes valid?

**YES** - The changes are necessary and correct from a security standpoint:

1. **RS256 instead of HS256**: Asymmetric cryptography is best practice for OIDC
2. **Flow Executor API**: Official Authentik method for headless/API authentication
3. **JWKS validation**: Standards-compliant token validation via public key
4. **Dev/Prod parity**: Same logic in both environments

---

## 2. Historical issues after restart (resolved)

These issues occurred in early iterations and are now resolved by the
`authentik-init` container (`docker/authentik/init-authentik.sh`):

- Missing providers/flows after restart
- Incorrect provider names in legacy scripts
- Frontend login errors when Authentik configuration was missing

---

## 3. Test Plan

### 3.1 Backend API Tests

| Test | Endpoint | Expected result |
|------|----------|-----------------|
| Health Check | `GET /auth/authentik/health_check` | `{"message": "Server is running with Authentik authentication"}` |
| Login Valid | `POST /auth/authentik/login` | RS256 token returned |
| Login Invalid | `POST /auth/authentik/login` (wrong pw) | `401` with `{"success": false, "error": "Invalid credentials", "error_type": "unauthorized"}` |
| Login Missing | `POST /auth/authentik/login` (no data) | `400` with `{"success": false, "error": "Username and password required", "error_type": "validation_error"}` |
| Token Validate | `GET /auth/authentik/validate` | `{"valid": true, ...}` |
| User Info | `GET /auth/authentik/me` | User data |

### 3.2 Frontend Tests

| Test | URL | Expected result |
|------|-----|-----------------|
| Login Page | `http://localhost:55080/login` | Login form is displayed |
| Login Submit | Form submit | Redirect to `/Home` or `redirect` query |
| Protected Route | `http://localhost:55080/Home` | Shows Home when logged in |
| Token Persistence | Refresh page | Stays logged in |

### 3.3 LLM Evaluators (LLM-as-Judge) Auth Tests

| Test | Endpoint | Expected result |
|------|----------|-----------------|
| Sessions List | `GET /api/judge/sessions` | 200 with auth, 401 without |
| Create Session | `POST /api/judge/sessions` | Requires `feature:comparison:edit` |
| Start Session | `POST /api/judge/sessions/{id}/start` | Requires auth |

### 3.4 OnCoCo Auth Tests

| Test | Endpoint | Expected result |
|------|----------|-----------------|
| Analyses List | `GET /api/oncoco/analyses` | 200 with auth, 401 without |
| Create Analysis | `POST /api/oncoco/analyses` | Requires auth |
| Analysis Results | `GET /api/oncoco/analyses/{id}` | Requires auth |

---

## 4. Authentik Setup Guide

### 4.1 Required components

After a fresh start, the following components must exist:

1. **OAuth2 Provider** (`llars-backend`)
   - Client ID: `llars-backend`
   - Client Type: `confidential`
   - Client Secret: `llars-backend-secret-change-in-production`
   - Signing Key: Self-signed Certificate (RS256)
   - Redirect URIs: `http://authentik-server:9000/`

2. **Application** (`llars-backend`)
   - Provider: llars-backend
   - Slug: llars-backend

3. **Authentication Flow** (`llars-api-authentication`)
   - Stages: Identification → Password → User Login
   - No MFA for API access

4. **User** (`akadmin`)
   - Password must be set

### 4.2 Manual setup commands

```bash
# 1. Create flow
docker compose exec -T authentik-server ak shell -c "
from authentik.flows.models import Flow, FlowStageBinding, FlowDesignation
from authentik.stages.identification.models import IdentificationStage, UserFields
from authentik.stages.password.models import PasswordStage
from authentik.stages.user_login.models import UserLoginStage

flow, created = Flow.objects.get_or_create(
    slug='llars-api-authentication',
    defaults={
        'name': 'LLARS API Authentication',
        'designation': FlowDesignation.AUTHENTICATION,
        'title': 'LLARS API Login'
    }
)
print(f'Flow: {flow.slug} (created: {created})')

if created:
    id_stage, _ = IdentificationStage.objects.get_or_create(
        name='llars-api-identification',
        defaults={'user_fields': [UserFields.USERNAME, UserFields.E_MAIL]}
    )
    pw_stage, _ = PasswordStage.objects.get_or_create(
        name='llars-api-password',
        defaults={'backends': ['authentik.core.auth.InbuiltBackend']}
    )
    login_stage, _ = UserLoginStage.objects.get_or_create(
        name='llars-api-user-login',
        defaults={'session_duration': 'seconds=0'}
    )
    FlowStageBinding.objects.create(target=flow, stage=id_stage, order=10)
    FlowStageBinding.objects.create(target=flow, stage=pw_stage, order=20)
    FlowStageBinding.objects.create(target=flow, stage=login_stage, order=30)
    print('Stages bound')
"

# 2. Create OAuth2 provider
docker compose exec -T authentik-server ak shell -c "
from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping
from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow
from authentik.core.models import Application

cert = CertificateKeyPair.objects.filter(name__contains='Self-signed').first()
auth_flow = Flow.objects.get(slug='default-provider-authorization-implicit-consent')

provider, created = OAuth2Provider.objects.get_or_create(
    name='llars-backend',
    defaults={
        'client_id': 'llars-backend',
        'client_secret': 'llars-backend-secret-change-in-production',
        'client_type': 'confidential',
        'authorization_flow': auth_flow,
        'signing_key': cert,
    }
)
print(f'Provider: {provider.name} (created: {created})')

# Add scopes
scopes = ScopeMapping.objects.filter(managed__startswith='goauthentik.io/providers/oauth2/scope-')
provider.property_mappings.set(scopes)
provider.save()
print(f'Added {scopes.count()} scopes')

# Create application
app, created = Application.objects.get_or_create(
    slug='llars-backend',
    defaults={'name': 'LLARS Backend', 'provider': provider}
)
print(f'Application: {app.name} (created: {created})')
"

# 3. Set password for akadmin
docker compose exec -T authentik-server ak shell -c "
from authentik.core.models import User
user = User.objects.get(username='akadmin')
user.set_password('admin123')
user.save()
print('Password set for akadmin')
"
```

### 4.3 Automated setup (current)

Auto-setup is implemented in the `authentik-init` container and uses
`docker/authentik/init-authentik.sh` (idempotent). The older
`init-authentik.py` is legacy and no longer used.

---

## 5. Tests Performed (as of 2025-11-25)

### Phase 1: Backend API (Priority: HIGH) - COMPLETED

- [x] Health Check works (`GET /auth/authentik/health_check` -> `{"message": "Server is running with Authentik authentication"}`)
- [x] Login with valid credentials returns RS256 token (token length: 1676 characters)
- [x] Login with invalid credentials is rejected (401)
- [x] Token validation works (`GET /auth/authentik/validate`)
- [x] /me endpoint returns user info (preferred_username, email, groups)

### Phase 2: Frontend (Priority: HIGH) - FIXED

- [x] Login page loads (`http://localhost:55080/login`)
- [x] Login form submits correctly to `/auth/authentik/login`
- [x] Token is stored (sessionStorage: `auth_token`, `auth_llars_roles`)
- [x] Protected routes work (router guard checks `auth_llars_roles`)
- [x] Logout works (clears all auth data)

**Bugfix performed:**
- `useAuth.js`: Now uses `llars_roles` from backend response instead of `realm_access.roles` (Keycloak-specific)
- `router.js`: Router guard now checks `auth_llars_roles` from sessionStorage

### Phase 3: LLM Evaluators (LLM-as-Judge) (Priority: MEDIUM) - COMPLETED

- [x] Sessions list requires auth (without auth: `{"error":"Missing authorization token"}`)
- [x] With auth: 3 sessions found
- [x] Pillars endpoint works with auth (5 pillars available)
- [ ] WebSocket events require auth (not tested)

### Phase 4: OnCoCo (Priority: MEDIUM) - COMPLETED

- [x] Analyses list requires auth (without auth: `{"error":"Missing authorization token"}`)
- [x] With auth: empty list (no analyses created)
- [x] Pillars endpoint works (85 threads in DB)
- [x] Info endpoint works (68 labels, model available)

---

## 6. Known Issues

Currently no known open issues. Auto-setup runs via `authentik-init`,
frontend uses `llars_roles`, configuration is persisted via volumes.

---

## 7. Corrections Made

### 7.1 Frontend auth system adjusted

**Problem:** The frontend looked for `realm_access.roles` in the token (Keycloak format), but Authentik uses `groups`.

**Solution:**
1. Backend returns `llars_roles` in the login response (based on Authentik groups)
2. Frontend stores `llars_roles` in sessionStorage
3. Router guard and useAuth composable use `llars_roles` for admin checks

**Files changed:**
- `llars-frontend/src/composables/useAuth.js`
- `llars-frontend/src/router.js`

### 7.2 Authentik components created manually

After a container restart, the following components were created via `ak shell`:
1. Flow: `llars-api-authentication` with 3 stages
2. OAuth2 Provider: `llars-backend` with RS256 signing key
3. Application: `llars-backend`
4. Scope mappings for user info (openid, profile, email)
5. Password for `akadmin` set

---

## 8. Next Steps

1. Test WebSocket authentication (optional)
