# Moodle Wrapper Assistant

Moodle Wrapper Assistant is a web app that helps track and automate study workflows.
It includes a Python/FastAPI backend and a frontend client.

## Features

- Backend API with PostgreSQL storage
- Moodle integration hooks
- Docker Compose development setup

## Quick start (Docker)

1. Copia la plantilla de entorno en la **raíz del proyecto** y relléna la que necesites. Docker Compose carga ese `.env` solo por estar en la misma carpeta que `docker-compose.yml` (no hace falta `env_file`):

```bash
cp .env.example .env
```

   Si no creas `.env`, el compose usa valores por defecto válidos para desarrollo (Postgres en `db:5432`, etc.).

2. Levanta el stack:

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
container managed by Dokploy. The compose file does **not** require a `.env`
file; all values come from environment variables (with defaults where applicable).

1. Create a new Docker Compose app in Dokploy and point it to this repo.
2. In the **Domains** tab, add your domain and assign it to the **frontend** service with port **80**.  
   All traffic (/, /login, /api/…) must go to the frontend; it serves the SPA and proxies `/api/` to the backend. If the domain points to the backend, you will get `404` on `/login`, `/favicon.ico`, etc.
3. In the app’s **Environment variables** (or “Env” section), set the variables
   listed below so they are available when `docker compose` runs. Do not rely
   on a `backend/.env` or `.env` file in the repo.
4. Deploy the stack.

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

- The frontend proxies `/api/` to the backend service inside Docker. If you see
  `502` or “backend could not be resolved”, the backend container is not running
  or not on the same Docker network—often because required env vars were missing
  at deploy time. Ensure all variables are set in Dokploy and that the backend
  service starts successfully.
- **404 en `/login`, `/favicon.ico` o rutas de la SPA:**  
  (1) En **Domains** el destino debe ser **frontend** y puerto **80**.  
  (2) El compose define una regla Traefik  
  `Host(\`…traefik.me\`,\`study.suantechs.com\`) && PathPrefix(\`/\`)`  
  con `priority=200` y `entrypoints=web,websecure`.  
  (3) En Dokploy, usa **Preview Compose** y comprueba que el servicio `frontend`  
  conserva las labels `traefik.http.routers.suantechs-frontend.*`. Si en el  
  preview no aparecen, Dokploy está sobrescribiendo las labels del servicio.  
  (4) La rama que despliega (p. ej. `main`) debe tener este `docker-compose.yml`.
- If you expose the backend directly, expect `404` on `/` (use `/health`).

## Development

- Backend code: `backend`
- Frontend code: `assistant-frontend`
- Database volume: `postgres_data`

### Local dev (backend in Docker, frontend local)

1) Start backend + db:

```bash
docker-compose up -d db backend
```

2) Run the frontend locally:

```bash
cd assistant-frontend
npm install
npm run start:local
```

This uses `assistant-frontend/proxy.local.json` to reach `http://localhost:8000`.

## PWA

The frontend is configured as a Progressive Web App for production builds.

- Manifest: `assistant-frontend/src/manifest.webmanifest`
- Service worker: `assistant-frontend/ngsw-config.json`

Build the frontend in production to enable the service worker:

```bash
cd assistant-frontend
npm run build -- --configuration production
```

## License

Licensed under the GNU Affero General Public License v3.0. See `LICENSE`.

## Contributing

See `CONTRIBUTING.md`.
