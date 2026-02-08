# Plan de acción: Swagger (OpenAPI) y modelo event-driven

**Proyecto:** suantechs-study  
**Alcance:** Documentar la API con Swagger/OpenAPI y evolucionar hacia un modelo event-driven interno para modularizar la ingest y futuras extensiones.  
**Contexto:** La funcionalidad de ingest por HTTP extiende (no replaza) lo existente; cualquier fuente (scraper en casa, otro servidor) que respete el contrato de datos puede ingestar. Sin RabbitMQ; entrada vía endpoints. El modelo event-driven debe guiar la implementación de **webhooks**, **actions** y **filters** (estilo WordPress), y permitir **correos** y **push notifications** sobre la data fetcheada de la plataforma.

---

## 1. Objetivos

| Objetivo | Descripción |
|----------|-------------|
| **Documentar la API** | Exponer y mejorar la documentación OpenAPI/Swagger de la aplicación para desarrolladores y clientes (scrapers, frontend, integraciones). |
| **Event-driven interno** | Introducir un modelo de eventos en proceso (sin broker externo) para desacoplar la lógica de ingest de sus efectos secundarios y permitir módulos futuros sin tocar el endpoint. |
| **Actions y filters (estilo WordPress)** | **Actions:** ejecutar lógica cuando ocurre un evento (webhooks, correo, push). **Filters:** transformar datos antes de persistir o de pasarlos al siguiente paso (ej. enriquecer snapshot, filtrar diffs). Mismo dispatcher, dos tipos de hooks. |
| **Webhooks como actions** | Permitir configurar URLs que reciban un POST cuando ocurran eventos relevantes (ingest recibido, survey detectada, módulo desbloqueado, etc.), con payload estándar (evento, datos, timestamp). |
| **Notificaciones (correo y push)** | Implementar actions que envíen correo y/o push notifications ante eventos relevantes de la data fetcheada (nueva encuesta, módulo desbloqueado, calificación publicada, etc.). |
| **Modularidad** | Mantener el contrato de datos (`docs/moodle-ingest-spec.md`); cualquier consumidor (HTTP POST o suscriptor de eventos) respeta el mismo contrato. |

---

## 2. Swagger / OpenAPI

### 2.1 Estado actual

- FastAPI ya genera OpenAPI 3.x y sirve Swagger UI en `/docs` y ReDoc en `/redoc` cuando la app está levantada.
- Falta: metadatos completos (descripción del API, versión, contacto), descripciones por operación, ejemplos en request/response, esquemas de seguridad (Bearer JWT, X-API-Key) documentados en OpenAPI, y tags ordenados por dominio.

### 2.2 Tareas (Swagger)

| Id | Título | Descripción | Tipo | Dependencias | Complejidad (1-5) |
|----|--------|-------------|------|--------------|--------------------|
| **SW-1** | Metadatos OpenAPI en FastAPI | Configurar en `app/main.py` (o donde se instancia `FastAPI`) los metadatos: `description`, `version`, `contact`, `license` si aplica. Usar `openapi_url` y opcionalmente `docs_url`/`redoc_url` para mantener `/docs` y `/redoc`. | backend | — | 1 |
| **SW-2** | Tags y agrupación por dominio | Definir tags con descripción (auth, tasks, events, moodle, vault) y asegurar que cada router ya use `tags=[...]` (ya parcialmente en `router.py`). Revisar que en Swagger UI se agrupen bien las operaciones. | backend | SW-1 | 1 |
| **SW-3** | Descripciones y ejemplos en endpoints | Añadir `summary` y `response_description` en los endpoints críticos (auth, moodle/ingest, moodle/ingest-key, vault, tasks). Añadir `example` o `examples` en los schemas Pydantic usados en body/response (p. ej. `MoodleIngestBody`) para que Swagger muestre ejemplos. | backend | SW-1 | 2 |
| **SW-4** | Esquemas de seguridad en OpenAPI | Configurar en FastAPI `openapi_components` (o equivalente) para documentar: (1) `Bearer` JWT para rutas que usan `get_current_user`, (2) `ApiKey` en header `X-API-Key` para el endpoint de ingest. Asignar `security` por ruta donde corresponda. | backend | SW-1 | 2 |
| **SW-5** | Exportar y versionar openapi.json | Añadir script o comando (ej. `python -c "from app.main import app; print(app.openapi())"` o endpoint opcional `GET /openapi.json` que devuelva el JSON) y guardar en `docs/openapi.json` (o `docs/api/openapi-v1.json`) para versionado en repo y uso por clientes externos. Documentar en README cómo generar y usar. | backend, docs | SW-2, SW-4 | 2 |

