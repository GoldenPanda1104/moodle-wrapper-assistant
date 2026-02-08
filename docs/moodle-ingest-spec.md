# Especificación: Ingest Moodle (contrato de payload)

## 1. Propósito

Define el **contrato del payload** que cualquier fuente de datos Moodle debe cumplir para ingestar en el backend. El backend aplica upserts en BD, guarda el snapshot y procesa diffs (eventos y tareas) de forma uniforme, independientemente del origen.

**Extensión, no reemplazo.** Esta funcionalidad no suplanta lo ya existente (p. ej. pipeline disparado desde el backend por API o scheduler); añade **nuevas maneras** de ingestar datos. Puede ser un scraper en casa, otro servidor que scrapea de forma distinta, o cualquier cliente que respete este contrato.

---

## 1.1 Fuentes de ingest (ejemplos)

| Fuente | Descripción |
|--------|-------------|
| **Backend (pipeline)** | El backend conecta a Moodle con credenciales del vault, ejecuta el pipeline y persiste en BD. Sigue disponible. |
| **Scraper remoto vía HTTP** | Un scraper (en casa o en otro servidor) obtiene los datos por su cuenta y envía un POST a `/api/v1/moodle/ingest` con el mismo payload. Respeta el contrato; el backend no sabe ni necesita saber cómo se obtuvieron los datos. |

Cualquier otra fuente (otro servidor, otro tipo de scraper, integración futura) solo debe producir el mismo JSON (`user_id`, `snapshot`, `diffs`) para ser aceptada por el backend.

---

## 2. Ingest vía HTTP

| Aspecto | Especificación |
|---------|----------------|
| **Método** | `POST` |
| **URL relativa** | `/api/v1/moodle/ingest` (base: URL pública del backend, ej. `https://api.ejemplo.com`) |
| **Content-Type** | `application/json` |
| **Autenticación** | **API key** en header `X-API-Key`. La key se genera una vez por usuario con `POST /api/v1/moodle/ingest-key` (requiere JWT); se guarda en el servidor local/scraper (env) y no se vuelve a mostrar. Más consistente y manejable que JWT para el scraper. |
| **Respuesta éxito** | `200 OK` (body opcional, ej. `{"status":"ok"}`). |
| **Respuesta error** | `4xx` según validación: body malformado, `user_id` inexistente o inactivo, o no autenticado. |

**Obtener la API key:** el usuario autenticado (JWT) llama a `POST /api/v1/moodle/ingest-key`; el backend devuelve `{"api_key": "..."}` una sola vez. Esa clave se configura en el scraper (variable de entorno `INGEST_API_KEY` o similar).

El scraper debe implementar **reintentos** (ej. 2–3 intentos con backoff) si el remoto no responde o devuelve 5xx.

---

## 3. Payload del body (JSON)

El body del POST es un único objeto JSON con tres campos obligatorios.

### 3.1 Campos raíz

| Campo      | Tipo   | Obligatorio | Descripción |
|-----------|--------|-------------|-------------|
| `user_id` | `integer` | Sí       | Identificador del usuario en la base de datos del backend remoto. El endpoint valida que exista y esté activo. |
| `snapshot`| `object`  | Sí       | Estado actual completo de cursos, módulos, encuestas y calificaciones. Estructura definida más abajo. |
| `diffs`   | `array`   | Sí       | Lista de diferencias respecto al snapshot anterior (salida de `diff_snapshots`). Puede ser `[]` si no hay cambios. |

### 3.2 Estructura de `snapshot`

El `snapshot` debe ser un objeto con exactamente cuatro claves, alineado con `backend/app/modules/moodle/snapshot.py` y el pipeline actual:

| Clave            | Tipo   | Descripción |
|------------------|--------|-------------|
| `courses`        | `array` | Lista de cursos. Cada elemento es un objeto con `id` (string) y `name` (string). |
| `modules`        | `array` | Lista de módulos. Cada elemento es un objeto con los campos del modelo MoodleModule (ver tabla). |
| `module_surveys` | `array` | Lista de encuestas de módulos. Cada elemento con campos de MoodleModuleSurvey. |
| `grade_items`    | `array` | Lista de ítems de calificación. Cada elemento con campos de MoodleGradeItem. |

#### Campos por tipo de elemento

**Course** (cada item en `courses`):

- `id`: string
- `name`: string

**Module** (cada item en `modules`):

- `id`: string  
- `course_id`: string  
- `title`: string  
- `visible`: boolean  
- `blocked`: boolean  
- `block_reason`: string | null  
- `has_survey`: boolean  
- `url`: string | null  

**Module survey** (cada item en `module_surveys`):

- `id`: string  
- `module_id`: string  
- `course_id`: string  
- `title`: string  
- `url`: string | null  
- `completion_url`: string | null  

**Grade item** (cada item en `grade_items`):

