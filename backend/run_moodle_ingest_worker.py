#!/usr/bin/env python3
"""
Punto de entrada del worker que consume la cola RabbitMQ moodle.ingest.

Uso (con RABBITMQ_URL configurado):
  python run_moodle_ingest_worker.py

En Docker Compose suele ejecutarse como servicio aparte con la misma
configuración de BD y RABBITMQ_* que el backend.
"""
import asyncio
import logging
import sys

# Asegurar que app esté en el path (ejecución desde backend/)
sys.path.insert(0, ".")

from app.services.moodle_ingest_consumer import run_consumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def main() -> None:
    asyncio.run(run_consumer())


if __name__ == "__main__":
    main()
