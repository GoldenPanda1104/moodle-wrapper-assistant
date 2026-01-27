# Moodle Wrapper Assistant

Moodle Wrapper Assistant is a web app that helps track and automate study workflows.
It includes a Python/FastAPI backend and a frontend client.

## Features

- Backend API with PostgreSQL storage
- Moodle integration hooks
- Docker Compose development setup

## Quick start (Docker)

1. Copy environment template and fill it in:

```bash
cp .env.example .env
```

2. Run the stack:

```bash
docker compose up --build
```

3. Open the apps:

- Frontend: http://localhost:4200
- Backend: http://localhost:8000

## Environment variables

Backend reads these variables (see `.env.example`):

- `PROJECT_NAME`
- `DATABASE_URL`
- `MOODLE_BASE_URL`
- `MOODLE_USERNAME`
- `MOODLE_PASSWORD`
- `APP_TIMEZONE`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
- `SERVER_MASTER_KEY`
- `MAILERSEND_API_KEY`
- `MAILERSEND_FROM_EMAIL`
- `MAILERSEND_FROM_NAME`
- `MAILERSEND_TO_EMAIL`

## Deploy on Dokploy (Docker Compose)

This project is designed to run with `docker-compose.yml` and a Postgres
container managed by Dokploy.

1. Create a new Docker Compose app in Dokploy and point it to this repo.
2. Set the required environment variables for the backend service.
3. Deploy the stack.

Recommended environment variables for Dokploy:

```
PROJECT_NAME=Moodle Wrapper
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/assistant
APP_TIMEZONE=America/Panama
MOODLE_BASE_URL=https://moodle.example.com
MOODLE_USERNAME=your-user
MOODLE_PASSWORD=your-pass
JWT_SECRET=change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=14
SERVER_MASTER_KEY=base64-32-bytes
MAILERSEND_API_KEY=
MAILERSEND_FROM_EMAIL=
MAILERSEND_FROM_NAME=Moodle Wrapper
MAILERSEND_TO_EMAIL=
```

Generate `SERVER_MASTER_KEY` (32 bytes, base64):

```bash
python - <<'PY'
import base64, os
print(base64.urlsafe_b64encode(os.urandom(32)).decode('ascii'))
PY
```

Health checks:

- Backend: `GET /health`
- Frontend: `GET /`

Notes:

- The frontend proxies `/api/` to the backend service inside Docker.
- If you expose the backend directly, expect `404` on `/` (use `/health`).

## Development

- Backend code: `backend`
- Frontend code: `assistant-frontend`
- Database volume: `postgres_data`

## License

Licensed under the GNU Affero General Public License v3.0. See `LICENSE`.

## Contributing

See `CONTRIBUTING.md`.