- `id`: string  
- `course_id`: string  
- `title`: string  
- `item_type`: string  
- `grade_value`: number | null  
- `grade_display`: string | null  
- `url`: string | null  
- `available_at`: string | null  
- `due_at`: string | null  
- `submission_status`: string | null  
- `grading_status`: string | null  
- `last_submission_at`: string | null  
- `attempts_allowed`: number | null  
- `time_limit_minutes`: number | null  

---

## 4. Estructura de cada elemento en `diffs`

Cada elemento de `diffs` es un objeto con al menos un campo `type`. Los tipos y campos adicionales son los que produce `backend/app/modules/moodle/diff.py` y consume `_handle_diff` en el pipeline.

| Tipo                | Campos adicionales típicos | Uso en el backend |
|---------------------|---------------------------|---------------------|
| `course_detected`   | `course_id`, `course`      | Evento MOODLE_COURSE_DETECTED |
| `module_detected`   | `course_id`, `course`, `module_id`, `module`, `module_url` | Evento + posible creación de tarea "Nuevo módulo disponible" |
| `survey_detected`   | `course_id`, `course`, `module_id`, `module`, `module_url` | Evento + creación de tarea "Enviar encuesta" |
| `blocked_detected`  | `course_id`, `course`, `module_id`, `module`, `reason`, `module_url` | Evento MOODLE_BLOCKED_DETECTED |
| `module_unlocked`   | `course_id`, `course`, `module_id`, `module`, `reason`, `module_url` | Evento MOODLE_MODULE_UNLOCKED |

Todos los diffs pueden incluir `course_id`, `course`, `module_id`, `module`, `module_url` cuando aplican al módulo.

---

## 5. Comportamiento esperado del endpoint

1. Deserializar el JSON del body del POST.
2. Validar que existan `user_id`, `snapshot` y `diffs`, y que `user_id` corresponda a un usuario existente y activo en la BD. Si no, responder con 4xx sin procesar.
3. Aplicar upserts con los datos del `snapshot`: cursos, módulos, module_surveys, grade_items (reutilizando `crud_moodle.upsert_*`).
4. Guardar el snapshot con `save_snapshot(user_id, snapshot)`.
5. Por cada elemento en `diffs`, ejecutar la lógica equivalente a `_handle_diff` (registro de eventos y creación de tareas cuando corresponda).

Body malformado (JSON inválido o campos obligatorios faltantes) debe responderse con 4xx (ej. 400 Bad Request o 422 Unprocessable Entity).

---

## 6. Ejemplo de payload

```json
{
  "user_id": 42,
  "snapshot": {
    "courses": [
      { "id": "123", "name": "Introducción a Python" }
    ],
    "modules": [
      {
        "id": "456",
        "course_id": "123",
        "title": "Semana 1 - Bienvenida",
        "visible": true,
        "blocked": false,
        "block_reason": null,
        "has_survey": true,
        "url": "https://moodle.ejemplo.edu/mod/page/view.php?id=456"
      }
    ],
    "module_surveys": [
      {
        "id": "789",
        "module_id": "456",
        "course_id": "123",
        "title": "Encuesta inicial",
        "url": "https://moodle.ejemplo.edu/mod/survey/view.php?id=789",
        "completion_url": null
      }
    ],
    "grade_items": []
  },
  "diffs": [
    {
      "type": "module_detected",
      "course_id": "123",
      "course": "Introducción a Python",
      "module_id": "456",
      "module": "Semana 1 - Bienvenida",
      "module_url": "https://moodle.ejemplo.edu/mod/page/view.php?id=456"
    },
    {
      "type": "survey_detected",
      "course_id": "123",
      "course": "Introducción a Python",
      "module_id": "456",
      "module": "Semana 1 - Bienvenida",
      "module_url": "https://moodle.ejemplo.edu/mod/survey/view.php?id=789"
    }
  ]
}
```

---

## 7. Consideraciones de arquitectura

- **Idempotencia**: Los upserts se basan en claves naturales; enviar el mismo payload más de una vez no debe duplicar datos. Opcional: deduplicación por `(user_id, snapshot_id)` si se añade un identificador de snapshot al body.
- **Tamaño**: Los snapshots pueden ser grandes. El backend debe configurar un límite de tamaño de body adecuado (ej. en el reverse proxy o en FastAPI).
- **Orden**: Si el scraper envía varios POST seguidos, el backend procesa en el orden en que llegan; la lógica de diffs asume que el snapshot anterior es el último aplicado para ese `user_id`.

---

## 8. Referencias en el código

- Snapshot: `backend/app/modules/moodle/snapshot.py`
- Cálculo de diffs: `backend/app/modules/moodle/diff.py`
- Procesamiento en backend: `backend/app/modules/moodle/pipeline.py` (`_handle_diff`; el endpoint POST de ingest reutilizará la misma lógica que el pipeline para upserts, `save_snapshot` y diffs).
