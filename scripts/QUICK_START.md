# Authentik Setup - Quick Start

## TL;DR

```bash
# 1. Start LLARS
./start_llars.sh

# 2. Wait for Authentik to be ready (~30 seconds)
docker compose logs authentik-server | grep -i "running on"

# 3. Run setup script
./scripts/setup_authentik.sh

# 4. Test login
open http://localhost:55080/login
# Login: admin / admin123
```

## One-Line Setup

```bash
./start_llars.sh && sleep 30 && ./scripts/setup_authentik.sh
```

## What You Get

**Test Users:**
- `admin` / `admin123` (Admin)
- `akadmin` / `admin123` (Admin)
- `researcher` / `admin123` (Researcher)
- `viewer` / `admin123` (Viewer)

**OAuth2 Providers:**
- Backend: `llars-backend` / `llars-backend-secret-change-in-production`
- Frontend: `llars-frontend` (public, no secret)

**URLs:**
- Frontend: http://localhost:55080
- Backend API: http://localhost:55080/api
- Authentik UI: http://localhost:55095

## Quick Verification

```bash
# Check if everything was created
docker compose exec -T authentik-server ak shell -c "
from authentik.flows.models import Flow
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.core.models import Application, User

print(f'Flows: {Flow.objects.filter(slug=\"llars-api-authentication\").count()}')
print(f'Providers: {OAuth2Provider.objects.filter(name__icontains=\"llars\").count()}')
print(f'Apps: {Application.objects.filter(slug__icontains=\"llars\").count()}')
print(f'Users: {User.objects.filter(username__in=[\"admin\", \"akadmin\"]).count()}')
"
```

Expected output:
```
Flows: 1
Providers: 2
Apps: 2
Users: 2
```

## Troubleshooting

**Script fails?**
```bash
# Check Authentik is running
docker compose ps | grep authentik

# Check logs
docker compose logs authentik-server --tail=50

# Wait longer and retry
sleep 60 && ./scripts/setup_authentik.sh
```

**Can't login?**
```bash
# Reset admin password
docker compose exec -T authentik-server ak shell -c "
from authentik.core.models import User
u = User.objects.get(username='admin')
u.set_password('admin123')
u.save()
print('Password reset')
"
```

## Production

**Before production deployment:**

1. Change `client_secret` in script (line ~95)
2. Change test user passwords
3. Update redirect URIs to production domain
4. Enable HTTPS (`AUTHENTIK_COOKIE_SECURE=true`)

## Full Documentation

See `README_AUTHENTIK_SETUP.md` for complete documentation.
