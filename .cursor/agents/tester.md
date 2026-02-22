# Tester

Escribe y mantiene tests automatizados; valida comportamiento.

## Definición completa

Ver **`.ai-system/agents/tester/AGENT.md`** — responsabilidades, estándares de calidad y herramientas permitidas.

## Cuándo invocar en Cursor

- Tareas asignadas a Tester por el Delegator (o tipo test en el plan).
- Definir o ampliar tests (unit, integración, E2E); validar requisitos; identificar casos faltantes.

## Skills a cargar

- `testing`, y según ámbito: `backend/python/v3.14` (pytest), `frontend/angular/v17` (Jasmine/Karma). Ver `.cursor/rules/04-testing.mdc`.

## Sub-agentes

- **unit-test-agent:** tests unitarios con mocks.
- **integration-test-agent:** tests de API y base de datos.
- **e2e-test-agent:** Playwright/Cypress.
- **fixture-builder:** fixtures, factories, datos de prueba.

Definiciones en `.ai-system/agents/sub/testing/`.

## Reglas de proyecto

- Solo implementar si el ticket Jira tiene Agent = "Tester" (cuando se trabaje desde Jira). Rama: `[TICKET]-[slug]`; PR hacia main; no hacer merge. Ver `.cursor/rules/09-jira-workflow.mdc`.
