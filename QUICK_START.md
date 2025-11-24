# 🚀 LLARS Authentik Quick Start

## ✅ Status: Authentik läuft!

Authentik-Server ist **erfolgreich gestartet** und läuft auf:
- **URL:** http://localhost:55095

---

## 📋 Schritt-für-Schritt Anleitung

### **Schritt 1: Authentik Admin öffnen**

```bash
open http://localhost:55095
```

**Oder im Browser:** http://localhost:55095

---

### **Schritt 2: Bootstrap-Admin Login**

Du wirst zur Login-Seite weitergeleitet.

**Credentials:**
```
Email:    admin@example.com
Passwort: admin123
```

---

### **Schritt 3: OAuth2 Provider erstellen (Frontend)**

1. Nach Login → **Admin Interface** (oben rechts)
2. **Applications** → **Providers** → **Create**
3. **Provider Type:** OAuth2/OpenID Connect

**Konfiguration:**
```
Name: llars-frontend-provider
Authorization flow: default-provider-authorization-explicit-consent
Client type: Public
Client ID: llars-frontend

Redirect URIs/Origins (Pflichtfeld):
http://localhost:55080/*
http://127.0.0.1:55080/*

Signing Key: authentik Self-signed Certificate (Standard)
```

**Wichtig:** Bei "Redirect URIs" auf **Add** klicken für jede URL!

4. **Finish** klicken und **Provider speichern**

---

### **Schritt 4: Application erstellen (Frontend)**

1. **Applications** → **Applications** → **Create**

**Konfiguration:**
```
Name: LLARS Frontend
Slug: llars-frontend
Provider: llars-frontend-provider (aus Schritt 3)
Launch URL: http://localhost:55080
```

2. **Create** klicken

---

### **Schritt 5: OAuth2 Provider erstellen (Backend)** ⚠️

1. **Applications** → **Providers** → **Create**
2. **Provider Type:** OAuth2/OpenID Connect

**Konfiguration:**
```
Name: llars-backend-provider
Authorization flow: default-provider-authorization-explicit-consent
Client type: Confidential
Client ID: llars-backend
Client secret: llars-backend-secret-change-in-production

Redirect URIs:
http://localhost:55080/*
```

3. **Finish** und Speichern

---

### **Schritt 6: Application erstellen (Backend)**

1. **Applications** → **Applications** → **Create**

**Konfiguration:**
```
Name: LLARS Backend
Slug: llars-backend
Provider: llars-backend-provider (aus Schritt 5)
```

2. **Create** klicken

---

### **Schritt 7: Test-User erstellen**

1. **Directory** → **Users** → **Create**

**User 1 - Admin:**
```
Username: admin
Name: Admin User
Email: admin@llars.local
Active: ✓ (Haken setzen)
```

2. **Create** klicken
3. User öffnen → **Actions** → **Set password**
4. Passwort: `admin123` → **Set password**

**Wichtig:** Wiederhole für weitere User:

**User 2 - Researcher:**
```
Username: researcher
Email: researcher@llars.local
Password: researcher123
```

**User 3 - Viewer:**
```
Username: viewer
Email: viewer@llars.local
Password: viewer123
```

---

## 🎯 Login testen!

### **Schritt 8: LLARS Frontend öffnen**

```bash
open http://localhost:55080
```

**Du siehst:** Login-Seite mit Username/Password-Feldern

---

### **Schritt 9: Login**

**Credentials eingeben:**
```
Username: admin
Password: admin123
```

**Auf "Login" klicken**

---

### **Schritt 10: Was passiert beim Login?**

**Frontend sendet Request:**
```
POST http://localhost:55095/application/o/llars-frontend/token
```

**Authentik antwortet mit:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "...",
  "token_type": "Bearer"
}
```

**Frontend speichert Token:**
```javascript
sessionStorage.setItem('kc_token', access_token)
```

**Redirect:**
- Admin → `/AdminDashboard`
- Andere → `/Home`

---

## ✅ Login erfolgreich!

Nach erfolgreichem Login solltest du:
- Im Dashboard sein (`/AdminDashboard` oder `/Home`)
- Oben rechts deinen Username sehen
- Zugriff auf Features haben (je nach Rolle)

---

## 🔍 Login-Probleme beheben

### **Problem 1: "Invalid client_id" Fehler**

**Ursache:** Provider/Application nicht richtig konfiguriert

**Lösung:**
1. Authentik Admin → **Applications** → **Providers**
2. Prüfe: `llars-frontend-provider` existiert
3. Öffne Provider → **Client ID** muss sein: `llars-frontend`

---

### **Problem 2: "Invalid redirect_uri"**

**Ursache:** Redirect-URL nicht in Provider konfiguriert

**Lösung:**
1. Provider öffnen → **Redirect URIs/Origins**
2. Muss enthalten: `http://localhost:55080/*`
3. **Add** klicken und speichern!

