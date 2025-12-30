# LLARS Release Checkliste

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Zweck

Diese Checkliste dient zur Vorbereitung und Durchführung eines LLARS-Releases.

**Geschätzte Dauer:** 2-4 Stunden

---

## 1. Pre-Release Vorbereitung

### Code Quality

- [ ] Alle Unit-Tests bestanden (`pytest tests/unit/`)
- [ ] Alle Integration-Tests bestanden (`pytest tests/integration/`)
- [ ] Code Coverage ≥ 80% (`pytest --cov`)
- [ ] Keine Linting-Fehler (`flake8 app/`)
- [ ] Keine TypeScript-Fehler (`npm run type-check`)
- [ ] Keine ESLint-Fehler (`npm run lint`)

### Security

- [ ] Keine bekannten Sicherheitslücken (`pip-audit`, `npm audit`)
- [ ] Secrets in `.env`, nicht im Code
- [ ] CORS korrekt konfiguriert
- [ ] Rate Limiting aktiv
- [ ] HTTPS erzwungen (Produktion)

### Documentation

- [ ] CHANGELOG.md aktualisiert
- [ ] Version in `package.json` aktualisiert
- [ ] Version in `app/__init__.py` aktualisiert
- [ ] API-Dokumentation aktuell
- [ ] CLAUDE.md aktuell

---

## 2. Datenbank

### Migrationen

- [ ] Alle Migrationen erstellt
- [ ] Migrationen auf Staging getestet
- [ ] Rollback-Skripte vorhanden
- [ ] Backup-Strategie dokumentiert

### Datenbankstruktur

```bash
# Schema-Änderungen prüfen
docker exec llars_db_service mariadb -u dev_user -pdev_password_change_me \
  database_llars -e "SHOW TABLES;"

# Neue Tabellen dokumentieren
docker exec llars_db_service mariadb -u dev_user -pdev_password_change_me \
  database_llars -e "DESCRIBE new_table_name;"
```

---

## 3. Staging-Deployment

### Deployment

- [ ] Staging-Umgebung aktualisiert
- [ ] Alle Container healthy
- [ ] Logs keine kritischen Fehler
- [ ] Migrations erfolgreich

### Smoke Test (Staging)

- [ ] Login funktioniert
- [ ] Home Dashboard lädt
- [ ] Chat antwortet
- [ ] RAG-Upload funktioniert
- [ ] PDF-Kompilierung funktioniert
- [ ] Admin-Bereich zugänglich

---

## 4. E2E Tests

### Kritische Pfade

- [ ] `npm run test:e2e -- --project=chromium`
- [ ] Login/Logout Flow
- [ ] Chatbot erstellen (Wizard)
- [ ] RAG Document hochladen
- [ ] LaTeX kompilieren
- [ ] Ranking speichern
- [ ] Admin: User erstellen

### Browser-Kompatibilität

- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari (macOS)
- [ ] Edge

---

## 5. Performance

### Load Tests

- [ ] API-Endpunkte unter Last getestet
- [ ] WebSocket-Verbindungen stabil
- [ ] Memory Leaks geprüft

### Benchmarks

| Metrik | Ziel | Aktuell |
|--------|------|---------|
| First Contentful Paint | < 1.5s | ___s |
| Time to Interactive | < 3s | ___s |
| API Response (p95) | < 500ms | ___ms |
| WebSocket Latency | < 100ms | ___ms |

---

## 6. Produktion Vorbereitung

### Konfiguration

- [ ] `.env.production` geprüft
- [ ] Secrets rotiert (wenn nötig)
- [ ] SSL-Zertifikate gültig
- [ ] DNS korrekt
- [ ] Backup-Job konfiguriert

### Abhängigkeiten

- [ ] Externe APIs erreichbar (LiteLLM, Authentik)
- [ ] Datenbank-Verbindung stabil
- [ ] Redis/Cache konfiguriert

---

## 7. Release Durchführung

### Deployment

```bash
# 1. Backup erstellen
docker exec llars_db_service mysqldump -u dev_user -pdev_password_change_me \
  database_llars > backup_pre_release_$(date +%Y%m%d_%H%M%S).sql

# 2. Images bauen
docker compose build

# 3. Services aktualisieren
docker compose up -d

# 4. Migrations ausführen (wenn nötig)
docker exec llars_flask_service flask db upgrade

# 5. Container-Status prüfen
docker ps
```

### Verifizierung

- [ ] Alle Container running
- [ ] Keine Fehler in Logs
- [ ] Health-Endpoints OK
- [ ] Smoke Test bestanden

---

## 8. Post-Release

### Monitoring

- [ ] Matomo Tracking funktioniert
- [ ] Error-Rate normal
- [ ] Response-Zeiten normal
- [ ] Memory/CPU normal

### Kommunikation

- [ ] Release Notes veröffentlicht
- [ ] Team benachrichtigt
- [ ] Known Issues dokumentiert

### Rollback-Plan

```bash
# Bei kritischen Fehlern:

# 1. Logs sichern
docker compose logs > crash_logs_$(date +%Y%m%d_%H%M%S).log

# 2. Auf vorherige Version zurück
git checkout <previous_release_tag>
docker compose build
docker compose up -d

# 3. DB Rollback (wenn nötig)
docker exec -i llars_db_service mariadb -u dev_user -pdev_password_change_me \
  database_llars < backup_pre_release_*.sql
```

---

## 9. Release-Typen

### Patch Release (x.x.X)

Bugfixes, keine Breaking Changes.

- [ ] Nur betroffene Tests
- [ ] Schneller Smoke Test
- [ ] Keine DB-Migrationen

### Minor Release (x.X.0)

Neue Features, backwards-kompatibel.

- [ ] Vollständige Test-Suite
- [ ] Staging-Testing (1-2 Tage)
- [ ] Dokumentation aktualisiert

### Major Release (X.0.0)

Breaking Changes möglich.

- [ ] Vollständige Test-Suite
- [ ] Extended Staging-Testing (1 Woche)
- [ ] Migration-Guide erstellt
- [ ] Deprecation Warnings entfernt

---

## 10. Signoff

| Rolle | Name | Datum | Signatur |
|-------|------|-------|----------|
| Developer | | | |
| QA | | | |
| DevOps | | | |
| Product Owner | | | |

---

## 11. Notizen

| Release | Datum | Notizen |
|---------|-------|---------|
| | | |

---

**Letzte Aktualisierung:** 30. Dezember 2025
