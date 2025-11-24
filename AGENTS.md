# Repository Guidelines

## Project Structure & Module Organization
- `app/`: Flask backend with OIDC auth (Authentik), services, RAG pipeline, and Socket.IO handlers; static assets in `app/static`; Python deps in `app/requirements.txt`.
- `llars-frontend/`: Vue 3 + Vite UI using OIDC client and Socket.IO; built assets served through the Docker stack.
- `yjs-server/`: WebSocket service powering collaborative editing.
- `docker*/` and `start_llars.sh`: Docker Compose orchestration; `.env.development`/`.env.production` drive ports, secrets, and `PROJECT_STATE`.
- `docs/`, `data/`, and helper scripts (`create_keycloak_user.sh`, `test_login_and_llm.py`) hold architecture notes, sample content, and operational utilities.

## Build, Test, and Development Commands
- Start stack (auto dev/prod): `./start_llars.sh [dev|prod]` — uses compose with `--watch` in dev and production overrides when `PROJECT_STATE=production`.
- Backend tests/shell: `docker compose -p llars exec backend-flask-service pytest` (runs Python suite under `/app`).
- Frontend dev server: `cd llars-frontend && npm install && npm run dev` (Vite hot reload).
- Collaborative server: `cd yjs-server && npm install && node server.js` for standalone debugging.
- Stop stack: `docker compose -p llars down` (volumes removed only if `REMOVE_VOLUMES=True`).

## Coding Style & Naming Conventions
- Python: PEP 8 with 4-space indents; add type hints in services/routes and keep functions small with clear logging.
- Vue: single-file components in `PascalCase.vue`; composables in `src/composables` named `useX`; prefer `<script setup>` and scoped SCSS.
- Permissions follow `feature:<domain>:<action>` (see `PermissionService`); new API routes belong under `/auth` or `/api`.

## Testing Guidelines
- Backend: `pytest` inside the backend container; integration login/LLM check via `python test_login_and_llm.py` against a running stack.
- Permission smoke test: `python app/test_permission_service.py` (expects local MySQL per `.env` ports).
- Frontend: no automated suite yet—verify flows manually (Authentik login, socket interactions) and capture screenshots for regressions.

## Commit & Pull Request Guidelines
- Commits follow the repo pattern: short, imperative subjects (e.g., `Add dev/prod configs`), optional brief body.
- PRs should state purpose, linked issue/ticket, affected components, and test commands run; include UI screenshots for visible changes and note env/auth updates.
- Keep scope tight and update docs/config snippets when touching auth, ports, or compose files.

## Security & Configuration Tips
- Do not commit `.env*` or Authentik secrets; derive from templates and set `PROJECT_STATE` plus port vars explicitly.
- Backend routes must enforce `@keycloak_required` and `@require_permission` on new endpoints.
- For production, terminate TLS at the proxy, rotate credentials, and back rate limiting with Redis when enabled in compose overrides.