---

### **Problem 3: Login-Formular lädt nicht**

**Browser Console öffnen (F12):**
```javascript
// Prüfe ob Frontend Authentik erreicht
fetch('http://localhost:55095/application/o/llars-frontend/.well-known/openid-configuration')
  .then(r => r.json())
  .then(console.log)
```

**Erwartete Response:** OIDC-Konfiguration als JSON

**Falls Fehler:** Prüfe ob Authentik läuft:
```bash
docker compose ps authentik-server
curl http://localhost:55095/-/health/ready/
```

---

### **Problem 4: 401 Unauthorized nach Login**

**Backend-Logs prüfen:**
```bash
docker compose logs backend-flask-service | grep -i "token\|401"
```

**Mögliche Ursache:**
- Backend kann JWKS nicht laden
- Token-Signatur ungültig

**Fix:**
```bash
# JWKS-Endpoint testen
curl http://localhost:55095/application/o/llars-backend/.well-known/jwks.json

# Sollte JSON mit "keys" Array zurückgeben
```

---

## 🧪 Token manuell testen

**1. Token holen (nach Login):**
```javascript
// Browser Console (F12)
sessionStorage.getItem('kc_token')
```

**2. Token kopieren und API testen:**
```bash
TOKEN="<dein-token>"

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:55080/auth/me
```

**Erwartete Response:**
```json
{
  "username": "admin",
  "user_id": "...",
  "roles": ["admin"],
  "email": "admin@llars.local"
}
```

---

## 📊 Übersicht: Was du konfiguriert hast

### ✅ Authentik-Komponenten

| Komponente | Name | Status |
|------------|------|--------|
| Provider (Frontend) | llars-frontend-provider | ✓ |
| Provider (Backend) | llars-backend-provider | ✓ |
| Application (Frontend) | LLARS Frontend | ✓ |
| Application (Backend) | LLARS Backend | ✓ |
| User (Admin) | admin | ✓ |
| User (Researcher) | researcher | ✓ |
| User (Viewer) | viewer | ✓ |

### ✅ LLARS-Services

| Service | URL | Status |
|---------|-----|--------|
| Frontend | http://localhost:55080 | ✓ Running |
| Backend API | http://localhost:55080/api | ✓ Running |
| Authentik | http://localhost:55095 | ✓ Running |
| Auth Health | http://localhost:55080/auth/health_check | ✓ OK |

---

## 🎉 Nächste Schritte

Nach erfolgreichem Login kannst du:

### **Als Admin:**
1. **Permission-Dashboard öffnen:**
   ```
   http://localhost:55080/AdminPermissions
   ```
   - User verwalten
   - Rollen zuweisen
   - Berechtigungen prüfen

2. **Alle Features nutzen:**
   - Mail Rating
   - Ranking
   - Prompt Engineering
   - etc.

### **Als Researcher:**
- Edit-Zugriff auf Features
- Keine Admin-Funktionen

### **Als Viewer:**
- View-Only Zugriff
- Eingeschränkte Navigation

---

## 🆘 Wenn gar nichts funktioniert

**Kompletter Reset:**
```bash
# Container stoppen
docker compose down

# Volumes NICHT löschen (behält User/Config)
# Nur neu starten
docker compose up -d

# Warten bis alles läuft
sleep 30
docker compose ps
```

**Dann nochmal versuchen:** http://localhost:55080

---

## 📞 Support

**Logs ansehen:**
```bash
# Alle Services
docker compose logs --follow

# Nur Authentik
docker compose logs authentik-server --follow

# Nur Backend
docker compose logs backend-flask-service --follow
```

**Weitere Dokumentation:**
- `AUTHENTIK_SETUP.md` - Detaillierte Setup-Doku
- `LOGIN_ANLEITUNG.md` - Login-Troubleshooting
- `CLAUDE.md` - Projekt-Übersicht

---

**Viel Erfolg! 🚀**
