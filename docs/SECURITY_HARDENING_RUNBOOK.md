# Security Hardening Runbook (Pentest 2026-06-10)

Dieses Runbook macht die Sicherheits-Härtung **reproduzierbar** — damit ein
`komplett neu hochziehen` keine Lücke wieder öffnet. Es unterscheidet:

- **Codifiziert (in Git)** → übersteht jeden Rebuild automatisch.
- **Manuell / pro Maschine** → muss bei Neuaufbau bewusst (erneut) ausgeführt werden.

---

## 1. Codifiziert (in Git — automatisch persistent)

| Fix | Ort |
|-----|-----|
| IDOR-Gates (LLM-Eval, available-users) | `app/routes/llm/llm_evaluation_routes.py`, `app/routes/scenarios/scenario_manager_api.py` |
| SSRF user-provider base_url (create/update + factory) | `app/services/user_llm_provider_service.py`, `app/services/llm/llm_client_factory.py` |
| Socket-Authz + Rate-Limit | `app/socketio_handlers/events_chat.py`, `events_chatbot.py`, `socket_rate_limit.py` |
| CSV-Formula-Injection-Schutz | `app/services/security/csv_safety.py`, `app/routes/api_v1/scenario_results_routes.py` |
| Stored-XSS (`safeExternalUrl`, sanitize style entfernt) | `llars-frontend/src/utils/url.js`, `utils/sanitize.js`, Conference-Komponenten + `app/services/conference_service.py` |
| Dual-Key-Crypto (zero-downtime Rotation) | `app/services/llm/secret_encryption.py` |
| DB-Port nur Loopback | `docker-compose.yml` (`DB_BIND_HOST:-127.0.0.1`) |
| Remote-Root bei frischer DB verhindern | `docker-compose.yml` (`MARIADB_ROOT_HOST=localhost`) |
| `.env` 0600 bei jedem Start | `start_llars.sh` |
| Session-Cookies HTTPONLY/SAMESITE/SECURE | `app/main.py` |

---

## 2. Manuell / pro Maschine (bei Neuaufbau erneut ausführen)

### 2a. Secret-Key-Rotation (C1/C2) — zero-downtime
> Pflicht: in Prod dürfen `JWT_SECRET_KEY` / `LLM_PROVIDER_ENCRYPTION_KEY` NICHT
> der Dev-Default `dev-secret-key-change-in-production` sein.

```bash
# 1. Neue Keys erzeugen
NEW_FERNET=$(openssl rand -base64 36)
NEW_JWT=$(openssl rand -base64 48)

# 2. In /var/llars/.env setzen (neu = primär, alt = Fallback während Migration):
#    LLM_PROVIDER_ENCRYPTION_KEY=$NEW_FERNET
#    LLM_PROVIDER_ENCRYPTION_KEY_FALLBACK=dev-secret-key-change-in-production
#    JWT_SECRET_KEY=$NEW_JWT
# 3. App-Container recreaten (lädt neue Env) — blue/green oder up -d
# 4. Re-Encrypt (liest alt via Fallback, schreibt neu):
docker exec llars_flask_<aktive_farbe> python /app/scripts/reencrypt_secrets.py --dry-run
docker exec llars_flask_<aktive_farbe> python /app/scripts/reencrypt_secrets.py
# 5. *_FALLBACK aus .env entfernen, App erneut recreaten.
# 6. Die bisher gespeicherten Provider-Keys galten als kompromittiert → upstream rotieren.
```
> **Danach** (separater Commit, NICHT vorher): Secret-Guard härten, sodass ein
> explizit gesetzter Dev-Default in Production den Boot verweigert
> (`secret_encryption._get_encryption_key`). Vor der Rotation deployed = Prod
> bootet nicht.

### 2b. Remote-Root aus EXISTIERENDER DB entfernen (C4)
> `MARIADB_ROOT_HOST=localhost` wirkt nur bei frischer DB. Bestehendes Volume:
```bash
docker exec llars_db_service sh -c \
  'mariadb -u root -p$MYSQL_ROOT_PASSWORD -e "DROP USER IF EXISTS '\''root'\''@'\''%'\''; FLUSH PRIVILEGES;"'
```

### 2c. DB-Port-Binding aktivieren (C4)
> Compose ist gesetzt, aber Blue-Green recreatet die DB nicht. Einmalig:
```bash
cd /var/llars && docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d db-maria-service
# kurzer DB-Blip (Sekunden), Flask reconnectet
```

### 2d. SSH-Härtung (Host, überlebt Docker-Rebuilds; bei OS-Neuinstall erneut)
```bash
# /etc/ssh/sshd_config.d/99-llars-hardening.conf:
#   PasswordAuthentication no
#   KbdInteractiveAuthentication no
#   PermitRootLogin no
sshd -t && systemctl reload ssh
```

### 2e. Offen (geplant, noch nicht umgesetzt)
- **C3 docker-socket-proxy** (read-only Docker-API statt direktem Socket-Mount).
- **C5 Brute-Force-Schutz** ohne IP: CAPTCHA-Stage + Per-Account-Reputation + MFA
  (echte Client-IP erreicht Authentik nicht; IP-Sperre = Kollektiv-Aussperrung).
- **M3** Container CPU/RAM-Limits.
- nginx `set_real_ip_from` (FH-Gateway) für funktionierendes per-Client Rate-Limit (M4).
```