### 2.3 Orden sugerido (Swagger)

1. SW-1 → SW-2 → SW-3 y SW-4 en paralelo → SW-5.

### 2.4 Riesgos y notas (Swagger)

- No romper rutas existentes; solo enriquecer metadatos y documentación.
- Si el backend se sirve detrás de un proxy que quita prefijos, asegurar que `servers` en OpenAPI (si se configura) refleje la URL pública para que los ejemplos de “Try it” sean útiles.

---

## 3. Modelo event-driven (in-process, sin RabbitMQ)

### 3.1 Principio

- **Entrada única por HTTP:** el ingest sigue siendo un `POST /api/v1/moodle/ingest` (y el pipeline desde el backend que reutiliza la misma lógica). No se añade RabbitMQ ni colas externas.
- **Eventos internos:** tras validar y aplicar el ingest (upserts, snapshot, diffs), la aplicación emite eventos en memoria (p. ej. `MoodleIngestReceived`, `SnapshotApplied`, `DiffsProcessed`) a un dispatcher interno.
- **Handlers:** la lógica actual (guardar snapshot, aplicar diffs, crear tareas/eventos) se mantiene como handlers de esos eventos; opcionalmente se añaden más handlers (logs, métricas, o en el futuro webhooks a sistemas externos) sin modificar el endpoint.

Así la arquitectura queda modular: el contrato de datos sigue siendo el de `moodle-ingest-spec.md`; los “productores” son el endpoint HTTP y cualquier cliente que haga POST; los “consumidores” son los handlers internos (y en el futuro, si se desea, un webhook que reenvíe el mismo evento a un servicio externo).

### 3.2 Eventos de dominio propuestos

| Evento | Momento de emisión | Payload típico |
|--------|--------------------|----------------|
| `MoodleIngestReceived` | Tras validar body y user_id, antes de upserts | `user_id`, `snapshot` (resumen o referencia), `diffs_count` |
| `SnapshotApplied` | Tras upserts y `save_snapshot` | `user_id`, `snapshot_id` o equivalente |
| `DiffsProcessed` | Tras procesar todos los diffs | `user_id`, `diffs_count`, lista de eventos/tareas generados (opcional) |

(Los nombres y payloads se pueden ajustar al código existente; lo importante es tener al menos un evento “ingest received” y uno “processed” para enganchar side effects.)

### 3.3 Tareas (event-driven)

| Id | Título | Descripción | Tipo | Dependencias | Complejidad (1-5) |
|----|--------|-------------|------|--------------|--------------------|
| **EV-1** | Definir contrato de eventos internos | Documentar en `docs/event-model.md` (o sección en `moodle-ingest-spec.md`) los eventos, payloads y cuándo se emiten. Incluir que el contrato de datos de ingest sigue siendo el HTTP + JSON de la spec; los eventos son solo para uso interno y futuros suscriptores. | docs | — | 2 |
| **EV-2** | Implementar dispatcher de eventos en proceso | Añadir un módulo (ej. `app/core/events.py` o `app/services/event_bus.py`) con un dispatcher síncrono o asíncrono: `emit(event_name, payload)` y `subscribe(event_name, handler)`. Sin broker externo; handlers se ejecutan en el mismo proceso. | backend | — | 3 |
| **EV-3** | Emitir eventos desde el flujo de ingest | En el endpoint POST de ingest (y donde se reutilice la misma lógica), tras validar y antes de upserts emitir `MoodleIngestReceived`; tras snapshot emitir `SnapshotApplied`; tras diffs emitir `DiffsProcessed`. Mantener la lógica actual como handlers registrados por defecto (o extraer la lógica a handlers que se registran al arranque). | backend | EV-2 | 3 |
| **EV-4** | Registrar handlers por defecto | Asegurar que la lógica actual de ingest (upserts, save_snapshot, _handle_diff) se ejecute como handlers de los eventos anteriores (o que el flujo actual llame al dispatcher sin duplicar lógica). Objetivo: un solo lugar donde se aplica el contrato; los efectos secundarios se desacoplan detrás de eventos. | backend | EV-3 | 3 |
| **EV-5** | Documentar extensión con nuevos handlers | En `docs/event-model.md` (o arquitectura) explicar cómo añadir un nuevo handler (ej. notificaciones, webhook) sin tocar el endpoint ni el contrato HTTP. Opcional: ejemplo de handler que registra “ingest recibido” para logging o métricas. | docs | EV-1, EV-4 | 1 |

### 3.4 Orden sugerido (event-driven)

