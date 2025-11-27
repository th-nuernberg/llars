# Authentik Setup Script - Summary

## Created Files

```
/Users/philippsteigerwald/PycharmProjects/llars/scripts/
├── setup_authentik.sh              # Main setup script (executable)
├── README_AUTHENTIK_SETUP.md       # Comprehensive documentation
├── QUICK_START.md                  # Quick reference guide
└── SETUP_SUMMARY.md                # This file
```

## Purpose

This setup script **manually configures Authentik** when the automatic initialization in Flask backend fails. It replaces the need for manual configuration via Authentik UI.

## Key Features

### 1. Complete Configuration
- ✅ Authentication Flow (llars-api-authentication)
- ✅ OAuth2 Providers (backend + frontend)
- ✅ Applications (LLARS Backend + Frontend)
- ✅ Test Users (admin, akadmin, researcher, viewer)
- ✅ RS256 signing with self-signed certificate
- ✅ Proper scope mappings

### 2. Production Ready
- Idempotent (safe to run multiple times)
- Error handling (exits on failure)
- Colored output (success/error/info)
- Verification step at the end
- Clear security warnings

### 3. Well Documented
- Inline comments explaining each step
- Comprehensive README with troubleshooting
- Quick start guide for rapid deployment
- Production deployment checklist

## Usage

### Basic Usage

```bash
# From project root
./scripts/setup_authentik.sh
```

### After Initial Setup

```bash
# Start LLARS
./start_llars.sh

# Wait for Authentik
sleep 30

# Configure Authentik
./scripts/setup_authentik.sh

# Verify
open http://localhost:55080/login
```

## What Gets Created

### Authentication Flow: llars-api-authentication

```
┌─────────────────────────────────────┐
│ Stage 1: Identification             │
│ - Accept username or email          │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│ Stage 2: Password                   │
│ - Validate against user database    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│ Stage 3: User Login                 │
│ - Create session                    │
└─────────────────────────────────────┘
```

### OAuth2 Providers

| Provider | Client ID | Type | Secret | Algorithm |
|----------|-----------|------|--------|-----------|
| llars-backend-provider | llars-backend | Confidential | llars-backend-secret-change-in-production | RS256 |
| llars-frontend-provider | llars-frontend | Public | None | RS256 |

### Applications

| Application | Slug | Provider |
|-------------|------|----------|
| LLARS Backend | llars-backend | llars-backend-provider |
| LLARS Frontend | llars-frontend | llars-frontend-provider |

### Test Users

| Username | Password | Email | Groups |
|----------|----------|-------|--------|
| admin | admin123 | admin@localhost | authentik Admins |
| akadmin | admin123 | akadmin@localhost | authentik Admins |
| researcher | admin123 | researcher@localhost | - |
| viewer | admin123 | viewer@localhost | - |

## Integration with LLARS

### Backend (Flask)

The backend uses the Flow Executor API for authentication:

```python
# app/auth/authentik_login.py
def login(username, password):
    # 1. Start flow
    GET /api/v3/flows/executor/llars-api-authentication/

    # 2. Submit username
    POST /api/v3/flows/executor/llars-api-authentication/

    # 3. Submit password
    POST /api/v3/flows/executor/llars-api-authentication/

    # 4. Get OAuth2 authorization code
    # 5. Exchange code for token
    POST /application/o/token/

    return access_token, id_token
```

### Frontend (Vue.js)

The frontend stores tokens in sessionStorage:

```javascript
// llars-frontend/src/composables/useAuth.js
const auth = useAuth()

await auth.login('admin', 'admin123')
// → Stores auth_token and auth_llars_roles in sessionStorage

auth.logout()
// → Clears sessionStorage and redirects to /login
```

## Verification Checklist

After running the script, verify:

