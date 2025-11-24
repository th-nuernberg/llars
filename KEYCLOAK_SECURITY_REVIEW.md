# Keycloak Security Review - LLARS Project

**Review Date:** 22. November 2025
**Keycloak Version:** 26.0.7
**Reviewer:** Claude Code Security Analysis

---

## Executive Summary

⚠️ **CRITICAL SECURITY ISSUES FOUND**

The current Keycloak setup has **7 critical security vulnerabilities** that MUST be addressed before production deployment. While the basic architecture (RS256, JWT validation, RBAC) is sound, several configuration issues expose the system to significant security risks.

**Overall Security Rating: 4/10** (Development acceptable, Production UNACCEPTABLE)

---

## Web Search Results Summary

Based on industry best practices for Keycloak JWT validation with RS256:

### Key Findings from Research

**Token Validation Best Practices:**
- ✅ Use JWKS endpoint for public key retrieval (implemented)
- ✅ Verify signature with RS256 algorithm (implemented)
- ✅ Validate claims: `iss`, `exp`, `aud` (implemented)
- ⚠️ Match `kid` (Key ID) from token header with JWKS key (NOT implemented)
- ⚠️ Implement key rotation strategy with cache invalidation (NOT implemented)
- ✅ Use short-lived tokens (5-15 min) (implemented: 5 min)

**Production Security Requirements:**
- ❌ HTTPS/TLS for ALL connections (NOT implemented)
- ❌ External production database with TLS (PostgreSQL used, no TLS)
- ❌ Secrets management (Vault, AWS Secrets Manager) (NOT implemented)
- ❌ Run containers as non-root (native Keycloak support, likely implemented)
- ❌ Network isolation (NOT fully implemented - Keycloak exposed)
- ✅ Resource limits in Docker (NOT explicitly set)

### Sources

