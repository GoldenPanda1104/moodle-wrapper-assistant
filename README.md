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
cp backend/.env.example backend/.env
```

2. Run the stack:

```bash
docker compose up --build
```

3. Open the apps:

- Frontend: http://localhost:4200
- Backend: http://localhost:8000

## Environment variables

Backend reads these variables (see `backend/.env.example`):

- `PROJECT_NAME`
- `DATABASE_URL`
- `MOODLE_BASE_URL`
- `MOODLE_USERNAME`
- `MOODLE_PASSWORD`

## Development

- Backend code: `backend`
- Frontend code: `assistant-frontend`
- Database volume: `postgres_data`

## License

Licensed under the GNU Affero General Public License v3.0. See `LICENSE`.

## Contributing

See `CONTRIBUTING.md`.
