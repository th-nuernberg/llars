# LLARS Quick Start (Development)

## 1) Start

```bash
cp .env.template.development .env
./start_llars.sh
```

## 2) Open

- LLARS: `http://localhost:55080`
- Authentik UI (optional direct): `http://localhost:55095`
- Docs (via nginx, dev): `http://localhost:55080/mkdocs/`

## 3) Login (LLARS)

| Username | Password |
|----------|----------|
| admin | admin123 |
| researcher | admin123 |
| evaluator | admin123 |

## 4) Matomo (Admin)

Admin -> **Analytics** -> **Open Matomo** (SSO).

## Troubleshooting

```bash
docker compose -p llars ps
docker compose -p llars logs backend-flask-service --tail=200
docker compose -p llars logs authentik-init --tail=200
docker compose -p llars logs matomo-init --tail=200
```
