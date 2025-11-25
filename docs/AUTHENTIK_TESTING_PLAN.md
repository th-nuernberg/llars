# LLARS Authentik Testing & Setup Plan

**Datum:** 25. November 2025
**Status:** IN ARBEIT

---

## 1. Analyse: Warum waren Änderungen nötig?

### Ursprüngliche Probleme (Sicherheitskritisch)

Der ursprüngliche Authentifizierungscode hatte mehrere **kritische Sicherheitsprobleme**:

| Problem | Beschreibung | Risiko |
|---------|--------------|--------|
| **Direkter DB-Zugriff** | Login-Endpoint griff direkt auf Authentik's PostgreSQL zu | Bypassing OIDC, keine Token-Validierung |
| **HS256 Tokens** | Eigene JWT-Tokens mit HS256 signiert | Shared-Secret statt asymmetrischer Krypto |
| **Hardcoded Password** | `admin123` wurde in Dev-Mode immer akzeptiert | Massive Sicherheitslücke |
| **Dev/Prod Gap** | Unterschiedliche Auth-Logik für Development vs Production | Inkonsistentes Verhalten |

### Implementierte Lösung

```
Frontend (Vue.js)
      │
      │ POST /auth/login {username, password}
      ▼
Backend (Flask)
      │
      │ 1. Start Flow (GET /api/v3/flows/executor/llars-api-authentication/)
      │ 2. Submit Username (POST mit uid_field)
      │ 3. Submit Password (POST mit password)
      │ 4. OAuth2 Authorization Request
      │ 5. Exchange Code for Token
      ▼
Authentik (OIDC Provider)
      │
      │ RS256-signiertes JWT Token
      ▼
Backend → Frontend
```

### Sind diese Änderungen valide?

**JA** - Die Änderungen sind sicherheitstechnisch notwendig und korrekt:

1. **RS256 statt HS256**: Asymmetrische Kryptographie ist Best Practice für OIDC
2. **Flow Executor API**: Offizielle Authentik-Methode für headless/API Authentication
3. **JWKS-Validierung**: Standard-konforme Token-Validierung über öffentlichen Schlüssel
4. **Dev/Prod Parity**: Gleiche Logik in beiden Umgebungen

---

## 2. Identifizierte Probleme nach Neustart

### Problem 1: init-authentik.py wird nicht ausgeführt

Das Script erstellt Provider mit falschen Namen:
- Script erstellt: `llars-frontend-provider`, `llars-backend-provider`
- Backend erwartet: `llars-backend` (als client_id)

### Problem 2: Fehlende Authentik-Konfiguration

Nach Container-Neustart fehlen:
- Flow: `llars-api-authentication`
- OAuth2 Provider: `llars-backend`
- Application: `llars-backend`
- Scopes auf dem Provider

### Problem 3: Frontend Login funktioniert nicht

Route `/login` liefert vermutlich CORS-Probleme oder Token wird nicht korrekt gespeichert.

---

## 3. Test-Plan

### 3.1 Backend API Tests

| Test | Endpoint | Erwartetes Ergebnis |
|------|----------|---------------------|
| Health Check | `GET /auth/health_check` | `{"message": "Server is running"}` |
| Login Valid | `POST /auth/login` | RS256 Token zurück |
| Login Invalid | `POST /auth/login` (wrong pw) | `401 Invalid credentials` |
| Login Missing | `POST /auth/login` (no data) | `400 Username and password required` |
| Token Validate | `GET /auth/authentik/validate` | `{"valid": true, ...}` |
| User Info | `GET /auth/authentik/me` | User-Daten |

### 3.2 Frontend Tests

| Test | URL | Erwartetes Ergebnis |
|------|-----|---------------------|
| Login Page | `http://localhost:55080/login` | Login-Formular wird angezeigt |
| Login Submit | Form submit | Redirect zu `/` mit Token |
| Protected Route | `http://localhost:55080/` | Zeigt Home wenn eingeloggt |
| Token Persistence | Refresh Page | Bleibt eingeloggt |

### 3.3 LLM-as-Judge Auth Tests

| Test | Endpoint | Erwartetes Ergebnis |
|------|----------|---------------------|
| Sessions List | `GET /api/judge/sessions` | 200 mit Auth, 401 ohne |
| Create Session | `POST /api/judge/sessions` | Erfordert `feature:comparison:edit` |
| Start Session | `POST /api/judge/sessions/{id}/start` | Erfordert Auth |

### 3.4 OnCoCo Auth Tests

| Test | Endpoint | Erwartetes Ergebnis |
|------|----------|---------------------|
| Sessions List | `GET /api/oncoco/sessions` | 200 mit Auth, 401 ohne |
| Create Session | `POST /api/oncoco/sessions` | Erfordert Auth |
| Analysis Results | `GET /api/oncoco/sessions/{id}` | Erfordert Auth |

---

## 4. Authentik Setup-Anleitung

### 4.1 Benötigte Komponenten

Nach einem frischen Start müssen folgende Komponenten existieren:

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
   - Ohne MFA für API-Zugriff

4. **User** (`akadmin`)
   - Password muss gesetzt sein

### 4.2 Manuelle Setup-Befehle

