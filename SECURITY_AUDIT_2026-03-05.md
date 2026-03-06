# LLARS Security Audit Report

**Datum:** 2026-03-05
**Scope:** Vollstaendige Codebase-Analyse (Backend, Frontend, Docker, CI/CD)
**Methode:** 6 parallele automatisierte Security-Agents, ~700 Endpoints analysiert

---

## Zusammenfassung

| Schweregrad | Anzahl | Status |
|-------------|--------|--------|
| CRITICAL    | 4      | Sofort beheben |
| HIGH        | 14     | Vor naechstem Deploy beheben |
| MEDIUM      | 20     | Zeitnah beheben |
| LOW         | 15     | Bei Gelegenheit |

---

## CRITICAL Findings

### C-1: Unauthentifizierter Transcript-Endpoint (RCE-Potenzial)
- **Datei:** `app/routes/messaging/ai_routes.py:103`
- **Route:** `POST /api/messaging/calls/transcript-chunk`
- **Problem:** KEIN Auth-Decorator. Jeder kann Transcript-Daten in beliebige Raeume injizieren und per Socket.IO an alle Teilnehmer broadcasten.
- **Auswirkung:** Daten-Injection, potentielles XSS, Spoofing von Call-Transkripten.
- **Fix:** `@system_api_key_required` hinzufuegen (Service-to-Service von LiveKit).

### C-2: Scenario-Export IDOR -- Volle Daten-Exfiltration
- **Datei:** `app/routes/scenarios/scenario_manager_api.py:2106`
- **Route:** `GET /api/scenarios/<scenario_id>/export`
- **Problem:** Nur `@authentik_required`, KEIN Membership-Check. Jeder authentifizierte User kann ALLE Evaluationsergebnisse (Rankings, Ratings, Votes, Usernamen) fuer JEDES Szenario exportieren.
- **Fix:** `require_scenario_membership(scenario_id, g.authentik_user)` hinzufuegen.

### C-3: LLMComparisonRoutes -- Custom Weak Auth (Timing-Attack)
- **Datei:** `app/routes/LLMComparisonRoutes.py:23-44`
- **Problem:** Eigene Ad-hoc-Auth liest `Authorization` Header direkt als API-Key. Kein `Bearer`-Prefix-Stripping, keine timing-safe Comparison (`hmac.compare_digest`), kein Permission-Check. Umgeht OIDC komplett.
- **Fix:** Auf `@authentik_required` oder `@api_key_or_token_required` migrieren.

### C-4: Docker-Socket read-write Mount in Flask-Container
- **Datei:** `docker-compose.yml:158`, `docker-compose.prod.yml:53`
- **Problem:** `/var/run/docker.sock:/var/run/docker.sock` -- read-write. Bei RCE im Flask-Container hat der Angreifer vollen Docker-Engine-Zugriff = Host-Root.
- **Fix:** Read-only Mount (`:ro`) oder Docker-Socket-Proxy (tecnativa/docker-socket-proxy) mit nur GET-Requests.

---

## HIGH Findings

### H-1: /my-permissions mit unverifizertem Token
- **Datei:** `app/routes/PermissionRoutes.py:97-124`
- **Route:** `GET /api/permissions/my-permissions`
- **Problem:** Kein Auth-Decorator. Nutzt `extract_username_without_validation()` mit `verify_signature: False`. Angreifer kann JWT mit beliebigem Username craftenund Permissions enumerieren.
- **Fix:** `@authentik_required` hinzufuegen.

### H-2: AI-Assist Test Routes nur durch FLASK_ENV geschuetzt
- **Datei:** `app/routes/ai_assist/test_routes.py:26-223`
- **Problem:** 4 Endpoints ohne Auth-Decorator. Nur Runtime-Check auf `FLASK_ENV`. Bei Fehlkonfiguration: unauthentifizierter LLM-Zugriff, Prompt-Template-Leak, API-Kosten.
- **Fix:** `@debug_route_protected` verwenden oder Routes nur in Development registrieren.

### H-3: Admin System Settings ohne Auth
- **Datei:** `app/routes/admin/system_settings_routes.py:40-71`
- **Routes:** `GET /api/system/ai-assistant`, `GET /api/system/communication-status`
- **Fix:** `@public_endpoint` oder `@authentik_required` hinzufuegen.

### H-4: Security-Test ignoriert 15 Route-Dateien
- **Datei:** `tests/security/test_route_security.py:29-46`
- **Problem:** `IGNORED_ROUTE_FILES` umfasst 15 Dateien inkl. LLMComparisonRoutes, PermissionRoutes, ai_assist/test_routes -- genau die mit echten Schwachstellen.
- **Fix:** Ignore-Liste leeren und alle Auth-Issues fixen.

