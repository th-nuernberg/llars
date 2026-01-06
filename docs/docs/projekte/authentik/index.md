# Authentik Integration

!!! success "✅ Status: Abgeschlossen"
    Die Authentik-Integration ist **vollständig implementiert**.
    Ersetzt das vorherige Keycloak-System.

## Übersicht

LLARS verwendet Authentik als Identity Provider mit OAuth2/OIDC für die Benutzerauthentifizierung.

## Dokumentation

| Dokument | Beschreibung | Status |
|----------|--------------|--------|
| [Overview](overview.md) | Schnellübersicht der Konfiguration | ✅ Aktuell |
| [Migration](migration.md) | Dokumentation der Keycloak→Authentik Migration | ✅ Abgeschlossen |
| [Testing Plan](testing-plan.md) | Test- und Verifikationsplan | ✅ Abgeschlossen |

## Features

- RS256 JWT-Tokens (asymmetrische Kryptographie)
- Flow Executor API für headless Authentication
- JWKS-basierte Token-Validierung
- Automatisches Setup via `authentik-init` Container (idempotent)

## Quick Commands

```bash
# Automatisches Setup (Standard)
./start_llars.sh

# Manueller Fallback (falls Auto-Setup fehlschlägt)
./scripts/setup_authentik.sh

# Verifizierung
./scripts/verify_authentik.sh
```

## Test-Benutzer

| User | Passwort | Rolle |
|------|----------|-------|
| admin | admin123 | admin |
| researcher | admin123 | researcher |
| evaluator | admin123 | evaluator |
