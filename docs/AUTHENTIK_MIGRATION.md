# Authentik Migration - LLARS Authentication

**Status:** ABGESCHLOSSEN
**Datum:** 25. November 2025
**Autor:** Claude Code

---

## Zusammenfassung

Die Authentik-Integration wurde erfolgreich implementiert:
- **Login:** Funktioniert über Flow Executor API
- **Token:** RS256-signiert, validierbar über JWKS
- **Validierung:** Korrekte Token-Prüfung im Backend
- **Dev/Prod Parity:** Gleiche Authentifizierungslogik in beiden Modi

---

## Problem-Zusammenfassung

### Ursprünglicher Zustand (Kritische Sicherheitsprobleme)

Die LLARS-Authentifizierung hatte mehrere kritische Probleme:

1. **Direkte Datenbank-Zugriffe**: Der Login-Endpoint griff direkt auf Authentik's PostgreSQL-Datenbank zu, statt die OAuth2/OIDC-APIs zu nutzen
2. **HS256 JWT-Tokens**: Eigene Tokens wurden mit HS256 signiert, statt Authentik's RS256-signierte Tokens zu verwenden
3. **Hardcoded Development-Passwort**: `admin123` wurde als universelles Passwort im Development-Modus akzeptiert
4. **Dev/Prod Parity verletzt**: Unterschiedliche Authentifizierungslogik für Development und Production

### Gewünschter Zustand

- Vollständige OIDC-Integration mit Authentik
- RS256-signierte JWT-Tokens (validierbar über JWKS-Endpoint)
- Gleiche Authentifizierungslogik für Development und Production
- Kein direkter Datenbankzugriff auf Authentik

---

## Lösung: Authentik Flow Executor API

### Architektur

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

### Warum Flow Executor API?

Authentik unterstützt **keinen** klassischen Resource Owner Password Credentials (ROPC) Grant. Stattdessen:

- `client_credentials` Grant funktioniert nur mit Service Accounts, nicht mit Benutzer-Passwörtern
- `password` Grant wird von Authentik wie `client_credentials` behandelt

Die Lösung ist die **Flow Executor API**:
1. Programmieren des gleichen Flows, den ein Benutzer im Browser durchlaufen würde
2. Nach erfolgreicher Flow-Authentifizierung: OAuth2 Authorization Code holen
3. Code gegen Token austauschen

---

## Implementierte Änderungen

### 1. Authentik Provider RS256 Konfiguration

Beide Provider wurden auf RS256 umgestellt:

```python
# In Authentik Shell
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.crypto.models import CertificateKeyPair

cert = CertificateKeyPair.objects.filter(name__contains="Self-signed").first()
for provider in OAuth2Provider.objects.all():
    provider.signing_key = cert
    provider.save()
```

### 2. Custom Authentication Flow erstellt

Flow: `llars-api-authentication`

Stages:
1. `IdentificationStage` - Benutzer-Identifikation (ohne MFA)
2. `PasswordStage` - Passwort-Validierung
3. `UserLoginStage` - Session erstellen

### 3. Backend Login-Endpoint

**Datei:** `app/routes/authentik_routes.py`

```python
@authentik_auth_blueprint.route('/login', methods=['POST'])
def login():
    # 1. Flow starten
    session.get(f"{authentik_url}/api/v3/flows/executor/{flow_slug}/")

    # 2. Username submitten
    session.post(flow_url, json={'uid_field': username})

    # 3. Passwort submitten
    session.post(flow_url, json={'password': password})

    # 4. OAuth2 Authorization Code holen
    session.get(auth_url, params={
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'openid profile email'
    })

    # 5. Code gegen Token austauschen
    requests.post(token_url, data={
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret
    })
```

### 4. Token-Validierung (nur RS256)

**Datei:** `app/auth/oidc_validator.py`

```python
def validate_token(token: str) -> Optional[Dict]:
    # Nur RS256 akzeptieren
    if alg != 'RS256':
        print(f"Unsupported token algorithm: {alg}. Only RS256 is accepted.")
        return None

    # Key von JWKS-Endpoint holen
    public_key = get_public_key(kid)

    # Token validieren
    decoded = jwt.decode(token, public_key, algorithms=['RS256'], ...)
```

---

## Konfiguration

### Umgebungsvariablen (.env)

```bash
# Authentik Basis-URL (intern vom Backend erreichbar)
AUTHENTIK_INTERNAL_URL=http://authentik-server:9000

# OAuth2 Client-Konfiguration
AUTHENTIK_BACKEND_CLIENT_ID=llars-backend
AUTHENTIK_BACKEND_CLIENT_SECRET=llars-backend-secret-change-in-production

# OIDC Issuer URL (für Token-Validierung)
AUTHENTIK_ISSUER_URL=http://authentik-server:9000/application/o/llars-backend/
```

### Authentik Provider-Einstellungen

| Einstellung | Wert |
|------------|------|
| Client ID | `llars-backend` |
| Client Type | Confidential |
| Signing Algorithm | RS256 |
| Signing Key | Self-signed Certificate |
| Redirect URIs | `http://authentik-server:9000/` (für Code-Exchange) |
| Authorization Flow | `default-provider-authorization-implicit-consent` |

---

## Implementierungsstatus

### Erfolgreich implementiert

- [x] RS256-Konfiguration in Authentik
- [x] JWKS-Endpoint erreichbar vom Backend (`/application/o/llars-backend/jwks/`)
- [x] Custom Authentication Flow ohne MFA (`llars-api-authentication`)
- [x] Flow Executor API - Username-Authentifizierung
- [x] Flow Executor API - Passwort-Authentifizierung
- [x] OAuth2 Authorization Code Flow
- [x] Token-Exchange
- [x] Backend Login-Endpoint Delegation
- [x] Token-Validierung via JWKS
- [x] Client Secret Synchronisierung

### Behobene Probleme

1. **JWKS URL falsch**: Code verwendete `/.well-known/jwks.json`, Authentik nutzt `/jwks/`
2. **Client Secret Mismatch**: Secret in .env stimmte nicht mit Authentik überein
3. **Login-Endpoint dupliziert**: Alter Login-Code in `routes.py` überschrieb neuen Code

---

## Troubleshooting

### Passwort ungültig obwohl korrekt

```bash
# Passwort in Authentik setzen
docker compose exec -T authentik-server ak shell -c "
from authentik.core.models import User
user = User.objects.get(username='akadmin')
user.set_password('admin123')
user.save()
"
```

### RS256 Provider prüfen

```bash
docker compose exec -T authentik-server ak shell -c "
from authentik.providers.oauth2.models import OAuth2Provider
for p in OAuth2Provider.objects.all():
    print(f'{p.name}: signing_key={p.signing_key}')
"
```

### JWKS-Endpoint testen

```bash
docker compose exec -T backend-flask-service curl -s \
  http://authentik-server:9000/application/o/llars-backend/jwks/ | jq .
```

---

## Referenzen

- [Authentik OIDC Provider Docs](https://goauthentik.io/docs/providers/oauth2/)
- [Authentik Flow Executor API](https://goauthentik.io/docs/flows/)
- [RFC 6749 - OAuth 2.0](https://tools.ietf.org/html/rfc6749)