```bash
# 1. Flow erstellen
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

# 2. OAuth2 Provider erstellen
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

# Create Application
app, created = Application.objects.get_or_create(
    slug='llars-backend',
    defaults={'name': 'LLARS Backend', 'provider': provider}
)
print(f'Application: {app.name} (created: {created})')
"

# 3. Password für akadmin setzen
docker compose exec -T authentik-server ak shell -c "
from authentik.core.models import User
user = User.objects.get(username='akadmin')
user.set_password('admin123')
user.save()
print('Password set for akadmin')
"
```

### 4.3 Automatisches Setup

Das `init-authentik.py` Script sollte korrigiert werden um:
1. Korrekte Provider-Namen zu verwenden (`llars-backend` statt `llars-backend-provider`)
2. Als Container-Entrypoint ausgeführt zu werden
3. Idempotent zu sein (mehrfache Ausführung sicher)

---

## 5. Durchgeführte Tests (Stand: 25.11.2025)

### Phase 1: Backend API (Priorität: HOCH) - ABGESCHLOSSEN

- [x] Health Check funktioniert (`GET /auth/health_check` -> `{"message": "Server is running"}`)
- [x] Login mit gültigen Credentials gibt RS256 Token (Token-Länge: 1676 Zeichen)
- [x] Login mit ungültigen Credentials wird abgelehnt (401)
- [x] Token-Validierung funktioniert (`GET /auth/authentik/validate`)
- [x] /me Endpoint gibt User-Info zurück (preferred_username, email, groups)

### Phase 2: Frontend (Priorität: HOCH) - KORRIGIERT

- [x] Login-Seite lädt (`http://localhost:55080/login`)
- [x] Login-Formular sendet korrekt an `/auth/authentik/login`
- [x] Token wird gespeichert (sessionStorage: `auth_token`, `auth_llars_roles`)
- [x] Protected Routes funktionieren (Router Guard prüft `auth_llars_roles`)
- [x] Logout funktioniert (löscht alle Auth-Daten)

**Bugfix durchgeführt:**
- `useAuth.js`: Nutzt jetzt `llars_roles` aus Backend-Response statt `realm_access.roles` (Keycloak-spezifisch)
- `router.js`: Router Guard prüft jetzt `auth_llars_roles` aus sessionStorage

### Phase 3: LLM-as-Judge (Priorität: MITTEL) - ABGESCHLOSSEN

- [x] Sessions-Liste erfordert Auth (ohne Auth: `{"error":"Missing authorization token"}`)
- [x] Mit Auth: 3 Sessions gefunden
- [x] Pillars-Endpoint funktioniert mit Auth (5 Säulen verfügbar)
- [ ] WebSocket Events erfordern Auth (nicht getestet)

### Phase 4: OnCoCo (Priorität: MITTEL) - ABGESCHLOSSEN

- [x] Analyses-Liste erfordert Auth (ohne Auth: `{"error":"Missing authorization token"}`)
- [x] Mit Auth: leere Liste (keine Analysen erstellt)
- [x] Pillars-Endpoint funktioniert (85 Threads in DB)
- [x] Info-Endpoint funktioniert (68 Labels, Modell verfügbar)

---

## 6. Bekannte Issues

| Issue | Status | Lösung |
|-------|--------|--------|
| init-authentik.py falsche Provider-Namen | OFFEN | Script korrigieren |
| init-authentik.py wird nicht ausgeführt | OFFEN | In docker-compose einbinden |
| Frontend nutzte `realm_access.roles` (Keycloak) | **BEHOBEN** | Geändert auf `llars_roles` aus Backend |
| Authentik-Konfiguration nicht persistent | WORKAROUND | Manuelle Befehle nach Neustart |

---

## 7. Durchgeführte Korrekturen

### 7.1 Frontend Auth-System angepasst

**Problem:** Das Frontend suchte nach `realm_access.roles` im Token (Keycloak-Format), aber Authentik verwendet `groups`.

**Lösung:**
1. Backend gibt `llars_roles` in der Login-Response zurück (basierend auf Authentik-Gruppen)
2. Frontend speichert `llars_roles` in sessionStorage
3. Router Guard und useAuth Composable nutzen `llars_roles` für Admin-Check

**Geänderte Dateien:**
- `llars-frontend/src/composables/useAuth.js`
- `llars-frontend/src/router.js`

### 7.2 Authentik-Komponenten manuell erstellt

Nach Container-Neustart wurden folgende Komponenten manuell via `ak shell` erstellt:
1. Flow: `llars-api-authentication` mit 3 Stages
2. OAuth2 Provider: `llars-backend` mit RS256 Signing Key
3. Application: `llars-backend`
4. Scope Mappings für User-Info (openid, profile, email)
5. Password für `akadmin` gesetzt

---

## 8. Nächste Schritte

1. ~~Frontend Login debuggen~~ **ERLEDIGT**
2. ~~LLM-as-Judge Endpoints testen~~ **ERLEDIGT**
3. ~~OnCoCo Endpoints testen~~ **ERLEDIGT**
4. init-authentik.py korrigieren (Provider-Namen)
5. Automatisches Setup bei Container-Start implementieren
6. WebSocket-Authentifizierung testen
