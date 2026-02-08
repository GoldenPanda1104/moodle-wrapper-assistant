# Imagen del scraper Moodle → ingest por HTTP al backend remoto.
# Ejecutable de forma independiente (no depende del resto del repo en runtime).
# Build desde la raíz del repo: docker build -f scraper/Dockerfile .
# Configuración vía variables de entorno (INGEST_URL, INGEST_API_KEY o API_KEY, etc.).

FROM python:3.12-bookworm

WORKDIR /app

# Código del backend (módulo moodle: adapter, diff, snapshot, pipeline) y script del scraper
COPY backend/app /app/app
COPY backend/requirements.txt /app/requirements.txt
COPY scraper/run_ingest.py /app/run_ingest.py

RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

ENV PYTHONPATH=/app

# Directorio donde el módulo snapshot guarda el JSON (opcional: montar volumen para persistir)
VOLUME ["/app/app/modules/moodle/data"]

ENTRYPOINT ["python", "/app/run_ingest.py"]
