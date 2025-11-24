# Authentik Setup für LLARS

## 🚀 Schnellstart (Automatisch)

Das Python-Skript richtet alles automatisch ein:

```bash
# Skript ausführbar machen
chmod +x setup_authentik.py

# Authentik muss laufen
docker compose up -d authentik-server

# Warten bis Authentik bereit ist (ca. 30-60 Sekunden)
sleep 30

# Setup ausführen
python3 setup_authentik.py
```

**Das Skript erstellt:**
- ✅ OAuth2 Provider für Frontend (Public Client)
- ✅ OAuth2 Provider für Backend (Confidential Client)
- ✅ Applications "llars-frontend" und "llars-backend"
- ✅ 3 Test-User: `admin`, `researcher`, `viewer`

---

## 👤 Test-User Credentials

Nach dem Setup kannst du dich mit diesen Accounts einloggen:

| Username | Password | Email | Rolle |
|----------|----------|-------|-------|
| `admin` | `admin123` | admin@llars.local | Administrator |
| `researcher` | `researcher123` | researcher@llars.local | Researcher |
| `viewer` | `viewer123` | viewer@llars.local | Viewer |

---

## 🔐 Login-Anleitung

### **1. LLARS Frontend öffnen**
```bash
open http://localhost:55080
# oder im Browser: http://localhost:55080
```

### **2. Login-Button klicken**
- Du wirst zur Login-Seite weitergeleitet
- Formular zeigt Username & Password Felder

### **3. Credentials eingeben**
```
Username: admin
Passwort: admin123
```

### **4. Nach erfolgreichem Login:**
- Du wirst zu `/Home` oder `/AdminDashboard` weitergeleitet (je nach Rolle)
- Token wird in `sessionStorage` gespeichert
- Alle API-Calls nutzen automatisch den Bearer-Token

---

## 🛠️ Manuelle Konfiguration (falls Skript fehlschlägt)

### **Schritt 1: Authentik Admin öffnen**
```bash
open http://localhost:55090
```

**Bootstrap Admin Login:**
- Email: `admin@example.com`
- Passwort: `admin123`

---

### **Schritt 2: OAuth2 Provider erstellen (Frontend)**

1. **Admin-Interface** → **Applications** → **Providers**
2. **Create** → **OAuth2/OpenID Provider**

**Konfiguration:**
```yaml
Name: llars-frontend-provider
Client Type: Public
Client ID: llars-frontend
Authorization Flow: default-provider-authorization-explicit-consent
Redirect URIs:
  - http://localhost:55080/*
  - http://127.0.0.1:55080/*
Signing Key: authentik Self-signed Certificate
Subject Mode: Based on User's hashed ID
```

**Speichern** → Notiere dir die **Provider ID**

---

### **Schritt 3: Application erstellen (Frontend)**

1. **Admin-Interface** → **Applications** → **Applications**
2. **Create**

**Konfiguration:**
```yaml
Name: LLARS Frontend
Slug: llars-frontend
Provider: llars-frontend-provider (aus Schritt 2)
Launch URL: http://localhost:55080
```

**Speichern**

---

### **Schritt 4: OAuth2 Provider erstellen (Backend)**

1. **Admin-Interface** → **Applications** → **Providers**
2. **Create** → **OAuth2/OpenID Provider**

**Konfiguration:**
```yaml
Name: llars-backend-provider
Client Type: Confidential
Client ID: llars-backend
Client Secret: llars-backend-secret-change-in-production
Authorization Flow: default-provider-authorization-explicit-consent
Redirect URIs:
  - http://localhost:55080/*
Signing Key: authentik Self-signed Certificate
```

**Speichern** → Notiere dir die **Provider ID**

---

### **Schritt 5: Application erstellen (Backend)**

1. **Admin-Interface** → **Applications** → **Applications**
2. **Create**

**Konfiguration:**
```yaml
Name: LLARS Backend
Slug: llars-backend
Provider: llars-backend-provider (aus Schritt 4)
Launch URL: http://localhost:55080
```

**Speichern**

---

### **Schritt 6: Test-User erstellen**

1. **Admin-Interface** → **Directory** → **Users**
2. **Create**