### H-5: Token Issuer/Audience Verification deaktiviert
- **Datei:** `app/auth/oidc_validator.py:173-174`
- **Problem:** `verify_iss: False`, `verify_aud: False` in `jwt.decode()`. Manuelle Checks ersetzen Library-Checks mit Path-only-Vergleich.
- **Fix:** `verify_iss` und `verify_aud` in Production aktivieren.

### H-6: Scenario Stats IDOR
- **Datei:** `app/routes/scenarios/scenario_manager_api.py:1691`
- **Route:** `GET /api/scenarios/<scenario_id>/stats`
- **Problem:** Kein Membership-Check. Jeder authentifizierte User kann Evaluator-Namen, Fortschritt, Votes sehen.
- **Fix:** `require_scenario_membership()` hinzufuegen.

### H-7: Scenario Thread Detail IDOR
- **Datei:** `app/routes/scenarios/scenario_manager_api.py:1037`
- **Route:** `GET /api/scenarios/<scenario_id>/threads/<thread_id>`
- **Problem:** Kein Membership-Check.
- **Fix:** `require_scenario_membership()` hinzufuegen.

### H-8: XSS in AnonymizationDetail.vue
- **Datei:** `llars-frontend/src/components/AnonymizationPipeline/AnonymizationDetail.vue:916-939`
- **Problem:** `highlightEntities()` und `renderContentWithEntities()` bauen HTML aus Entity-Daten ohne DOMPurify. `entity.original_text`/`entity.replacement_text` direkt in HTML interpoliert.
- **Fix:** `DOMPurify.sanitize()` vor v-html-Rendering.

### H-9: XSS in KatexFormula.vue -- Fallback rendert Raw-Input
- **Datei:** `llars-frontend/src/components/common/KatexFormula.vue:29`
- **Problem:** Bei KaTeX-Parse-Fehler wird `props.formula` direkt in `v-html` zurueckgegeben. `<img src=x onerror=alert(1)>` wird ausgefuehrt.
- **Fix:** `escapeHtml(props.formula)` im Catch-Block.

### H-10: subprocess.run OHNE Timeout (LaTeX Compile)
- **Datei:** `app/services/latex_compile_service.py:242-248`
- **Problem:** Kein `timeout` Parameter. Malicious LaTeX (`\loop`) haengt den Worker-Thread permanent.
- **Fix:** `timeout=120` hinzufuegen.

### H-11: Massive Rate-Limit Exemptions
- **Datei:** `app/main.py:163-203`
- **Problem:** `/api/scenarios/*`, `/api/evaluation/*`, `/api/generation/*`, `/api/import/*`, `/api/judge/*` etc. sind ALLE von Rate-Limiting ausgenommen.
- **Fix:** Exemptions reduzieren, mindestens grosszuegige Limits setzen.

### H-12: Kein Production-Guard fuer AUTHENTIK_BACKEND_CLIENT_SECRET
- **Datei:** `app/routes/authentik_routes.py:147`
- **Problem:** Fallback auf `llars-backend-secret-change-in-production`. Im Gegensatz zu `FLASK_SECRET_KEY` und `SYSTEM_ADMIN_API_KEY` gibt es KEINEN Startup-Guard.
- **Fix:** Production-Guard in `main.py` analog zu Zeile 213-224.

### H-13: Default Encryption Key fuer gespeicherte API-Keys
- **Dateien:** `app/services/zotero/encryption.py:33`, `app/services/llm/secret_encryption.py:28`
- **Problem:** Fallback auf `dev-secret-key-change-in-production` fuer Fernet-Encryption. Kein Startup-Guard. Bei fehlendem `JWT_SECRET_KEY` sind alle verschluesselten API-Keys in der DB mit bekanntem Key entschluesselbar.
- **Fix:** Startup-Guard fuer `JWT_SECRET_KEY` hinzufuegen.

### H-14: Authentik Trusted Proxy CIDR = 0.0.0.0/0
- **Dateien:** `docker-compose.yml:382`, `docker-compose.prod.yml:216`
- **Problem:** Authentik vertraut JEDER IP als Proxy. X-Forwarded-For Header koennen gefaelscht werden.
- **Fix:** Auf Docker-Netzwerk-Subnet beschraenken (z.B. `172.16.0.0/12`).

---

## MEDIUM Findings

