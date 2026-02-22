# Planner

Descompone requisitos de alto nivel en un plan de tareas atómicas en JSON.

## Definición completa

Ver **`.ai-system/agents/planner/AGENT.md`** — es la fuente de verdad para responsabilidades, formato de salida y reglas.

## Cuándo invocar en Cursor

- Cuando el usuario pida un plan, descomposición de requisitos o una lista de tareas.
- Antes de delegar: el plan en JSON es la entrada del Delegator.
- Opcionalmente integrado con Jira (MCP Atlassian) para crear epics/tareas; ver skills jira-epic, jira-task en el AGENT.md del sistema.

## Reglas rápidas

- Salida siempre en JSON (project + tasks con id, title, description, type, dependencies, estimated_complexity).
- No escribir código ni modificar archivos.
- Cargar reglas: `.cursor/rules/00-boot.mdc`, `01-project-context.mdc`; si aplica Jira, `09-jira-workflow.mdc`.
