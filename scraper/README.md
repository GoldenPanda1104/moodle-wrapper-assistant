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

En un servidor local se puede programar con cron. Ejemplos:

- **Cada hora** (minuto 0 de cada hora):

```cron
0 * * * * docker run --rm --init --ipc=host -v /path/to/scraper-data:/app/app/modules/moodle/data --env-file /path/to/.env moodle-scraper
```

- **Cada 6 horas**:

```cron
0 */6 * * * docker run --rm --init --ipc=host -v /path/to/scraper-data:/app/app/modules/moodle/data --env-file /path/to/.env moodle-scraper
```

Ajusta `/path/to/scraper-data` y `/path/to/.env` a tus rutas reales.

### Cómo obtener las rutas completas (Ubuntu)

Desde la raíz del repo y con la carpeta de datos creada (`mkdir -p ~/scraper-data`):

```bash
echo "Ruta .env:   $(realpath scraper/.env)"
echo "Ruta datos:  $(realpath ~/scraper-data)"
echo "Ruta docker: $(which docker)"
```

Usa esas rutas en la línea del cron.

### Registrar el cron en Ubuntu

1. Abre el crontab de tu usuario:
   ```bash
   crontab -e
   ```
2. Añade la línea (cada hora) al final del archivo, con tus rutas reales. Si `docker` no está en el PATH de cron, usa la ruta completa (`which docker`):
   ```cron
   0 * * * * /usr/bin/docker run --rm --init --ipc=host -v /home/TU_USUARIO/scraper-data:/app/app/modules/moodle/data --env-file /home/TU_USUARIO/suantechs-study/scraper/.env moodle-scraper
   ```
3. Guarda y cierra (en nano: `Ctrl+O`, Enter, `Ctrl+X`).
4. Verifica: `crontab -l`.
