# 🔐 LLARS Login-Anleitung

## Status: Authentik-Integration vorbereitet ⚙️

Die Umstellung auf Authentik ist **code-seitig vollständig abgeschlossen**, aber Authentik-Server benötigt noch Konfiguration.

---

## 🎯 Zwei Optionen zum Testen

### **Option 1: Mit Authentik (Empfohlen - benötigt Setup)**

Authentik ist noch nicht konfiguriert. Siehe **Authentik Setup** unten.

### **Option 2: Development-Mode (Schnelltest)**

Für sofortiges Testen kannst du einen Mock-Auth-Endpoint erstellen:

```bash
# Quick Mock für Testing (temporär)
# Erstelle Test-Token-Endpoint

# Wird noch implementiert...
```

---

## 🛠️ Authentik Setup (Manuelle Methode)

Da das automatische Setup-Skript auf Authentik-Server-Probleme stößt, hier die manuelle Methode:

### **Problem: Authentik Server startet nicht**

**Diagnose:**
```bash
# Container-Status prüfen
docker compose ps authentik-server

# Logs prüfen
docker compose logs authentik-server --tail=100

# Exit-Code prüfen
docker compose ps -a | grep authentik-server
```

**Mögliche Ursachen:**
1. **DB-Credentials falsch** - Bereits behoben in vorherigen Steps
2. **Port-Konflikt** - Port 55090 belegt?
3. **Memory-Limit** - Authentik braucht min. 2GB RAM
4. **Healthcheck schlägt fehl** - DB nicht bereit

---

### **Fix 1: Authentik Server manuell starten**

```bash
# Alle Authentik-Services neu starten
docker compose down authentik-server authentik-worker
docker compose up -d authentik-db authentik-redis

# Warten bis DB healthy
sleep 10

# Server starten und Logs folgen
docker compose up authentik-server --no-deps

# In anderem Terminal prüfen:
curl http://localhost:55090/-/health/ready/
```

**Erwartete Response:** `{"status": "ok"}`

---

### **Fix 2: Authentik ohne Healthcheck starten**

Wenn Healthcheck das Problem ist:

```yaml
# In docker-compose.yml temporär:
authentik-server:
  # healthcheck: auskommentieren
  # ...
```

```bash
docker compose up -d authentik-server --force-recreate
```

---

### **Fix 3: Authentik Logs analysieren**

```bash
# Vollständige Logs
docker compose logs authentik-server > authentik_logs.txt

# Häufige Fehler:
grep -i "error\|failed\|exception" authentik_logs.txt

# DB-Connection-Fehler?
grep -i "postgres\|database" authentik_logs.txt
```

---

## 📋 Manuelle Authentik-Konfiguration (Web-UI)

**Sobald Authentik läuft** (erkennbar an: http://localhost:55090 erreichbar):

### **1. Erstmaliger Zugriff**

```bash
open http://localhost:55090
```

**Bootstrap-Admin:**
- Email: `admin@example.com`
- Passwort: `admin123`

---

### **2. Provider erstellen (OAuth2/OIDC)**

**Für Frontend (Public Client):**

1. **Admin-Interface** → **Applications** → **Providers** → **Create**
2. **Type:** OAuth2/OpenID Provider

```
Name: llars-frontend-provider
Client Type: Public
Client ID: llars-frontend
Redirect URIs:
  http://localhost:55080/*
  http://127.0.0.1:55080/*

Scopes: openid, email, profile
Access Token Validity: 10 minutes
Refresh Token Validity: 30 days
```

**Für Backend (Confidential Client):**

```
Name: llars-backend-provider
Client Type: Confidential
Client ID: llars-backend
Client Secret: llars-backend-secret-change-in-production
Redirect URIs: http://localhost:55080/*
```

---

### **3. Applications erstellen**

1. **Admin-Interface** → **Applications** → **Applications** → **Create**

**Frontend Application:**
```
Name: LLARS Frontend
Slug: llars-frontend
Provider: llars-frontend-provider (aus Step 2)
Launch URL: http://localhost:55080
```

**Backend Application:**
```
Name: LLARS Backend
Slug: llars-backend
Provider: llars-backend-provider
```

---

### **4. Test-User anlegen**

**Admin-Interface** → **Directory** → **Users** → **Create**

**User 1: Admin**
```
Username: admin
Email: admin@llars.local
Name: Admin User
Active: ✓

Nach Speichern → "Set Password" → admin123
```

**User 2: Researcher**
```
Username: researcher
Email: researcher@llars.local
Password: researcher123
```

**User 3: Viewer**
```
Username: viewer
Email: viewer@llars.local
Password: viewer123
```

---

## 🚀 Login-Test

### **Schritt 1: LLARS öffnen**
```bash
open http://localhost:55080
```

### **Schritt 2: Login**
- Du siehst die Login-Seite mit Username/Password-Feldern
- Die Felder sind verbunden mit `llars-frontend/src/composables/useAuth.js`

### **Schritt 3: Credentials eingeben**
```
Username: admin
Password: admin123
```

### **Schritt 4: Was passiert?**

**Frontend (useAuth.js:44):**
```javascript
// Sendet Request an:
POST http://localhost:55090/application/o/llars-frontend/token

// Mit Daten:
{
  client_id: "llars-frontend",
  grant_type: "password",
  username: "admin",
  password: "admin123",
  scope: "openid profile email"
}
```

**Authentik Response:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "...",
  "id_token": "...",
  "token_type": "Bearer",
  "expires_in": 600
}
```

**Frontend speichert:**
```javascript
sessionStorage.setItem('kc_token', access_token)
```

**Redirect:**
- Admin → `/AdminDashboard`
- Andere → `/Home`

---

### **Schritt 5: API-Calls nutzen Token**

**Automatisch via Axios Interceptor (main.js):**
```javascript
axios.interceptors.request.use(config => {
  const token = sessionStorage.getItem('kc_token')
  config.headers.Authorization = `Bearer ${token}`
  return config
})
```

**Backend validiert Token (app/auth/oidc_validator.py:136):**
```python
def validate_token(token):
    # Holt Public Key von Authentik
    public_key = get_public_key(kid)

    # Validiert JWT
    decoded = jwt.decode(
        token,
        public_key,
        algorithms=['RS256']
    )

    return decoded  # Username, Rollen, etc.
