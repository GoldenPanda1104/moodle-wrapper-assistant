# Moodle Wrapper Assistant

Moodle Wrapper Assistant is a web app that helps track and automate study workflows.
It includes a Python/FastAPI backend and a frontend client.

## Features

- Backend API with PostgreSQL storage
- Moodle integration hooks
- Docker Compose development setup

## Quick start (Docker)

**`docker-compose.yml`** levanta el stack completo (db + backend + frontend). Un solo dominio puede apuntar al servicio **frontend** (puerto 80); el frontend hace proxy de `/api` al backend.

Opcional: **`docker-compose.frontend.yml`** sirve para desplegar solo el frontend en otro host.

1. Copia la plantilla de entorno en la **raíz del proyecto**:

```bash
cp .env.example .env
```

2. Levanta el stack:

```bash
docker compose up --build -d
```

3. Abre las apps:

- Frontend: http://localhost:52052
- Backend (API): http://localhost:8000

Para desarrollo con frontend en local (proxy a backend): `cd assistant-frontend && npm run start:local` → http://localhost:4200

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

### Configuración Paso a Paso

1. **Crea una app Docker Compose en Dokploy** y apunta al repo. **Compose Path**: `./docker-compose.yml` (stack completo: db + backend + frontend).

2. **Configura las variables de entorno** en la pestaña Environment:

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

# Traefik/Dokploy configuration (IMPORTANTE)
FRONTEND_DOMAIN=study.suantechs.com
BACKEND_DOMAIN=study-api.suantechs.com
TRAEFIK_CERTRESOLVER=letsencrypt
TRAEFIK_ENABLE_FRONTEND=true
TRAEFIK_ENABLE_BACKEND=true
BACKEND_UPSTREAM=backend:8000
```

3. **IMPORTANTE - Configuración de Dominios:**

   **Opción A: Usar Traefik Labels (Recomendado)**
   - NO añadas dominios en la pestaña "Domains" de Dokploy
   - Los dominios se configuran automáticamente mediante las variables de entorno `FRONTEND_DOMAIN` y `BACKEND_DOMAIN`
   - Asegúrate de que `TRAEFIK_CERTRESOLVER` coincida con el nombre del cert resolver de tu Traefik (por defecto: `letsencrypt`)
   - Los certificados SSL se obtienen automáticamente vía Let's Encrypt

   **Opción B: Usar la UI de Dokploy**
   - Si prefieres usar la pestaña "Domains" de Dokploy, configura:
     - `TRAEFIK_ENABLE_FRONTEND=false`
     - `TRAEFIK_ENABLE_BACKEND=false`
   - Luego añade manualmente tus dominios en la UI

4. **Despliega** y verifica que ambos servicios estén corriendo

### Verificación de Certificados SSL

Para verificar el cert resolver correcto de Traefik:
- Verifica el nombre en la configuración de Traefik de Dokploy (usualmente `letsencrypt`)
- Si el cert resolver tiene otro nombre, actualiza `TRAEFIK_CERTRESOLVER` en las variables de entorno

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

### Troubleshooting

**Error 404 en Frontend y Backend:**
- Verifica que `TRAEFIK_ENABLE_FRONTEND=true` y `TRAEFIK_ENABLE_BACKEND=true` estén configurados
- Asegúrate de que los dominios (`FRONTEND_DOMAIN`, `BACKEND_DOMAIN`) estén correctamente configurados
- Verifica que no haya dominios duplicados en la UI de Dokploy si estás usando Traefik labels

**Error: No se obtiene certificado SSL:**
- Verifica que `TRAEFIK_CERTRESOLVER` coincida con el nombre exacto del cert resolver en Traefik
- Común en Dokploy: `letsencrypt` (minúsculas)
- Los dominios deben apuntar correctamente a tu servidor (DNS configurado)
- Verifica que los puertos 80 y 443 estén abiertos en tu firewall

**Error 502 - Bad Gateway:**
- El backend no está corriendo o no está en la red `dokploy-network`
- Verifica que todas las variables de entorno estén configuradas (especialmente `DATABASE_URL`, `JWT_SECRET`, `SERVER_MASTER_KEY`)
- Revisa los logs del contenedor backend: `docker logs <container_name>`

**Error: Backend could not be resolved:**
- Verifica que `BACKEND_UPSTREAM=backend:8000` esté configurado
- Asegúrate de que ambos servicios estén en las redes `app-network` y `dokploy-network`

**Conflicto de routers Traefik:**
- Si tienes dominios configurados en la UI de Dokploy Y las variables de entorno, deshabilita uno de los dos
- Recomendado: usa solo las variables de entorno y deja la pestaña Domains vacía

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
