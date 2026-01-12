# Manual Deployment Skill

Dieses Skill beschreibt, wie LLARS manuell auf dem Produktionsserver deployed wird.

## Server-Informationen

| Eigenschaft | Wert |
|-------------|------|
| Hostname | `llars` (SSH-Config) oder `llars.informatik.fh-nuernberg.de` |
| IP | `141.75.150.128` (internes Netz) |
| SSH User | `master` |
| SSH Key | `~/.ssh/id_ed25519_llars` |
| LLARS Verzeichnis | `/var/llars` |
| Owner | `gitlab-runner:gitlab-runner` |
| Produktions-URL | https://llars.e-beratungsinstitut.de |

## SSH-Verbindung

```bash
# Via SSH-Config (empfohlen)
ssh llars

# Oder direkt
ssh -i ~/.ssh/id_ed25519_llars master@llars.informatik.fh-nuernberg.de
```

## Deployment-Schritte

### 1. Aenderungen committen und pushen

```bash
# Alle Aenderungen stagen
git add -A

# Commit mit sinnvoller Message (OHNE KI-Hinweise!)
git commit -m "feat(scope): beschreibung der aenderung"

# Nach GitLab pushen
git push origin main
```

**Commit-Message-Format:**
- `feat(scope):` - Neue Features
- `fix(scope):` - Bugfixes
- `refactor(scope):` - Code-Refactoring
- `docs(scope):` - Dokumentation
- `chore(scope):` - Wartung/Tooling

### 2. Auf Server verbinden und Code pullen

```bash
# Da /var/llars dem gitlab-runner gehoert, brauchen wir sudo
ssh llars 'sudo -u gitlab-runner bash -c "cd /var/llars && git pull origin main"'
```

Falls interaktiv (Passwort-Eingabe noetig):
```bash
ssh -t llars 'sudo -u gitlab-runner bash -c "cd /var/llars && git pull origin main"'
```

### 3. LLARS neu starten

**Option A: Mit start_llars.sh (empfohlen)**
```bash
ssh llars 'sudo bash -c "cd /var/llars && ./start_llars.sh"'
```

**Option B: Manuell mit docker compose**
```bash
ssh llars 'cd /var/llars && docker compose down && docker compose up -d --build'
```

### 4. Verifizieren

```bash
# Container-Status pruefen
ssh llars 'cd /var/llars && docker compose ps'

# Logs pruefen (bei Fehlern)
ssh llars 'cd /var/llars && docker compose logs -f --tail=100'

# Smoke-Test
curl -s -o /dev/null -w "%{http_code}" https://llars.e-beratungsinstitut.de/
```

## Troubleshooting

### "No space left on device"

```bash
# Docker aufraeumen
ssh llars 'sudo docker system prune -af'

# Danach LLARS neu starten
ssh llars 'sudo bash -c "cd /var/llars && ./start_llars.sh"'
```

### Permission denied bei git pull

Das Verzeichnis `/var/llars` gehoert dem `gitlab-runner` User. Alle git-Befehle muessen mit `sudo -u gitlab-runner` ausgefuehrt werden:

```bash
ssh llars 'sudo -u gitlab-runner bash -c "cd /var/llars && git pull origin main"'
```

### Container unhealthy

```bash
# Logs des betroffenen Services pruefen
ssh llars 'cd /var/llars && docker compose logs <service-name> --tail=50'

# Alle Container stoppen und neu starten
ssh llars 'sudo bash -c "cd /var/llars && docker compose down && ./start_llars.sh"'
```

### Authentik-Probleme

```bash
# Authentik-Setup erneut ausfuehren
ssh llars 'sudo bash -c "cd /var/llars && python3 setup_authentik.py"'
```

## Services

| Service | Container | Port (intern) |
|---------|-----------|---------------|
| Frontend | llars_frontend_service | 80, 5173 |
| Backend | llars_flask_service | 8081 |
| Supervisor | llars_supervisor_service | - |
| YJS (Collab) | llars_yjs_service | 8082 |
| MariaDB | llars_db_service | 3306 |
| Redis | llars_redis | 6379 |
| Authentik Server | llars_authentik_server | 9000 |
| Authentik Worker | llars_authentik_worker | - |
| Authentik DB | llars_authentik_db | 5432 |
| Matomo | llars_matomo_service | 80 |
| MkDocs | llars_mkdocs_service | 8000 |
| Nginx | llars_nginx_service | 80, 443 |

## Wichtige Hinweise

1. **Force-Push auf main ist verboten** - Der Branch ist protected
2. **Backups vor grossen Aenderungen** - `docker exec llars_db_service mysqldump...`
3. **Bei Problemen: Logs zuerst pruefen** - `docker compose logs -f`
4. **Authentik-Konfiguration nie aendern** - Client-IDs, Flow-Slugs etc. sind fix
