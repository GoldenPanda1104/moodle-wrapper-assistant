# Tests del backend

## Requisitos

- Dependencias instaladas: `pip install -r requirements.txt`
- Base de datos: `DATABASE_URL` (por defecto la de `app.core.config`). Las pruebas crean usuarios y datos de prueba; se recomienda usar una BD de test (ej. `assistant_test`).
- Migraciones aplicadas: `alembic upgrade head`

## Ejecutar

Desde el directorio `backend`:

```bash
pytest
# o solo los tests de ingest:
pytest tests/test_moodle_ingest.py -v
```

## test_moodle_ingest.py (T6)

Tests del endpoint `POST /api/v1/moodle/ingest`:

- **Payload válido**: 200, upserts en BD, snapshot guardado, diffs procesados.
- **Sin X-API-Key / API key inválida**: 401.
- **API key válida pero body.user_id distinto al dueño**: 403.
- **Usuario inactivo**: 401.
- **Body malformado** (falta user_id, falta snapshot, no JSON): 422.
