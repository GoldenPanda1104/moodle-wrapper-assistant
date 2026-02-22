# Backend

Implementa lógica de backend: APIs, servicios, persistencia y seguridad.

## Definición completa

Ver **`.ai-system/agents/backend/AGENT.md`** — responsabilidades, out-of-scope, spawning de sub-agentes y herramientas permitidas.

## Cuándo invocar en Cursor

- Tareas asignadas a Backend por el Delegator (o tipo backend en el plan).
- Endpoints, servicios, CRUD, migraciones, validación, auth JWT, integración con Moodle/APIs externas.

## Skills a cargar

- `backend/python/v3.14`, `databases/postgres`, `jwt`, `testing`. Ver `ai/ai.profile.json` y `.cursor/rules/02-backend-python.mdc`.

## Spawning de sub-agentes

Si la tarea supera umbral (archivos > 3, concerns > 2, LOC > 200), considerar:

- **api-builder:** endpoints, controladores, rutas.
- **service-builder:** lógica de negocio, repositorios.
- **migration-builder:** migraciones, schema, seeds.
- **validation-builder:** DTOs, validadores, guards.
- **queue-builder:** jobs, colas, workers.

Definiciones en `.ai-system/agents/sub/backend/`.

## Reglas de proyecto

- Solo implementar si el ticket Jira tiene Agent = "Backend" (cuando se trabaje desde Jira). Rama: `[TICKET]-[slug]`; PR hacia main; no hacer merge. Ver `.cursor/rules/09-jira-workflow.mdc`.
