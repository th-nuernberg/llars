# LLARS Keycloak Login Guide

## Problem: Endlose Weiterleitung zu Keycloak

Wenn du nach dem Login auf die Keycloak-Seite weitergeleitet wirst:
```
http://localhost:55090/realms/llars/protocol/openid-connect/auth?client_id=llars-frontend...
```

### Ursache

LLARS verwendet **Keycloak für die Frontend-Authentifizierung**, nicht das Legacy Backend-System.

Es gibt 2 separate Auth-Systeme:
- **Legacy Backend Auth** (Flask JWT) - für API-Tests (`/auth/register`, `/auth/login`)
- **Keycloak OIDC** - für das Frontend (moderne Authentifizierung)

### Lösung: Benutzer in Keycloak registrieren

## Option 1: Selbst-Registrierung (Empfohlen)

1. Öffne das Frontend: http://localhost:55173
2. Klicke auf **"Registrieren"** / **"Register"** auf der Keycloak-Login-Seite
3. Fülle das Formular aus:
   - Username: `testuser`
   - Email: `test@llars.local`
   - First Name: `Test`
   - Last Name: `User`
   - Password: `Test123!`
   - Password Confirmation: `Test123!`
4. Klicke auf **"Register"**
5. Du wirst automatisch eingeloggt und zum Frontend weitergeleitet

## Option 2: Über Keycloak Admin Console

1. Öffne Keycloak Admin: http://localhost:55090/admin
2. Login:
   - Username: `admin`
   - Password: `admin_secure_password_123`
3. Wähle Realm: **llars** (oben links)
4. Gehe zu **Users** → **Add user**
5. Fülle aus:
   - Username: `testuser`
   - Email: `test@llars.local`
   - First name: `Test`
   - Last name: `User`
   - Email verified: **ON**
   - Enabled: **ON**
6. Klicke **Create**
7. Gehe zum Tab **Credentials**
8. Klicke **Set password**
9. Setze Passwort: `Test123!`
10. Temporary: **OFF**
11. Klicke **Save**

## Option 3: Via Script (Automatisch)

```bash
# Im Terminal im Projektverzeichnis
docker exec -it llars_keycloak_service /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 \
  --realm master \
  --user admin \
  --password admin_secure_password_123

docker exec -it llars_keycloak_service /opt/keycloak/bin/kcadm.sh create users \
  -r llars \
  -s username=testuser \
  -s email=test@llars.local \
  -s firstName=Test \
  -s lastName=User \
  -s enabled=true \
  -s emailVerified=true

docker exec -it llars_keycloak_service /opt/keycloak/bin/kcadm.sh set-password \
  -r llars \
  --username testuser \
  --new-password Test123!
```

## Test-User Credentials

Nach der Registrierung kannst du dich einloggen mit:

```
URL:      http://localhost:55173
Username: testuser
Password: Test123!
```

## Warum 2 Auth-Systeme?

Das Legacy Backend-System (`/auth/register`, `/auth/login`) ist veraltet und wird nur noch für:
- API-Tests
- Rückwärtskompatibilität
- Legacy-Integrationen

verwendet.

**Das Frontend nutzt ausschließlich Keycloak** für:
- Moderne OAuth2/OIDC-Authentifizierung
- Single Sign-On (SSO)
- Bessere Sicherheit
- Zentrales Identity Management