### M-1: Kein nginx Rate-Limiting in Production
- **Dateien:** `docker/nginx/nginx.prod.conf`, `docker/nginx/nginx.prod-no-ssl.conf`
- **Problem:** Keine `limit_req_zone` oder `limit_req` Direktiven. Dev-nginx hat Rate-Limiting, Prod nicht.

### M-2: Socket.IO Room-Joins ohne Autorisierung
- **Dateien:** `app/socketio_handlers/events_scenarios.py:33-55`, `events_markdown_collab.py:37-49`
- **Problem:** `scenario:subscribe` und `markdown_collab:subscribe` pruefen nicht ob der User Zugriff hat. Jeder authentifizierte User kann Echtzeit-Updates fuer jedes Szenario/Workspace empfangen.

### M-3: CSV Injection in Exports
- **Dateien:** `app/routes/auth/data_routes.py:97-121`, `app/services/generation/output_export_service.py:106-191`
- **Problem:** User-Content wird ohne Formel-Prefix in CSV geschrieben. `=CMD("calc")` in Excel ausfuehrbar.

### M-4: Import Sessions ohne Owner-Binding
- **Datei:** `app/services/data_import/import_service.py:99-128`
- **Problem:** In-Memory Sessions per UUID ohne User-Zuordnung. Jeder mit UUID kann fremde Sessions nutzen.

### M-5: Open User Registration
- **Datei:** `app/routes/auth/auth_routes.py:22-63`
- **Problem:** `@public_endpoint` -- Jeder kann Accounts erstellen, Authentik wird umgangen.

### M-6: Admin Registration Key kann leer sein
- **Datei:** `app/routes/auth/auth_routes.py:95-136`
- **Problem:** `ADMIN_REGISTRATION_KEY` Default = `''`. Leerer String passiert den Check.

### M-7: Tokens in sessionStorage (XSS-zugaenglich)
- **Datei:** `llars-frontend/src/utils/authStorage.js`
- **Problem:** JWT-Tokens in sessionStorage/localStorage zugaenglich. Bei XSS komplett stehlbar.

### M-8: Frontend Router prueft keine Permissions
- **Datei:** `llars-frontend/src/router.js:339-380`
- **Problem:** `requiresPermission` Meta wird nicht ausgewertet. Evaluator kann per URL auf Admin-UI navigieren (API-Calls scheitern, aber UI-Struktur ist sichtbar).

### M-9: PermissionRoutes leaken Error-Details
- **Datei:** `app/routes/PermissionRoutes.py`
- **Problem:** Raw `str(e)` statt `@handle_api_errors`. Interne Fehlerdetails werden zurueckgegeben.

### M-10: Redis ohne Authentifizierung
- **Datei:** `docker-compose.yml:441,496`
- **Problem:** Beide Redis-Instanzen ohne Passwort. Jeder Container im Netzwerk hat Zugriff.

### M-11: CSP mit unsafe-inline und unsafe-eval
- **Dateien:** `docker/nginx/nginx.prod.conf:54`, `nginx.prod-no-ssl.conf:54`
- **Problem:** Schwaecht XSS-Schutz erheblich.

### M-12: Rate Limiter nutzt In-Memory Storage
- **Datei:** `app/main.py:159`
- **Problem:** Per-Worker Limits, Reset bei Restart. Redis existiert aber ist nicht angebunden.

### M-13: User API Keys in Plaintext gespeichert
- **Datei:** `app/db/models/user.py:37`
- **Problem:** Kein Hashing/Encryption. DB-Leak = alle API-Keys kompromittiert.

### M-14: LaTeX Asset Upload ohne Typ-/Groessen-Limit
- **Datei:** `app/routes/latex_collab/latex_asset_routes.py:36-97`
- **Problem:** Akzeptiert JEDEN Dateityp, kein Size-Limit. SVG mit JS wird inline served.

### M-15: Messaging Attachment ohne Limits
- **Datei:** `app/routes/messaging/message_routes.py:109-133`
- **Problem:** Kein Dateityp-Filter, kein Size-Limit. Gesamte Datei in Memory gelesen.

### M-16: No Magic Byte Validation bei Uploads
- **Dateien:** `app/services/rag/document_service.py:39-41`, `app/services/chatbot/file_processor.py:74-86`
- **Problem:** Nur Extension-Check. Malicious File mit .pdf Extension passiert.

### M-17: Pagination ohne Upper Bound
- **Dateien:** `app/routes/rag/document_routes.py:45`, `app/routes/chatbot/chatbot_collection_routes.py:53`
- **Problem:** `per_page` ohne Maximum. `per_page=1000000` moeglich.

### M-18: Token-Exchange-Fehler loggt volle Response
- **Datei:** `app/routes/authentik_routes.py:325`
- **Problem:** `token_response.text` koennte Tokens/Secrets enthalten.

