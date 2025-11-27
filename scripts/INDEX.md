# LLARS Authentik Setup Scripts - Index

## Overview

This directory contains scripts and documentation for manually configuring Authentik authentication for LLARS when automatic initialization fails.

## Files

### 🔧 Executable Scripts

| File | Purpose | Usage |
|------|---------|-------|
| **setup_authentik.sh** | Main setup script - creates all Authentik configuration | `./scripts/setup_authentik.sh` |
| **verify_authentik.sh** | Verification script - checks if setup was successful | `./scripts/verify_authentik.sh` |

### 📚 Documentation

| File | Purpose | Audience |
|------|---------|----------|
| **QUICK_START.md** | Quick reference guide (TL;DR) | Users who need to set up quickly |
| **README_AUTHENTIK_SETUP.md** | Comprehensive documentation | Detailed setup, troubleshooting, production |
| **SETUP_SUMMARY.md** | Overview of what gets created | Understanding the architecture |
| **INDEX.md** | This file - navigation guide | Finding the right documentation |

## Quick Start

```bash
# 1. Ensure LLARS is running
./start_llars.sh

# 2. Wait for Authentik to be ready
sleep 30

# 3. Run setup
./scripts/setup_authentik.sh

# 4. Verify setup
./scripts/verify_authentik.sh

# 5. Test login
open http://localhost:55080/login
# Login: admin / admin123
```

## File Details

### setup_authentik.sh (429 lines)

**Creates:**
- Authentication flow: `llars-api-authentication`
- OAuth2 providers: `llars-backend-provider`, `llars-frontend-provider`
- Applications: `LLARS Backend`, `LLARS Frontend`
- Test users: `admin`, `akadmin`, `researcher`, `viewer`

**Features:**
- Idempotent (safe to run multiple times)
- Error handling with colored output
- Verification step at the end
- Production security warnings

**Example Output:**
```
========================================
1. Creating Authentication Flow
========================================
[1/4] Creating authentication flow...
  ✓ Created new flow: llars-api-authentication
[2/4] Creating identification stage...
  ✓ Created identification stage
...
✓ Authentication flow setup complete!
```

### verify_authentik.sh (143 lines)

**Checks:**
- Authentication flow exists (1 expected)
- Flow stages exist (3 expected)
- OAuth2 providers exist (2 expected)
- Applications exist (2 expected)
- Test users exist (4 expected)
- Admin users exist (2 expected)
- Provider configuration (client IDs, types)
- Service URLs accessible

**Example Output:**
```
Verifying Authentik Setup...

✓ Authentik server is running

Configuration:
✓ Authentication flows: 1/1
✓ Flow stages: 3/3
✓ OAuth2 providers: 2/2
✓ Applications: 2/2
✓ Test users: 4/4
✓ Admin users: 2/2

Provider Details:
✓ Backend provider client_id: llars-backend
✓ Backend provider type: confidential
✓ Frontend provider client_id: llars-frontend
✓ Frontend provider type: public
```

### QUICK_START.md (104 lines)

**Contents:**
- TL;DR section (one-line setup)
- What you get (users, providers, URLs)
- Quick verification commands
- Basic troubleshooting

**When to use:**
- First-time setup
- Quick reference during deployment
- Reminder of test credentials

### README_AUTHENTIK_SETUP.md (371 lines)

**Contents:**
- Prerequisites and installation
- What gets created (detailed)
- Verification procedures
- Common issues and solutions
- Production deployment checklist
- Integration with LLARS backend/frontend
- Related documentation links

**When to use:**
- Understanding the authentication flow
- Troubleshooting complex issues
- Production deployment planning
- Deep dive into configuration

### SETUP_SUMMARY.md (337 lines)

**Contents:**
- Architecture overview
- Component relationships
- Integration patterns
- Maintenance procedures
- Success metrics
- Design principles

**When to use:**
- Understanding the system architecture
- Planning modifications
- Training new developers
- Documentation updates