1. EV-1 → EV-2 → EV-3 → EV-4 → EV-5.

### 3.5 Riesgos y notas (event-driven)

- **Rendimiento:** los handlers son in-process; si en el futuro un handler es muy lento, considerar ejecutarlo en background (task en thread/process o cola interna) sin reintroducir RabbitMQ si no hace falta.
- **Consistencia:** si un handler falla, definir política (reintento, log y seguir, o fallar todo el request). Por defecto, fallar el request mantiene consistencia.
- **Modularidad:** la idea es que otro “servidor” o scraper solo necesite hacer POST al endpoint respetando el contrato; no tiene que conocer los eventos internos. Los eventos son para desacoplar módulos dentro del mismo backend.

---

## 4. Actions, filters, webhooks y notificaciones

El mismo modelo event-driven debe soportar **actions** (hacer algo cuando ocurre un evento) y **filters** (transformar datos antes de usarlos), de forma análoga a WordPress. Sobre eso se implementan webhooks, correo y push como actions concretas.

### 4.1 Modelo tipo WordPress

| Concepto | Descripción | Ejemplo |
|----------|-------------|---------|
| **Action** | Hook que se ejecuta cuando ocurre un evento. No devuelve valor; puede enviar correo, llamar a webhook, enviar push. | `survey_detected` → enviar email "Tienes una encuesta pendiente". |
| **Filter** | Hook que recibe datos y devuelve datos (transformados o filtrados). Se aplica antes de persistir o de pasar al siguiente handler. | Filter `snapshot_before_save` → enriquecer o filtrar cursos; filter `diffs_before_process` → excluir ciertos tipos de diff. |

- **Orden:** para un mismo evento, típicamente se ejecutan filters primero (para transformar el payload) y luego actions (para side effects). El dispatcher debe soportar ambos: `apply_filters(event_name, payload)` → payload modificado; `do_action(event_name, payload)` → sin retorno.
- **Granularidad de eventos:** además de `MoodleIngestReceived`, `SnapshotApplied`, `DiffsProcessed`, conviene emitir eventos más granulares para que las notificaciones y webhooks sean útiles: p. ej. `survey_detected`, `module_unlocked`, `blocked_detected`, `grade_item_updated` (según lo que ya produzca `_handle_diff`). Cada uno puede tener sus actions (webhook, email, push) y opcionalmente filters.

### 4.2 Webhooks como actions

- **Definición:** un webhook es una URL configurada por el usuario (o por tenant) que recibe un POST cuando ocurre uno o más eventos seleccionados.
- **Payload estándar:** `{ "event": "<nombre>", "timestamp": "<ISO8601>", "user_id": <id>, "data": { ... } }` donde `data` depende del evento (p. ej. para `survey_detected`: course, module, survey, url).
- **Configuración:** almacenar en BD (tabla `webhook_endpoints` o similar: user_id, url, eventos suscritos, secret opcional para firma). CRUD vía API o panel; el dispatcher, al hacer `do_action(event_name, payload)`, invoca al handler "webhook" que envía POST a las URLs registradas para ese evento.
- **Seguridad:** opcionalmente firmar el body (HMAC) con un secret para que el receptor verifique origen.

### 4.3 Notificaciones (correo y push)

- **Correo:** action que, ante eventos como `survey_detected`, `module_unlocked`, `grade_item_updated`, envía un correo al usuario (reutilizando o extendiendo el mailer existente). Plantillas por tipo de evento; configuración por usuario (activar/desactivar, preferencias).
- **Push:** action que envía notificación push (FCM, APNs o servicio unificado) con título y cuerpo derivados del evento. Requiere registrar dispositivos/tokens por usuario y configurar credenciales del proyecto push.

### 4.4 Tareas (actions, filters, webhooks, notificaciones)

