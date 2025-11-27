# Authentik Manual Setup Script

## Overview

This script manually configures Authentik for LLARS when the automatic initialization fails. It creates all necessary OAuth2 providers, applications, authentication flows, and test users.

## Prerequisites

1. **Docker Compose running**: Authentik container must be running
   ```bash
   docker compose up -d
   ```

2. **Authentik accessible**: Wait ~30 seconds for Authentik to fully start
   ```bash
   # Check if ready
   docker compose logs authentik-server | grep -i "running on"
   ```

## Usage

### Basic Usage

```bash
cd /Users/philippsteigerwald/PycharmProjects/llars
./scripts/setup_authentik.sh
```

### Troubleshooting Run

If the script fails, you can run it with verbose output:

```bash
bash -x ./scripts/setup_authentik.sh
```

## What Gets Created

### 1. Authentication Flow

**Name:** `llars-api-authentication`

**Stages:**
1. **Identification** (`llars-api-identification`)
   - Accepts username or email
   - No external sources

2. **Password** (`llars-api-password`)
   - Uses Authentik's built-in authentication backend
   - Validates password against user database

3. **User Login** (`llars-api-user-login`)
   - Creates session after successful authentication
   - Default session duration

**Purpose:** This flow is used by the Flask backend when users login via the Flow Executor API (`/api/v3/flows/executor/llars-api-authentication/`).

### 2. OAuth2 Providers

#### Backend Provider (Confidential)

```yaml
Name: llars-backend-provider
Client ID: llars-backend
Client Secret: llars-backend-secret-change-in-production
Client Type: Confidential
Signing Algorithm: RS256
Redirect URIs:
  - http://localhost:55080/auth/callback
  - http://localhost:8081/auth/callback
Scopes: All default OAuth2 scopes (openid, profile, email, etc.)
```

**Purpose:** Used for backend API authentication. The Flask app exchanges authorization codes for tokens.

#### Frontend Provider (Public)

```yaml
Name: llars-frontend-provider
Client ID: llars-frontend
Client Type: Public (no client secret)
Signing Algorithm: RS256
Redirect URIs:
  - http://localhost:55080/
  - http://localhost:55080/login
Scopes: All default OAuth2 scopes
```

**Purpose:** Could be used for frontend-initiated OAuth flows (currently unused, as LLARS uses Flow Executor API).

### 3. Applications

#### LLARS Backend

```yaml
Slug: llars-backend
Name: LLARS Backend
Provider: llars-backend-provider
```

#### LLARS Frontend

```yaml
Slug: llars-frontend
Name: LLARS Frontend
Provider: llars-frontend-provider
```

**Purpose:** Applications link providers to the Authentik UI and enable access control.

### 4. Test Users

| Username   | Password   | Email                 | Role       |
|------------|------------|-----------------------|------------|
| admin      | admin123   | admin@localhost       | Admin      |
| akadmin    | admin123   | akadmin@localhost     | Admin      |
| researcher | admin123   | researcher@localhost  | User       |
| viewer     | admin123   | viewer@localhost      | User       |

**Admin users** are added to the `authentik Admins` group, giving them superuser access to the Authentik UI.

## Script Features

### Idempotent Design

The script is safe to run multiple times:
- Uses `get_or_create()` or `update_or_create()` for all objects
- Shows `✓ Created` for new objects
- Shows `ℹ Already exists` or `ℹ Updated` for existing objects

### Error Handling

- Exits immediately on error (`set -e`)
- Checks if Docker is installed
- Checks if Authentik container is running
- Validates required objects exist (certificates, flows)

### Colored Output

- **Blue [INFO]**: Informational messages
- **Green [SUCCESS]**: Successful operations
- **Yellow [WARNING]**: Important notices
- **Red [ERROR]**: Errors

## Verification

After running the script, verify the setup:

### 1. Check Authentik UI

```bash
# Access Authentik
open http://localhost:55095

# Login with
Username: akadmin
Password: admin123

# Navigate to:
Applications → Providers → Should show llars-backend-provider and llars-frontend-provider
Applications → Applications → Should show LLARS Backend and LLARS Frontend
Flows & Stages → Flows → Should show llars-api-authentication
```

### 2. Test LLARS Login

```bash
# Access LLARS
open http://localhost:55080/login

# Try logging in with
Username: admin
Password: admin123

# Should successfully redirect to dashboard
```

### 3. Manual Verification Commands

