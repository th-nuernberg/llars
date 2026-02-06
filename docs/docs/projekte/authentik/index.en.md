# Authentik Integration

!!! success "✅ Status: Complete"
    The Authentik integration is **fully implemented**.
    It replaces the previous Keycloak system.

## Overview

LLARS uses Authentik as its identity provider with OAuth2/OIDC for user authentication.

## Documentation

| Document | Description | Status |
|----------|-------------|--------|
| [Overview](overview.md) | Quick configuration overview | ✅ Current |
| [Migration](migration.md) | Documentation of the Keycloak -> Authentik migration | ✅ Complete |
| [Testing Plan](testing-plan.md) | Test and verification plan | ✅ Complete |

## Features

- RS256 JWT tokens (asymmetric cryptography)
- Flow Executor API for headless authentication
- JWKS-based token validation
- Automatic setup via `authentik-init` container (idempotent)

## Quick commands

```bash
# Automatic setup (default)
./start_llars.sh

# Manual fallback (if auto-setup fails)
./scripts/setup_authentik.sh

# Verification
./scripts/verify_authentik.sh
```

## Test users

| User | Password | Role |
|------|----------|------|
| admin | admin123 | admin |
| akadmin | admin123 | admin |
| researcher | admin123 | researcher |
| evaluator | admin123 | evaluator |
