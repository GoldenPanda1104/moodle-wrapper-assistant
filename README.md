# Moodle Wrapper Assistant

Moodle Wrapper Assistant is a web app that helps track and automate study workflows.
It includes a Python/FastAPI backend and a frontend client.

## Features

- Backend API with PostgreSQL storage
- Moodle integration hooks
- Docker Compose development setup

## Quick start (Docker)

El proyecto usa **dos composes** para permitir despliegue por separado:

- **`docker-compose.yml`**: solo **db** y **backend** (API + PostgreSQL).
- **`docker-compose.frontend.yml`**: solo **frontend** (app web). Opcional; puedes correr el frontend en local con `npm run start:local`.

1. Copia la plantilla de entorno en la **raíz del proyecto** (Docker Compose carga el `.env` por estar en la misma carpeta):

```bash
cp .env.example .env
```

2. Levanta backend + DB:

```bash
docker compose up --build -d
```

3. (Opcional) Levanta el frontend en Docker (puerto 52052) o en local:

```bash
# Con backend en el mismo host (por defecto backend:8000 no resuelve; en otro servidor usa BACKEND_UPSTREAM):
# En Windows/Mac con backend en la máquina host:
docker compose -f docker-compose.frontend.yml up --build -d
# y configura BACKEND_UPSTREAM=host.docker.internal:8000 en el .env o al ejecutar

# O frontend en local (proxy a localhost:8000):
cd assistant-frontend && npm install && npm run start:local
```

4. Abre las apps:

- Backend: http://localhost:8000
- Frontend (Docker): http://localhost:52052 — o Frontend (local): http://localhost:4200

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

Puedes desplegar en dos apps separadas (recomendado para backend y frontend por separado) o en una sola si usas ambos composes.

- **App 1 – Backend + DB**: usa `docker-compose.yml`. En **Environment variables** configura las variables listadas abajo. No asignes dominio al backend si todo el tráfico web debe pasar por el frontend.
- **App 2 – Frontend**: usa `docker-compose.frontend.yml`. Configura `BACKEND_UPSTREAM` con el host:puerto del backend (p. ej. el nombre del servicio backend en la otra app o la URL pública del API). En la pestaña **Domains** asigna tu dominio al servicio **`frontend`**, puerto **`80`**:
  - **Protocol**: **HTTPS**.
  - **Certificate**: **Let's Encrypt**.
  - Todo el tráfico (`/`, `/login`, `/api/…`) debe llegar al contenedor frontend; Nginx sirve la SPA y hace proxy de `/api/` al backend (usando `BACKEND_UPSTREAM`).
  - No añadas labels Traefik manuales; Dokploy genera el router.
5. Despliega ambas apps (o una sola que use ambos archivos si tu flujo lo permite).

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
- **404 en `/login`, `/favicon.ico` o rutas de la SPA:** En **Domains** el destino debe ser **`frontend`**, puerto **`80`**, HTTPS y Let's Encrypt. No añadas labels Traefik manuales. Si persiste, quita dominios, despliega y vuelve a añadirlos.
- Si expones solo el backend, en `/` verás 404 (usa `/health` para comprobar).

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