## Common Workflows

### Initial Setup

```bash
# First time setting up LLARS
./start_llars.sh
sleep 30
./scripts/setup_authentik.sh
./scripts/verify_authentik.sh
```

### Troubleshooting Failed Setup

```bash
# Check what's missing
./scripts/verify_authentik.sh

# Re-run setup (safe - it's idempotent)
./scripts/setup_authentik.sh

# Check logs
docker compose logs authentik-server --tail=100
```

### Production Deployment

```bash
# 1. Edit setup script - change secrets
vim ./scripts/setup_authentik.sh
# Line ~95: Change client_secret
# Line ~102, 118: Change redirect_uris to production domain

# 2. Run setup on production
./scripts/setup_authentik.sh

# 3. Verify
./scripts/verify_authentik.sh

# 4. Delete test users (optional)
docker compose exec -T authentik-server ak shell -c "
from authentik.core.models import User
User.objects.filter(username__in=['researcher', 'viewer']).delete()
"

# 5. Change admin passwords
# (via Authentik UI or script)
```

### Reset and Start Fresh

```bash
# WARNING: Deletes all Authentik data!
docker compose down -v
docker compose up -d
sleep 60
./scripts/setup_authentik.sh
./scripts/verify_authentik.sh
```

## Architecture

### Authentication Flow

```
User Login Request
        │
        ▼
┌─────────────────────┐
│ Frontend (Vue.js)   │
│ /login              │
└──────────┬──────────┘
           │ POST /auth/authentik/login
           │ {username, password}
           ▼
┌─────────────────────┐
│ Backend (Flask)     │
│ authentik_login.py  │
└──────────┬──────────┘
           │ Flow Executor API
           ▼
┌─────────────────────┐
│ Authentik           │
│ llars-api-auth flow │
└──────────┬──────────┘
           │ 1. Identification
           │ 2. Password
           │ 3. User Login
           ▼
┌─────────────────────┐
│ OAuth2 Token        │
│ (RS256 JWT)         │
└──────────┬──────────┘
           │ Return to Frontend
           ▼
┌─────────────────────┐
│ sessionStorage      │
│ - auth_token        │
│ - auth_llars_roles  │
└─────────────────────┘
```

### Component Relationships

```
Applications
    │
    ├── LLARS Backend ──────────┐
    │                           │
    │                           ▼
    └── LLARS Frontend      OAuth2 Providers
                                │
                                ├── llars-backend-provider (confidential)
                                │   ├── Client ID: llars-backend
                                │   ├── Client Secret: ***
                                │   ├── Type: Confidential
                                │   └── Algorithm: RS256
                                │
                                └── llars-frontend-provider (public)
                                    ├── Client ID: llars-frontend
                                    ├── Type: Public
                                    └── Algorithm: RS256

Authentication Flow
    │
    └── llars-api-authentication
        ├── Stage 1: Identification (username/email)
        ├── Stage 2: Password (validate)
        └── Stage 3: User Login (create session)

Users
    │
    ├── admin (Admin)
    ├── akadmin (Admin)
    ├── researcher (User)
    └── viewer (User)
```

## Documentation Map

**Need to...**

| Goal | Start Here |
|------|------------|
| Set up Authentik quickly | QUICK_START.md |
| Understand what gets created | SETUP_SUMMARY.md |
| Troubleshoot issues | README_AUTHENTIK_SETUP.md → "Common Issues" |
| Deploy to production | README_AUTHENTIK_SETUP.md → "Production Considerations" |
| Verify setup worked | Run `verify_authentik.sh` |
| Understand architecture | SETUP_SUMMARY.md → "Integration with LLARS" |
| Modify configuration | README_AUTHENTIK_SETUP.md → "Re-running After Changes" |
| Find test credentials | QUICK_START.md → "What You Get" |
| Check service URLs | QUICK_START.md → "URLs" |
| Debug login failures | README_AUTHENTIK_SETUP.md → "Troubleshooting" |