```

---

## 🧪 Login ohne Authentik testen (Dev-Workaround)

Wenn Authentik nicht funktioniert, kannst du den Token-Check temporär deaktivieren:

### **Backend-Bypass (NUR FÜR TESTING):**

```python
# In app/auth/decorators.py TEMPORÄR ändern:

@wraps(f)
def decorated_function(*args, **kwargs):
    # DEVELOPMENT BYPASS - REMOVE IN PRODUCTION!
    if os.getenv('AUTH_BYPASS', 'false') == 'true':
        g.keycloak_user = 'dev_admin'
        g.keycloak_user_id = 'dev-user-id'
        g.keycloak_token = {'realm_access': {'roles': ['admin']}}
        return f(*args, **kwargs)

    # Normale Token-Validierung...
```

```bash
# In .env:
AUTH_BYPASS=true

# Backend neu starten
docker compose restart backend-flask-service
```

**⚠️ WICHTIG:** Nur für lokales Testing! In Production entfernen!

---

## ✅ Login erfolgreich - Was nun?

Nach erfolgreichem Login siehst du:

### **Als Admin:**
- **Dashboard:** `/AdminDashboard`
- **Permissions:** `/AdminPermissions` (3 Tabs: User, Rollen, Permissions)
- **Alle Features:** Mail Rating, Ranking, Rating, etc.

### **Als Researcher:**
- **Home:** `/Home`
- **Features:** Edit-Zugriff auf meiste Features
- **Kein Admin-Dashboard**

### **Als Viewer:**
- **Home:** `/Home`
- **Features:** Nur View-Zugriff
- **Eingeschränkte Navigation**

---

## 🔍 Troubleshooting

### **Problem: "Cannot read properties of undefined"**

**Frontend Console (F12):**
```javascript
// Prüfe ob Token existiert
console.log(sessionStorage.getItem('kc_token'))

// Prüfe Auth-State
import { useAuth } from '@/composables/useAuth'
const auth = useAuth()
console.log(auth.isAuthenticated.value)
```

---

### **Problem: 401 Unauthorized**

```bash
# Backend-Logs prüfen
docker compose logs backend-flask-service | grep -i "token\|auth"

# Token manuell validieren
TOKEN="<your-token>"
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:55080/auth/validate
```

---

### **Problem: CORS-Fehler**

```bash
# Prüfe ALLOWED_ORIGINS in .env
grep ALLOWED_ORIGINS .env

# Sollte enthalten:
# http://localhost:55080,http://localhost:55173,...
```

---

## 📚 Nächste Schritte

1. **Authentik zum Laufen bringen:**
   ```bash
   docker compose logs authentik-server --follow
   # Fehler beheben
   ```

2. **Setup-Skript ausführen:**
   ```bash
   python3 setup_authentik.py
   ```

3. **Login testen:**
   ```bash
   open http://localhost:55080
   ```

4. **Permission-System nutzen:**
   - Als Admin einloggen
   - `/AdminPermissions` öffnen
   - Rollen zuweisen

---

## 🆘 Wenn gar nichts funktioniert

**Kompletter Reset:**
```bash
# Alle Container stoppen
docker compose down

# Volumes löschen (ACHTUNG: Löscht Daten!)
docker compose down -v

# Neu starten
./start_llars.sh

# Warten bis alles healthy
docker compose ps

# Authentik Server manuell starten
docker compose up -d authentik-server

# Logs verfolgen
docker compose logs authentik-server --follow
```

---

**Bei Fragen:** Siehe `AUTHENTIK_SETUP.md` oder LLARS Logs prüfen.
