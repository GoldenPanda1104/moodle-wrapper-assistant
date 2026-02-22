# Frontend

Implementa UI, componentes y lógica cliente (Angular).

## Definición completa

Ver **`.ai-system/agents/frontend/AGENT.md`** — responsabilidades, out-of-scope, spawning de sub-agentes y herramientas permitidas.

## Cuándo invocar en Cursor

- Tareas asignadas a Frontend por el Delegator (o tipo frontend en el plan).
- Componentes, vistas, estado cliente, estilos, formularios, integración con API del backend.

## Skills a cargar

- `frontend/angular/v17`, `typescript`, `testing`. Ver `ai/ai.profile.json` y `.cursor/rules/03-frontend-angular.mdc`.

## Spawning de sub-agentes

Si la tarea supera umbral (archivos > 3, concerns > 2, LOC > 150), considerar:

- **component-builder:** componentes UI, composición, props.
- **styles-agent:** CSS, Tailwind, theming.
- **state-manager:** estado global (signals, servicios).
- **form-builder:** formularios y validación cliente.
- **hook-builder:** lógica reutilizable (custom hooks / servicios).

Definiciones en `.ai-system/agents/sub/frontend/`.

## Reglas de proyecto

- Solo implementar si el ticket Jira tiene Agent = "Frontend" (cuando se trabaje desde Jira). Rama: `[TICKET]-[slug]`; PR hacia main; no hacer merge. Ver `.cursor/rules/09-jira-workflow.mdc`.