### M-19: Hardcoded admin123 in setup_authentik.py
- **Datei:** `setup_authentik.py:292`
- **Problem:** Admin-User wird immer mit `admin123` erstellt, env var wird ignoriert.

### M-20: Hardcoded Passwort im Frontend-Bundle
- **Datei:** `llars-frontend/src/components/Login.vue:180`
- **Problem:** `'admin123'` String existiert im JS-Bundle. Tot-Code-Pfad in Production, aber String sichtbar.

---

## LOW Findings

### L-1 bis L-15 (Kurzfassung)

| # | Problem | Datei |
|---|---------|-------|
| L-1 | 4 Dockerfiles ohne USER Statement | supervisor, livekit-agents, mkdocs, smoke-test |
| L-2 | MariaDB Port 55306 in Dev exponiert | docker-compose.yml:274 |
| L-3 | MkDocs Port in Prod nicht geschlossen | docker-compose.yml:356 |
| L-4 | Dev nginx ohne Security Headers | docker/nginx/nginx.conf |
| L-5 | OCSP Stapling deaktiviert | docker/nginx/nginx.prod.conf:319 |
| L-6 | Socket.IO CORS * in Dev | app/main.py:91 |
| L-7 | Health Endpoints leaken Service-Info | wizard_routes.py:452 |
| L-8 | .env.bak nicht in .gitignore | .gitignore |
| L-9 | Legacy Flask-JWT-Extended installiert | requirements.txt:8 |
| L-10 | Legacy keycloak-js im Frontend | package.json |
| L-11 | PyPDF2 deprecated | requirements.txt |
| L-12 | Werkzeug 3.0.1 hat bekannte CVEs | requirements.txt |
| L-13 | aiohttp 3.9.5 hat bekannte CVEs | requirements.txt |
| L-14 | gunicorn 21.2.0 veraltet | requirements.txt |
| L-15 | print() statt logger in oidc_validator.py | app/auth/oidc_validator.py |

---

## Positive Befunde

Die Analyse hat auch zahlreiche gut implementierte Sicherheitsmassnahmen identifiziert:

- **SQL Injection:** Exzellent -- SQLAlchemy ORM durchgaengig, parametrisierte Queries bei Raw-SQL
- **SSRF Protection:** Solide Implementierung in `auth/url_validator.py` mit DNS-Check, Private-IP-Block, Cloud-Metadata-Block
- **System API Key:** Timing-safe via `hmac.compare_digest`, nur Header (keine Query-Params)
- **Production Guards:** Server startet nicht mit Default FLASK_SECRET_KEY oder SYSTEM_ADMIN_API_KEY
- **File Uploads:** `secure_filename()` + UUID-Prefix, nicht direkt web-zugaenglich
- **Flask Container:** Laeuft als non-root User (flaskuser)
- **Keine privileged Container**
- **SSL/TLS:** Moderne Cipher-Suites, TLS 1.2+, HSTS in Production
- **CORS:** Korrekt restriktiv in Production
- **Error Handler:** CWE-209-Schutz -- interne Details nur fuer Admins
- **Permission System:** Deny-by-default, User > Rolle, Deny > Grant

---

## Empfohlene Massnahmen (Top 10, priorisiert)

| Prio | Finding | Aufwand | Impact |
|------|---------|---------|--------|
| 1 | C-1: Auth auf Transcript-Endpoint | 5 min | Unauthentifizierte Daten-Injection verhindern |
| 2 | C-2: Scenario Export Membership-Check | 5 min | Daten-Exfiltration verhindern |
| 3 | H-6/H-7: Scenario Stats/Thread IDOR | 10 min | IDOR-Luecken schliessen |
| 4 | C-3: LLMComparisonRoutes migrieren | 30 min | Auth-Bypass eliminieren |
| 5 | H-1: /my-permissions Auth-Decorator | 5 min | Permission-Enumeration verhindern |
| 6 | H-12/H-13: Production Guards fuer Secrets | 15 min | Encryption-Key Exposure verhindern |
| 7 | C-4: Docker Socket readonly/proxy | 30 min | Container-Escape verhindern |
| 8 | H-8/H-9: XSS Fixes (DOMPurify) | 15 min | Stored XSS verhindern |
| 9 | H-4: Security-Test Ignore-Liste leeren | 1h | Automatische Erkennung ermoeglichen |
| 10 | H-10: LaTeX subprocess Timeout | 5 min | DoS verhindern |

---

*Dieser Report wurde automatisch durch 6 parallele Security-Audit-Agents erstellt.*
