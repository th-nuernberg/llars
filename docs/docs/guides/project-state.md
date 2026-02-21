# LLARS PROJECT_STATE Guide

## Überblick

`PROJECT_STATE` steuert, ob LLARS im **Development**- oder **Production**-Modus läuft. Alle Services (Flask, Vue/Vite, Authentik, Yjs, nginx) erhalten diese Variable.

## Konfiguration

In `.env` setzen:

```bash
# Development (Standard)
PROJECT_STATE=development

# Production
PROJECT_STATE=production
```

## Auswirkungen nach Modus

### Development (`development`)
- Hot-Reload für Frontend (Vite) und Backend
- Einstieg über nginx (Standard: `http://localhost:55080`)
- MkDocs via nginx: `/mkdocs/` (Dev)
- Optional direkter Zugriff auf Authentik/DB/MkDocs über die externen Ports (Defaults: 55095/55306/55800)
- Ausführliches Logging
- Erweiterte Demo-Daten (20-30 Samples pro Szenario) werden automatisch gesät
- Debug-Ports nur, wenn benötigt (Standard-Compose hält die Exposes minimal)

### Production (`production`)
- Optimierte Builds, kein Hot-Reload
- Weniger Logging
- Zugriff ausschließlich über nginx (80/443)
- Authentik wird hinter nginx erwartet (HTTPS empfohlen)
- MkDocs via nginx: `/mkdocs/` (Prod)

## Nutzung

### Start (Standard: Development)
```bash
./start_llars.sh
# oder explizit
PROJECT_STATE=development ./start_llars.sh
```

### Auf Production umschalten
1. `.env` anpassen:
   ```bash
   PROJECT_STATE=production
   ```
2. Neu starten:
   ```bash
   ./start_llars.sh prod
   ```

## Überprüfen

```bash
docker compose ps
```

- Development: nginx (55080) und Authentik (55095) sind erreichbar; Frontend/Backend laufen intern hinter nginx.
- Production: nur nginx-Port nach außen offen; alle internen Services laufen hinter nginx (80/443).

## Troubleshooting

- **Falscher Modus aktiv?**  
  `.env` prüfen (`grep PROJECT_STATE .env`) und neu starten.

- **Authentik nur per HTTPS erreichbar?**  
  In Production nur über nginx vorsehen; für lokale Tests `development` nutzen.

- **Frontend ohne Hot-Reload?**  
  Sicherstellen, dass `PROJECT_STATE=development` aktiv ist und der Stack neu gestartet wurde (`./start_llars.sh`).

## Best Practices

- Entwicklung: `PROJECT_STATE=development`, Debug-Ports nutzen.
- Produktion: `PROJECT_STATE=production`, HTTPS vor nginx, Standard-Passwörter ändern.
- Nach Änderung des Modus immer `./start_llars.sh` neu ausführen.

- [Authentik Setup](authentik-setup.md) - OIDC-Login mit Authentik
- [Authentik Dokumentation](https://docs.goauthentik.io/)
- [Docker Compose Dokumentation](https://docs.docker.com/compose/)