| Id | Título | Descripción | Tipo | Dependencias | Complejidad (1-5) |
|----|--------|-------------|------|--------------|--------------------|
| **EV-6** | Soporte actions y filters en el dispatcher | Extender el módulo de eventos con `do_action(event_name, payload)` (ejecuta handlers sin retorno) y `apply_filters(event_name, payload)` (cadena de filters que devuelve el payload transformado). Definir orden: filters primero, luego actions. Documentar en `docs/event-model.md`. | backend | EV-2, EV-4 | 3 |
| **EV-7** | Eventos granulares por tipo de diff | Emitir eventos concretos desde _handle_diff: `survey_detected`, `module_detected`, `module_unlocked`, `blocked_detected`, `grade_item_updated` (o los que apliquen según diff.py). Payload mínimo: user_id, course, module, urls, etc. Permitir que actions y webhooks se suscriban a estos eventos. | backend | EV-3, EV-4, EV-6 | 3 |
| **EV-8** | Modelo y CRUD de webhooks | Modelo (y migración) para guardar webhooks: user_id, url, lista de eventos (o wildcard), secret opcional, activo. Endpoints o lógica para crear/listar/actualizar/eliminar webhooks (protegidos por JWT). Documentar en OpenAPI. | backend | EV-6, EV-7 | 3 |
| **EV-9** | Handler webhook (action) | Handler registrado como action para los eventos configurados: por cada webhook suscrito al evento, hacer POST al URL con payload estándar (event, timestamp, user_id, data). Ejecución en background recomendable (no bloquear request). Opcional: firma HMAC en header. | backend | EV-8 | 3 |
| **EV-10** | Action de correo para eventos relevantes | Registrar actions que envíen correo ante `survey_detected`, `module_unlocked`, y otros que se definan (p. ej. grade_item_updated). Usar mailer existente; plantillas por tipo; preferencias por usuario (activar/desactivar por evento o global). | backend | EV-7 | 3 |
| **EV-11** | Action de push notifications | Registrar action que envíe push (FCM/APNs o capa unificada) con título y cuerpo según evento. Requiere: modelo para tokens de dispositivo por usuario, configuración de credenciales push, y envío en background. Documentar requisitos de infra (claves, entorno). | backend, infra | EV-7 | 4 |
| **EV-12** | Documentar actions, filters y webhooks | En `docs/event-model.md`: lista de eventos disponibles, cómo registrar actions y filters, formato del payload de webhooks, cómo configurar correo y push. Incluir ejemplos (registrar webhook, desactivar notificaciones por evento). | docs | EV-6, EV-9, EV-10 | 2 |

### 4.5 Orden sugerido (extensión actions/filters/webhooks/notificaciones)

1. EV-6 (dispatcher con actions y filters) → EV-7 (eventos granulares).
2. EV-8 (modelo webhooks) y EV-10 (correo) pueden ir en paralelo tras EV-7.
3. EV-9 (handler webhook) tras EV-8.
4. EV-11 (push) cuando haya modelo de dispositivos y credenciales.
5. EV-12 (documentación) al final del bloque.

### 4.6 Riesgos y notas

- **Rendimiento:** webhooks y envío de correo/push deben ejecutarse en background (task, thread o cola en proceso) para no alargar la respuesta del ingest.
- **Fallo de webhook/correo:** no debe fallar el ingest; log + reintentos opcionales y desactivar webhook tras N fallos si se desea.
- **Privacidad:** en webhooks y notificaciones no exponer datos sensibles más allá de lo necesario (ej. no incluir credenciales Moodle en el payload).

---

## 5. Dependencias entre bloques

- **Swagger** y **event-driven** son independientes: se pueden hacer en paralelo o en el orden que prefiera el equipo.
- Si se quiere que en Swagger aparezca un “webhook” o callback futuro como extensión, conviene tener EV-1/EV-2 antes de documentar esa posibilidad en OpenAPI (opcional).

---

## 6. Resumen de entregables

| Entregable | Ubicación / descripción |
|------------|-------------------------|
| OpenAPI enriquecido | Metadatos, tags, descripciones, ejemplos, seguridad en `/docs` y `/redoc`. |
| openapi.json versionado | `docs/openapi.json` o `docs/api/openapi-v1.json` + instrucciones en README. |
| Contrato de eventos | `docs/event-model.md` (eventos, payloads, cómo extender con handlers). |
| Dispatcher + emisión | Módulo `app/core/events.py` (o similar), emisión en flujo de ingest, handlers por defecto. |
| Actions y filters | `do_action` y `apply_filters` en el dispatcher; eventos granulares (survey_detected, module_unlocked, etc.). |
| Webhooks | Modelo y CRUD de webhook_endpoints; handler que hace POST a URLs configuradas con payload estándar (event, timestamp, user_id, data). |
| Notificaciones (correo y push) | Actions de correo y push ante eventos relevantes; preferencias por usuario; ejecución en background. |
| Documentación de extensión | Cómo registrar actions, filters y webhooks; formato de payload; configuración de correo y push. |

---

## 7. Referencias

- Plan previo (ingest HTTP sin RabbitMQ): `rabbitmq_scraper_remoto_fe365de3_extended.plan.json`.
- Contrato de ingest: `docs/moodle-ingest-spec.md`.
- Backend FastAPI: `backend/app/main.py`, `backend/app/api/v1/router.py`, `backend/app/api/v1/endpoints/moodle.py`.