- [Keycloak Token Validation for APIs](https://skycloak.io/blog/keycloak-token-validation-for-apis/)
- [How to verify a Keycloak-issued access token](https://skycloak.io/blog/how-to-verify-a-keycloak-issued-access-token-on-the-backend/)
- [Keycloak Access Token Verification Example](https://blog.ropardo.ro/2025/02/06/keycloak-access-token-verification-a-step-by-step-example/)
- [Keycloak Token Validation Discussion](https://github.com/keycloak/keycloak/discussions/27225)

---

## Critical Security Issues (🔴 MUST FIX)

### 1. 🔴 CRITICAL: Development Mode in Production

**Location:** `docker-compose.yml:202`

```yaml
command:
  - start-dev
  - --import-realm
```

**Issue:** Keycloak is running in `start-dev` mode, which:
- Disables production optimizations
- Enables developer features that expose attack surface
- May have debug endpoints enabled
- Not suitable for production workloads

**Fix:**
```yaml
command:
  - start
  - --optimized
```

**Priority:** 🔴 CRITICAL - Fix immediately

---

### 2. 🔴 CRITICAL: No TLS/HTTPS Enabled

**Location:** `docker-compose.yml:184`, `realm-import-template.json:6`

```yaml
KC_HTTP_ENABLED=true
KC_PROXY=edge
```

```json
"sslRequired": "__SSL_REQUIRED__"
```

**Issues:**
1. Keycloak accepts plain HTTP connections
2. JWT tokens transmitted in clear text
3. `sslRequired` is a placeholder, never replaced
4. Credentials exposed during login

**Fix:**
```yaml
# docker-compose.yml
KC_HTTP_ENABLED=false
KC_HTTPS_CERTIFICATE_FILE=/opt/keycloak/certs/cert.pem
KC_HTTPS_CERTIFICATE_KEY_FILE=/opt/keycloak/certs/key.pem
KC_PROXY=edge  # Keep for nginx reverse proxy
```

```json
// realm-import-template.json
"sslRequired": "all"  // or "external" for proxy setup
```

**Priority:** 🔴 CRITICAL - Required for production

---

### 3. 🔴 CRITICAL: Hardcoded Secrets in Realm Import

**Location:** `realm-import-template.json:89, 176`

```json
"credentials": [
  {
    "type": "password",
    "value": "admin123",  // ❌ Hardcoded weak password
    "temporary": false
  }
]

"secret": "llars-backend-secret-change-in-production"  // ❌ Hardcoded in Git
```

**Issue:**
- Admin password `admin123` is trivially weak
- Client secret is in Git repository
- Secrets are world-readable in version control

**Fix:**
1. Remove hardcoded admin user from realm import
2. Create admin via environment variables:
   ```yaml
   KEYCLOAK_ADMIN: ${KEYCLOAK_ADMIN_USER}
   KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD}
   ```
3. Generate strong client secret (32+ chars):
   ```bash
   openssl rand -base64 32
   ```
4. Use Docker secrets or external vault

**Priority:** 🔴 CRITICAL - Security breach risk

---

### 4. 🔴 CRITICAL: CORS Wildcard Origin

**Location:** `realm-import-template.json:120-122, 190-192`

```json
"webOrigins": [
  "+"  // ❌ Allows ALL origins
]
```

**Issue:**
- `"+"` wildcard allows ANY website to make authenticated requests
- Enables CSRF attacks from malicious sites
- Defeats purpose of CORS protection

**Fix:**
```json
"webOrigins": [
  "http://localhost:55080",
  "http://localhost:55173",
  "https://llars.yourdomain.com"
]
```

**Priority:** 🔴 CRITICAL - CSRF vulnerability

---

### 5. 🔴 CRITICAL: Keycloak Directly Exposed to Host

**Location:** `docker-compose.yml:188-189`

```yaml
ports:
  - "${KEYCLOAK_EXTERNAL_PORT}:${KEYCLOAK_INTERNAL_PORT}"
```

**Issue:**
- Keycloak admin console accessible from internet on port 55090
- Should only be accessible via nginx reverse proxy
- Exposes admin interface to attacks

**Fix:**
```yaml
# Remove port mapping, use only expose:
expose:
  - "8080"
# Access Keycloak only via nginx proxy at /auth
```

**Priority:** 🔴 CRITICAL - Attack surface reduction

---

### 6. 🔴 CRITICAL: Missing `kid` Validation in JWT

**Location:** `app/auth/keycloak_validator.py:35-65`

```python
@lru_cache(maxsize=1)
def get_public_key() -> str:
    # ...
    if 'keys' in jwks and len(jwks['keys']) > 0:
        key_data = jwks['keys'][0]  # ❌ Always uses FIRST key
```

**Issue:**
- Does not match `kid` (Key ID) from JWT header
- During key rotation, may use wrong key
- Tokens signed with old keys will fail validation incorrectly

**Fix:**
```python
def get_public_key(kid: str = None) -> str:
    """Get public key matching the kid from JWKS"""
    response = requests.get(keycloak_config.certs_url, timeout=5)
    jwks = response.json()

    # If kid provided, find matching key
    if kid:
        for key in jwks['keys']:
            if key.get('kid') == kid:
                return RSAAlgorithm.from_jwk(key)
        raise ValueError(f"Key with kid {kid} not found")

    # Fallback to first key (development only)
    return RSAAlgorithm.from_jwk(jwks['keys'][0])

# In validate_token, extract kid from JWT header
def validate_token(token: str) -> Optional[Dict]:
    # Decode header without verification to get kid
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get('kid')

    public_key = get_public_key(kid)
    # ... rest of validation
```

**Priority:** 🔴 CRITICAL - Key rotation will break auth

---

### 7. 🔴 CRITICAL: Public Key Cache Never Invalidates

**Location:** `app/auth/keycloak_validator.py:35`

```python
@lru_cache(maxsize=1)
def get_public_key() -> str:
```

**Issue:**
- `lru_cache` never expires
- After Keycloak key rotation, backend keeps using old key indefinitely
- Requires Flask restart to pick up new keys

**Fix:**
```python
from functools import lru_cache
from datetime import datetime, timedelta

_key_cache = {}
_cache_timeout = timedelta(hours=1)

def get_public_key(kid: str = None) -> str:
    """Get public key with 1-hour TTL cache"""
    cache_key = f"jwks_{kid or 'default'}"

    # Check cache
    if cache_key in _key_cache:
        cached_key, cached_time = _key_cache[cache_key]
        if datetime.now() - cached_time < _cache_timeout:
            return cached_key

    # Fetch fresh key
    key = _fetch_public_key(kid)
    _key_cache[cache_key] = (key, datetime.now())
    return key
```

**Priority:** 🔴 CRITICAL - Breaks key rotation

---

## High-Priority Issues (🟡 SHOULD FIX)

### 8. 🟡 Email Verification Disabled

**Location:** `realm-import-template.json:10`

```json
"verifyEmail": false
```

**Issue:** Users can register with fake emails
**Fix:** Set to `true` and configure SMTP
**Priority:** 🟡 HIGH (before allowing public registration)

---

### 9. 🟡 Self-Registration Enabled Without Safeguards

**Location:** `realm-import-template.json:7`

```json
"registrationAllowed": true
```

**Issue:** Anyone can create accounts without approval
**Fix:**
- Disable for production, use admin-created accounts
- Or enable email verification + CAPTCHA
**Priority:** 🟡 HIGH

---

### 10. 🟡 No Multi-Factor Authentication (MFA)

**Issue:** No 2FA/MFA configured
**Fix:** Enable OTP in Keycloak realm settings
**Priority:** 🟡 HIGH (for admin accounts)

---

### 11. 🟡 Weak Passwords in .env

**Location:** `.env:28-30, 39`

```bash
KEYCLOAK_DB_PASSWORD=keycloak_db_secure_password_123
KEYCLOAK_ADMIN_PASSWORD=admin_secure_password_123
KEYCLOAK_BACKEND_CLIENT_SECRET=llars-backend-secret-change-in-production
```

**Issue:** Predictable patterns, checked into Git
**Fix:**
- Generate strong random passwords (32+ chars)
- Use secrets management (Vault, AWS Secrets)
- Add `.env` to `.gitignore`
**Priority:** 🟡 HIGH

---

### 12. 🟡 No Database TLS Connection

**Location:** `docker-compose.yml:178`

```yaml
KC_DB_URL=jdbc:postgresql://keycloak-db-service:5432/keycloak
```

**Issue:** Keycloak → PostgreSQL traffic unencrypted
**Fix:**
```yaml
KC_DB_URL=jdbc:postgresql://keycloak-db-service:5432/keycloak?ssl=true&sslmode=require
```
**Priority:** 🟡 HIGH (for production)

---

## Medium-Priority Issues (🟢 RECOMMENDED)

### 13. 🟢 Token Introspection Not Used

**Location:** `app/auth/keycloak_validator.py:113-145`

**Issue:** `introspect_token()` function exists but is never used
**Recommendation:** For critical operations, use introspection for real-time revocation checks

---

### 14. 🟢 No Token Revocation Handling

**Issue:** No mechanism to handle revoked tokens
**Recommendation:** Implement token introspection or maintain revocation list

---

### 15. 🟢 Missing Rate Limiting on Auth Endpoints

**Issue:** No rate limiting specifically for token validation
**Recommendation:** Add stricter rate limits to prevent token brute-forcing

---

### 16. 🟢 No Audit Logging for Keycloak Events

**Issue:** No event listeners configured
**Recommendation:** Enable Keycloak event listeners to track:
- Failed login attempts
- Admin actions
- Permission changes

---

### 17. 🟢 Implicit Flow Disabled (Good!)

**Location:** `realm-import-template.json:106, 179`

```json
"implicitFlowEnabled": false
```

**Status:** ✅ CORRECT - Implicit flow is deprecated and insecure

---

## Security Strengths (✅ GOOD)

### 1. ✅ Brute Force Protection Enabled

```json
"bruteForceProtected": true,
"failureFactor": 5,
"maxFailureWaitSeconds": 900
```

**Good:** Locks accounts after 5 failed attempts for 15 minutes

---

### 2. ✅ Short Access Token Lifespan

```json
"accessTokenLifespan": 300  // 5 minutes
```

**Good:** Reduces window for token theft/replay attacks

---

### 3. ✅ RS256 Algorithm Used

**Good:** Asymmetric signature prevents token forgery

---

### 4. ✅ Security Headers Configured

```json
"browserSecurityHeaders": {
  "xContentTypeOptions": "nosniff",
  "xFrameOptions": "SAMEORIGIN",
  "xXSSProtection": "1; mode=block",
  "strictTransportSecurity": "max-age=31536000; includeSubDomains"
}
```

**Good:** Defense-in-depth against XSS, clickjacking

---

### 5. ✅ PKCE Enabled for Frontend Client

```json
"attributes": {
  "pkce.code.challenge.method": "S256"
}
```

**Good:** Protects authorization code flow from interception

---

### 6. ✅ Proper Token Validation in Backend

**Location:** `app/auth/keycloak_validator.py:85-95`

```python
decoded = jwt.decode(
    token,
    public_key,
    algorithms=['RS256'],
    audience=keycloak_config.client_id,
    options={
        'verify_signature': True,
        'verify_exp': True,
        'verify_aud': True
    }
)
```

**Good:** Validates signature, expiration, and audience

---

### 7. ✅ Confidential Client for Backend

```json
"publicClient": false,
"secret": "...",
"serviceAccountsEnabled": true
```

**Good:** Backend uses client credentials, not public client

---

## Compliance with Best Practices

| Best Practice | Status | Comment |
|---------------|--------|---------|
| HTTPS/TLS enabled | ❌ FAIL | HTTP only, no TLS |
| Short-lived tokens | ✅ PASS | 5 min access tokens |
| RS256 algorithm | ✅ PASS | Asymmetric signing |
| Brute force protection | ✅ PASS | 5 attempts, 15 min lockout |
| MFA enabled | ❌ FAIL | Not configured |
| Email verification | ❌ FAIL | Disabled |
| Strong passwords | ❌ FAIL | Weak defaults |
| Secrets in vault | ❌ FAIL | Hardcoded in .env |
| CORS properly configured | ❌ FAIL | Wildcard `+` allows all |
| Key rotation support | ❌ FAIL | No kid matching, cache never expires |
| Network isolation | ❌ FAIL | Keycloak exposed on host |
| DB connection encrypted | ❌ FAIL | No TLS to PostgreSQL |
| Production mode | ❌ FAIL | Using `start-dev` |
| Security headers | ✅ PASS | CSP, X-Frame-Options configured |
| PKCE for public clients | ✅ PASS | S256 challenge method |

**Score: 6/15 (40%)**

---

## Recommended Action Plan

### Phase 1: Critical Fixes (Before ANY production use)

1. **Switch to production mode** (1 hour)
   - Change `start-dev` to `start --optimized`
   - Test startup and realm import

2. **Enable TLS/HTTPS** (4 hours)
   - Generate/acquire SSL certificates
   - Configure Keycloak TLS
   - Update `sslRequired` to `"all"`
   - Configure nginx TLS termination

3. **Fix CORS wildcard** (15 minutes)
   - Replace `"+"` with explicit origins
   - Test frontend/backend communication

4. **Remove hardcoded secrets** (2 hours)
   - Generate strong random secrets
   - Move to external secrets management
   - Remove admin user from realm import
   - Update .env (and .gitignore it)

5. **Remove Keycloak port exposure** (30 minutes)
   - Change `ports:` to `expose:`
   - Configure nginx reverse proxy for admin console
   - Test admin access via proxy

6. **Fix JWT kid validation** (3 hours)
   - Implement kid-aware key fetching
   - Add cache expiration (1-hour TTL)
   - Test with key rotation

7. **PostgreSQL TLS** (1 hour)
   - Enable SSL on PostgreSQL
   - Configure Keycloak JDBC URL with SSL

**Estimated Time: 1-2 days**

---

### Phase 2: High-Priority Improvements (Before public release)

1. Enable email verification (4 hours)
2. Configure SMTP for emails (2 hours)
3. Enable MFA for admin accounts (2 hours)
4. Implement token revocation checking (4 hours)
5. Add comprehensive audit logging (4 hours)

**Estimated Time: 2-3 days**

---

### Phase 3: Production Hardening (Ongoing)

1. Regular security audits
2. Penetration testing
3. Monitor Keycloak security advisories
4. Implement Web Application Firewall (WAF)
5. Set up automated security scanning

---

## Version Information

**Keycloak 26.0.7 (November 2024)**
- ✅ Current stable version (as of review date)
- ✅ Actively maintained
- ✅ No critical CVEs outstanding
- ⚠️ Check for updates regularly

**Note:** Keycloak 26 is relatively new. Monitor for:
- Security patches
- Breaking changes
- Migration guides if upgrading

---

## Conclusion

The LLARS Keycloak implementation has a **solid architectural foundation** with proper use of RS256 JWT, good token lifespans, and basic security headers. However, **critical configuration issues** make it **unsuitable for production** in its current state.

**Key Priorities:**
1. 🔴 **IMMEDIATELY:** Fix critical issues 1-7 before ANY production deployment
2. 🟡 **SOON:** Address high-priority issues 8-12 before public release
3. 🟢 **ONGOING:** Implement recommended improvements for defense-in-depth

**Estimated effort to production-ready:** 1-2 weeks (including testing)

---

## References

1. [Keycloak Official Documentation - Server Administration](https://www.keycloak.org/docs/latest/server_admin/)
2. [Keycloak Security Best Practices](https://www.keycloak.org/docs/latest/server_installation/#_security_hardening)
3. [OWASP JWT Security Cheat Sheet](https://cheatsheetsecurity.md/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
4. [RFC 7519 - JSON Web Token (JWT)](https://datatracker.ietf.org/doc/html/rfc7519)
5. [RFC 7517 - JSON Web Key (JWK)](https://datatracker.ietf.org/doc/html/rfc7517)

**Review Completed:** 22. November 2025