```bash
# Check authentication flow exists
docker compose exec -T authentik-server ak shell -c "
from authentik.flows.models import Flow
print(Flow.objects.filter(slug='llars-api-authentication').exists())
"

# Check providers exist
docker compose exec -T authentik-server ak shell -c "
from authentik.providers.oauth2.models import OAuth2Provider
print(OAuth2Provider.objects.filter(name__icontains='llars').count())
"

# Check test users exist
docker compose exec -T authentik-server ak shell -c "
from authentik.core.models import User
users = ['admin', 'akadmin', 'researcher', 'viewer']
print(User.objects.filter(username__in=users).count())
"
```

## Common Issues

### Issue: "Authentik server is not running"

**Solution:**
```bash
# Start Authentik
docker compose up -d authentik-server authentik-worker

# Wait for startup (check logs)
docker compose logs -f authentik-server | grep -i "running on"
```

### Issue: "No self-signed certificate found"

**Solution:**
```bash
# Check if certificate exists
docker compose exec -T authentik-server ak shell -c "
from authentik.crypto.models import CertificateKeyPair
print(list(CertificateKeyPair.objects.values_list('name', flat=True)))
"

# If none exist, Authentik didn't initialize properly
# Try recreating Authentik containers:
docker compose down
docker compose up -d authentik-server authentik-worker
```

### Issue: "No authorization flow found"

**Solution:**
```bash
# Check available flows
docker compose exec -T authentik-server ak shell -c "
from authentik.flows.models import Flow
print(list(Flow.objects.values_list('slug', flat=True)))
"

# If default flows are missing, run Authentik migrations:
docker compose exec authentik-server ak migrate
```

### Issue: Login fails with "Invalid credentials"

**Debugging:**
```bash
# Verify user exists and password is set
docker compose exec -T authentik-server ak shell -c "
from authentik.core.models import User
user = User.objects.get(username='admin')
print(f'User exists: {user.username}')
print(f'User active: {user.is_active}')
print(f'Has usable password: {user.has_usable_password()}')
"

# Reset password manually
docker compose exec -T authentik-server ak shell -c "
from authentik.core.models import User
user = User.objects.get(username='admin')
user.set_password('admin123')
user.save()
print('Password reset successfully')
"
```

## Production Considerations

Before deploying to production, you MUST:

### 1. Change Secrets

```bash
# Update in script before running:
client_secret='llars-backend-secret-change-in-production'
# → Use a strong random secret (e.g., openssl rand -hex 32)
```

### 2. Change User Passwords

```bash
# Don't use 'admin123' in production!
# Change via Authentik UI or script
```

### 3. Update Redirect URIs

```bash
# Replace localhost with production domain:
redirect_uris='https://llars.your-domain.de/auth/callback'
```

### 4. Configure HTTPS

```bash
# Ensure Authentik is behind HTTPS proxy
# Update AUTHENTIK_COOKIE_SECURE=true in .env
```

## Integration with LLARS

After running this script, the LLARS backend will be able to:

1. **Authenticate users** via Flow Executor API:
   ```python
   # app/auth/authentik_login.py
   POST /api/v3/flows/executor/llars-api-authentication/
   ```

2. **Validate JWT tokens** from Authentik:
   ```python
   # app/auth/oidc_validator.py
   validate_token(token)  # Uses JWKS from Authentik
   ```

3. **Exchange authorization codes** for tokens:
   ```python
   # OAuth2 flow (if needed in future)
   POST /application/o/token/
   ```

## Re-running After Changes

If you modify the script and want to re-run:

```bash
# Safe to run - uses update_or_create()
./scripts/setup_authentik.sh

# To completely reset Authentik (DELETES ALL DATA):
docker compose down -v  # WARNING: Deletes volumes!
docker compose up -d
./scripts/setup_authentik.sh
```

## Script Location

```
/Users/philippsteigerwald/PycharmProjects/llars/
└── scripts/
    ├── setup_authentik.sh          # Main setup script
    └── README_AUTHENTIK_SETUP.md   # This documentation
```

## Related Documentation

- **CLAUDE.md**: Main LLARS documentation (section: Authentik-Integration)
- **docs/AUTHENTIK_TESTING_PLAN.md**: Testing procedures
- **app/auth/authentik_login.py**: Backend authentication implementation
- **llars-frontend/src/composables/useAuth.js**: Frontend auth composable

## Support

If you encounter issues:

1. Check Authentik logs:
   ```bash
   docker compose logs authentik-server | tail -100
   ```

2. Check backend logs:
   ```bash
   docker compose logs backend-flask-service | grep -i authentik
   ```

3. Verify .env configuration:
   ```bash
   grep AUTHENTIK .env
   ```

4. Run manual verification commands (see Verification section)