**User 1 - Admin:**
```yaml
Username: admin
Name: Admin User
Email: admin@llars.local
Active: ✓
Path: users
```
- **Speichern**
- **Set Password** → `admin123`

**User 2 - Researcher:**
```yaml
Username: researcher
Name: Researcher User
Email: researcher@llars.local
Active: ✓
```
- **Set Password** → `researcher123`

**User 3 - Viewer:**
```yaml
Username: viewer
Name: Viewer User
Email: viewer@llars.local
Active: ✓
```
- **Set Password** → `viewer123`

---

## 🔍 Troubleshooting

### **Problem: Authentik Server startet nicht**

```bash
# Logs prüfen
docker compose logs authentik-server --tail=100

# Häufige Ursachen:
# 1. PostgreSQL nicht bereit
docker compose logs authentik-db

# 2. Port-Konflikt (55090 belegt)
lsof -i :55090

# 3. Container neu starten
docker compose restart authentik-server
```

---

### **Problem: Login funktioniert nicht**

**1. Provider-Konfiguration prüfen:**
- Authentik Admin → Applications → Providers
- "llars-frontend-provider" öffnen
- **Redirect URIs** muss `http://localhost:55080/*` enthalten

**2. Browser-Console prüfen:**
```javascript
// F12 → Console
// Fehler bei Token-Request?
```

**3. Backend-Token-Validierung testen:**
```bash
# Token holen (manuell über Authentik UI)
TOKEN="eyJhbGc..."

# Backend-Validierung testen
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:55080/auth/me
```

---

### **Problem: "Invalid audience" Error**

**Backend-Logs prüfen:**
```bash
docker compose logs backend-flask-service | grep -i audience
```

**Fix in `app/auth/oidc_validator.py`:**
- Zeile 172-174: Audience-Check ist flexibel implementiert
- Prüfe `client_id` in `.env` vs. Token `aud` claim

---

### **Problem: JWKS-Key nicht gefunden**

```bash
# JWKS-Endpoint testen
curl http://localhost:55090/application/o/llars-backend/.well-known/jwks.json
```

**Muss JSON mit `keys` Array zurückgeben:**
```json
{
  "keys": [
    {
      "kid": "...",
      "kty": "RSA",
      "use": "sig",
      "n": "...",
      "e": "AQAB"
    }
  ]
}
```

---

## 🧪 Login testen

### **Test 1: Frontend-Login**
```bash
1. Open http://localhost:55080
2. Username: admin
3. Password: admin123
4. Check Browser Console (F12) für Token
```

### **Test 2: Backend-API mit Token**
```bash
# 1. Token aus sessionStorage kopieren
# Browser Console:
# sessionStorage.getItem('kc_token')

# 2. API-Call testen
TOKEN="<your-token>"
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:55080/auth/me

# Erwartete Response:
# {
#   "username": "admin",
#   "roles": [...],
#   "email": "admin@llars.local"
# }
```

### **Test 3: Permission-System**
```bash
# Als Admin einloggen und Permission-Dashboard öffnen
open http://localhost:55080/AdminPermissions

# Sollte 3 Tabs zeigen:
# - Benutzer
# - Rollen
# - Berechtigungen
```

---

## 📚 Weitere Ressourcen

- **Authentik Docs:** https://docs.goauthentik.io/
- **OIDC Flow:** https://docs.goauthentik.io/docs/providers/oauth2/
- **LLARS Auth:** `app/auth/oidc_validator.py`
- **Frontend Auth:** `llars-frontend/src/composables/useAuth.js`

---

## ✅ Setup-Checklist

Nach erfolgreichem Setup solltest du:

- [ ] Authentik Admin UI erreichbar (Port 55090)
- [ ] 2 Provider erstellt (frontend + backend)
- [ ] 2 Applications erstellt
- [ ] 3 Test-User angelegt
- [ ] LLARS Frontend erreichbar (Port 55080)
- [ ] Login mit Test-User erfolgreich
- [ ] `/auth/me` API-Call funktioniert
- [ ] Permission-Dashboard sichtbar (für Admin)

---

**Bei Problemen:** Siehe Troubleshooting-Abschnitt oder LLARS Logs prüfen:
```bash
docker compose logs --follow
```
