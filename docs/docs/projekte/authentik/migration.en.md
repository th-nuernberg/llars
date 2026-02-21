# Authentik Migration - LLARS Authentication

**Status:** COMPLETED
**Date:** November 25, 2025
**Author:** Claude Code

---

## Summary

The Authentik integration has been successfully implemented:
- **Login:** Works via the Flow Executor API
- **Token:** RS256-signed, verifiable via JWKS
- **Validation:** Correct token validation in the backend
- **Dev/Prod Parity:** Same authentication logic in both modes
- **SSO Session:** Authentik session cookie is optionally forwarded to the browser (e.g., for Matomo)

---

## Problem Summary

### Original State (Critical Security Issues)

LLARS authentication had several critical problems:

1. **Direct database access**: The login endpoint accessed Authentik's PostgreSQL database directly instead of using OAuth2/OIDC APIs
2. **HS256 JWT tokens**: Custom tokens were signed with HS256 instead of using Authentik's RS256-signed tokens
3. **Hardcoded development password**: `admin123` was accepted as a universal password in development mode
4. **Dev/Prod parity violated**: Different authentication logic for development and production

### Target State

- Full OIDC integration with Authentik
- RS256-signed JWT tokens (verifiable via JWKS endpoint)
- Same authentication logic for development and production
- No direct database access to Authentik

---

## Solution: Authentik Flow Executor API

### Architecture

```
Frontend (Vue.js)
      │
      │ POST /auth/login {username, password}
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

### Why the Flow Executor API?

Authentik does **not** support the classic Resource Owner Password Credentials (ROPC) grant. Instead:

- The `client_credentials` grant works only with service accounts, not user passwords
- The `password` grant is treated like `client_credentials` by Authentik

The solution is the **Flow Executor API**:
1. Programmatically run the same flow a user would go through in the browser
2. After successful flow authentication: obtain an OAuth2 authorization code
3. Exchange the code for tokens

---

## Implemented Changes

### 1. Authentik Provider RS256 Configuration

Both providers were switched to RS256:

```python
# In Authentik shell
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.crypto.models import CertificateKeyPair

cert = CertificateKeyPair.objects.filter(name__contains="Self-signed").first()
for provider in OAuth2Provider.objects.all():
    provider.signing_key = cert
    provider.save()
```

### 2. Custom Authentication Flow Created

Flow: `llars-api-authentication`

Stages:
1. `IdentificationStage` - User identification (no MFA)
2. `PasswordStage` - Password validation
3. `UserLoginStage` - Create session

### 3. Backend Login Endpoint

**File:** `app/routes/authentik_routes.py`

```python
@authentik_auth_blueprint.route('/login', methods=['POST'])
def login():
    # 1. Start flow
    session.get(f"{authentik_url}/api/v3/flows/executor/{flow_slug}/")

    # 2. Submit username
    session.post(flow_url, json={'uid_field': username})

    # 3. Submit password
    session.post(flow_url, json={'password': password})

    # 4. Request OAuth2 authorization code
    session.get(auth_url, params={
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'openid profile email'
    })

    # 5. Exchange code for token
    requests.post(token_url, data={
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret
    })
```

### 4. SSO Session Cookie Forwarding (optional)

If an Authentik session is created during the flow, the
`authentik_session` cookie is forwarded server-side to the browser.
This lets other OIDC-protected apps (e.g., Matomo) reuse the session
without prompting for login again.

### 5. Token Validation (RS256 only)

**File:** `app/auth/oidc_validator.py`

```python
def validate_token(token: str) -> Optional[Dict]:
    # Accept RS256 only
    if alg != 'RS256':
        print(f"Unsupported token algorithm: {alg}. Only RS256 is accepted.")
        return None

    # Get key from JWKS endpoint
    public_key = get_public_key(kid)

    # Validate token
    decoded = jwt.decode(token, public_key, algorithms=['RS256'], ...)
```

---

## Configuration

### Environment variables (.env)

```bash
# Authentik base URL (reachable internally by the backend)
AUTHENTIK_INTERNAL_URL=http://authentik-server:9000

# OAuth2 client configuration
AUTHENTIK_BACKEND_CLIENT_ID=llars-backend
AUTHENTIK_BACKEND_CLIENT_SECRET=llars-backend-secret-change-in-production

# OIDC issuer URL (for token validation)
AUTHENTIK_ISSUER_URL=http://authentik-server:9000/application/o/llars-backend/
```

### Authentik provider settings

| Setting | Value |
|------------|------|
| Client ID | `llars-backend` |
| Client Type | Confidential |
| Signing Algorithm | RS256 |
| Signing Key | Self-signed Certificate |
| Redirect URIs | `http://authentik-server:9000/` (for code exchange) |
| Authorization Flow | `default-provider-authorization-implicit-consent` |

---

## Implementation Status

### Successfully implemented

- [x] RS256 configuration in Authentik
- [x] JWKS endpoint reachable from backend (`/application/o/llars-backend/jwks/`)
- [x] Custom authentication flow without MFA (`llars-api-authentication`)
- [x] Flow Executor API - username authentication
- [x] Flow Executor API - password authentication
- [x] OAuth2 authorization code flow
- [x] Token exchange
- [x] Backend login endpoint delegation
- [x] Token validation via JWKS
- [x] Client secret synchronization

### Fixed issues

1. **JWKS URL incorrect**: Code used `/.well-known/jwks.json`, Authentik uses `/jwks/`
2. **Client secret mismatch**: Secret in .env did not match Authentik
3. **Duplicate login endpoint**: Old login code in `routes.py` overrode new code

---

## Troubleshooting

### Password invalid although correct

```bash
# Set password in Authentik
docker compose exec -T authentik-server ak shell -c "
from authentik.core.models import User
user = User.objects.get(username='akadmin')
user.set_password('admin123')
user.save()
"
```

### Verify RS256 providers

```bash
docker compose exec -T authentik-server ak shell -c "
from authentik.providers.oauth2.models import OAuth2Provider
for p in OAuth2Provider.objects.all():
    print(f'{p.name}: signing_key={p.signing_key}')
"
```

### Test JWKS endpoint

```bash
docker compose exec -T backend-flask-service curl -s \
  http://authentik-server:9000/application/o/llars-backend/jwks/ | jq .
```

---

## References

- [Authentik OIDC Provider Docs](https://goauthentik.io/docs/providers/oauth2/)
- [Authentik Flow Executor API](https://goauthentik.io/docs/flows/)
- [RFC 6749 - OAuth 2.0](https://tools.ietf.org/html/rfc6749)