## Integration Points

### Backend Files

| File | Purpose |
|------|---------|
| `/app/auth/authentik_login.py` | Flow Executor API implementation |
| `/app/auth/oidc_validator.py` | JWT token validation (JWKS) |
| `/app/decorators/permission_decorator.py` | Route protection |
| `/app/routes/AuthRoutes.py` | `/auth/authentik/*` endpoints |

### Frontend Files

| File | Purpose |
|------|---------|
| `/llars-frontend/src/composables/useAuth.js` | Auth composable (login/logout) |
| `/llars-frontend/src/components/Login.vue` | Login form |
| `/llars-frontend/src/main.js` | Axios interceptors (token, 401 handling) |

### Configuration Files

| File | Purpose |
|------|---------|
| `/.env` | Authentik environment variables |
| `/docker-compose.yml` | Authentik service definition |
| `/CLAUDE.md` | Main documentation (Authentik section) |

## Environment Variables

Key variables in `.env`:

```bash
# Authentik URLs
AUTHENTIK_HOST=http://authentik-server:9000
AUTHENTIK_TOKEN=your-authentik-api-token

# OAuth2 Configuration
OIDC_CLIENT_ID=llars-backend
OIDC_CLIENT_SECRET=llars-backend-secret-change-in-production
OIDC_ISSUER=http://localhost:55095/application/o/llars-backend-provider/

# Ports
AUTHENTIK_EXTERNAL_PORT=55095
NGINX_EXTERNAL_PORT=55080
```

## Testing Checklist

After running setup script:

- [ ] Script completed without errors
- [ ] `verify_authentik.sh` shows all green checks
- [ ] Can access Authentik UI (http://localhost:55095)
- [ ] Can login to Authentik with `akadmin/admin123`
- [ ] Providers visible in UI (Applications → Providers)
- [ ] Applications visible in UI (Applications → Applications)
- [ ] Flow visible in UI (Flows & Stages → Flows)
- [ ] Can access LLARS frontend (http://localhost:55080)
- [ ] Can login to LLARS with `admin/admin123`
- [ ] Dashboard loads after login
- [ ] Token stored in sessionStorage (`auth_token`)
- [ ] Roles stored in sessionStorage (`auth_llars_roles`)
- [ ] API calls include Bearer token (check Network tab)
- [ ] 401 redirects to login (logout and try accessing protected page)

## Production Checklist

Before deploying to production:

- [ ] Changed `client_secret` in script (use `openssl rand -hex 32`)
- [ ] Changed all test user passwords
- [ ] Updated redirect URIs to production domain
- [ ] Enabled HTTPS (`AUTHENTIK_COOKIE_SECURE=true`)
- [ ] Removed unnecessary test users (`researcher`, `viewer`)
- [ ] Configured proper admin email addresses
- [ ] Set up backup for Authentik PostgreSQL database
- [ ] Set up backup for LLARS MariaDB database
- [ ] Tested login flow on production domain
- [ ] Tested logout flow
- [ ] Tested token expiration/refresh
- [ ] Verified JWT signature validation works
- [ ] Checked logs for errors/warnings
- [ ] Documented production credentials securely

## Support

**Issues during setup?**

1. Check `verify_authentik.sh` output
2. Review `README_AUTHENTIK_SETUP.md` troubleshooting section
3. Check Authentik logs: `docker compose logs authentik-server`
4. Check backend logs: `docker compose logs backend-flask-service`

**Need help understanding?**

- Architecture: `SETUP_SUMMARY.md`
- Integration: `README_AUTHENTIK_SETUP.md` → "Integration with LLARS"
- Main docs: `/CLAUDE.md` → "Authentik-Integration"

---

**Last Updated:** 2025-11-27
**Version:** 1.0
**Maintainer:** Philipp Steigerwald
**Documentation Standard:** LLARS Project Guidelines