- [ ] Script completed without errors
- [ ] Green "Setup Complete!" message shown
- [ ] Can access Authentik UI (http://localhost:55095)
- [ ] Can login to Authentik with akadmin/admin123
- [ ] Can see providers in Applications → Providers
- [ ] Can see applications in Applications → Applications
- [ ] Can login to LLARS with admin/admin123
- [ ] Dashboard loads after login

## Common Issues & Solutions

### "Authentik server is not running"
```bash
docker compose up -d authentik-server
sleep 30
./scripts/setup_authentik.sh
```

### "No self-signed certificate found"
```bash
# Authentik didn't initialize properly
docker compose down
docker compose up -d authentik-server
sleep 60  # Wait longer
./scripts/setup_authentik.sh
```

### Login fails with "Invalid credentials"
```bash
# Reset password
docker compose exec -T authentik-server ak shell -c "
from authentik.core.models import User
u = User.objects.get(username='admin')
u.set_password('admin123')
u.save()
"
```

## Production Deployment

**CRITICAL:** Before deploying to production:

1. **Change Secrets** (lines ~95-100 in script):
   ```bash
   client_secret='llars-backend-secret-change-in-production'
   # → Use: openssl rand -hex 32
   ```

2. **Change Passwords**:
   - Don't use `admin123` in production
   - Set strong passwords for all users

3. **Update Redirect URIs** (lines ~102, 118):
   ```bash
   redirect_uris='https://llars.your-domain.de/auth/callback'
   ```

4. **Enable HTTPS**:
   - Configure nginx SSL/TLS
   - Set `AUTHENTIK_COOKIE_SECURE=true` in .env

5. **Remove Test Users** (optional):
   - Delete `researcher` and `viewer` if not needed

## Related Documentation

- **CLAUDE.md** - Main LLARS documentation (Authentik section)
- **README_AUTHENTIK_SETUP.md** - Full setup documentation
- **QUICK_START.md** - Quick reference guide
- **docs/AUTHENTIK_TESTING_PLAN.md** - Testing procedures

## Script Details

### Technologies Used
- **Bash**: Shell scripting with error handling
- **Docker Compose**: Container orchestration
- **Authentik Management**: `ak shell` Django ORM commands
- **Color Output**: ANSI color codes for better UX

### Design Principles
1. **Idempotency**: Use `get_or_create()` and `update_or_create()`
2. **Fail Fast**: Exit immediately on error (`set -e`)
3. **Clear Feedback**: Colored output with symbols (✓, ℹ, ✗)
4. **Defensive**: Check prerequisites before running
5. **Documented**: Inline comments + separate docs

### Error Handling
```bash
# Check Docker installed
command -v docker || exit 1

# Check Authentik running
docker compose ps | grep -q "authentik-server.*running" || exit 1

# Check required objects exist
cert = CertificateKeyPair.objects.filter(...).first()
if not cert:
    print("ERROR: No certificate found!")
    exit(1)
```

## Maintenance

### Re-running Script
Safe to run multiple times - it will update existing objects:
```bash
./scripts/setup_authentik.sh
# → Shows "ℹ Updated existing..." for existing objects
```

### Complete Reset
To start fresh (DELETES ALL DATA):
```bash
# WARNING: Deletes all Authentik data!
docker compose down -v
docker compose up -d
sleep 60
./scripts/setup_authentik.sh
```

### Updating Configuration
To change provider settings:
1. Edit script (e.g., change redirect_uris)
2. Re-run script
3. Configuration will be updated (uses `update_or_create`)

## Success Metrics

After successful execution, you should see:

```
========================================
Setup Complete!
========================================

Authentik has been configured with:

Authentication Flow:
  • llars-api-authentication (Identification → Password → Login)

OAuth2 Providers:
  • llars-backend-provider (confidential, RS256)
    - Client ID: llars-backend
    - Client Secret: llars-backend-secret-change-in-production
  • llars-frontend-provider (public, RS256)
    - Client ID: llars-frontend

Applications:
  • LLARS Backend (linked to backend provider)
  • LLARS Frontend (linked to frontend provider)

Test Users:
  • admin / admin123 (admin)
  • akadmin / admin123 (admin)
  • researcher / admin123 (researcher)
  • viewer / admin123 (viewer)
```

## Support

If you encounter issues not covered in documentation:

1. **Check Logs**:
   ```bash
   docker compose logs authentik-server --tail=100
   docker compose logs backend-flask-service | grep -i authentik
   ```

2. **Verify Configuration**:
   ```bash
   grep AUTHENTIK .env
   ```

3. **Run Manual Verification** (see README_AUTHENTIK_SETUP.md)

4. **Check Authentik UI**: http://localhost:55095
   - Login: akadmin / admin123
   - Check: Applications → Providers, Applications, Flows

---

**Created:** 2025-11-27
**Version:** 1.0
**Author:** Claude (Anthropic)
**Purpose:** Manual Authentik configuration for LLARS
