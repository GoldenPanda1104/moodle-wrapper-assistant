# Scraper Moodle → Ingest HTTP

Imagen Docker y script para obtener datos de un sitio Moodle y enviarlos al backend remoto mediante `POST /api/v1/moodle/ingest`. La imagen **se ejecuta de forma independiente** (no depende del resto del repo ni de otros contenedores en runtime).

Para **despliegue del stack remoto** y **acceso desde casa** (HTTPS, URL pública, configuración de API key), ver [docs/deploy-remoto-y-scraper-casa.md](../docs/deploy-remoto-y-scraper-casa.md).

## Build

Desde la **raíz del repo**:

```bash
docker build -f scraper/Dockerfile -t moodle-scraper .
```

## Configuración (API_KEY e INGEST_URL)

Todas las opciones se configuran por **variables de entorno**:

| Variable | Obligatoria | Descripción |
|----------|-------------|-------------|
| `MOODLE_BASE_URL` | Sí | URL base del sitio Moodle |
| `MOODLE_USERNAME` | Sí | Usuario Moodle |
| `MOODLE_PASSWORD` | Sí | Contraseña Moodle |
| `USER_ID` | Sí | ID del usuario en el backend |
| `INGEST_URL` | Sí | URL base del API (ej. `https://api.ejemplo.com`) |
| `INGEST_API_KEY` o `API_KEY` | Sí | API key de ingest (generada en el backend con `POST /api/v1/moodle/ingest-key`) |

Copiar `scraper/.env.example` a `.env` y rellenar; luego pasar al contenedor con `--env-file .env` o `-e` individual.

## Ejecución

```bash
docker run --rm --init --ipc=host \
  --env-file scraper/.env \
  moodle-scraper
```

- `--ipc=host`: recomendado para Chromium (evita fallos de memoria).
- `--init`: evita procesos zombie.

Para persistir el snapshot entre ejecuciones (cálculo de diffs):

```bash
docker run --rm --init --ipc=host \
  -v scraper-data:/app/app/modules/moodle/data \
  --env-file scraper/.env \
  moodle-scraper
```

## Ejecución en local (sin Docker)

Desde la raíz del repo, con dependencias del backend instaladas:

```bash
cd backend && pip install -r requirements.txt && playwright install --with-deps chromium && cd ..
PYTHONPATH=backend python scraper/run_ingest.py
```

Las variables de entorno deben estar definidas (export o `.env` cargado). El script añade `backend` al path si no se ejecuta bajo `/app` (Docker).

## Cron / programación

En un servidor local se puede programar con cron, por ejemplo cada 6 horas:

```cron
0 */6 * * * docker run --rm --init --ipc=host -v /path/to/scraper-data:/app/app/modules/moodle/data --env-file /path/to/.env moodle-scraper
```
