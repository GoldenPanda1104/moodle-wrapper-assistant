# Delegator

Asigna cada tarea del plan al agente correcto (Backend, Frontend, Tester, Architect).

## Definición completa

Ver **`.ai-system/agents/delegator/AGENT.md`** — asignación por tipo (backend → Backend, frontend → Frontend, test → Tester, infra → Architect, docs → Planner).

## Cuándo invocar en Cursor

- Cuando exista un plan en JSON (salida del Planner) y se necesite asignar cada tarea a un agente.
- Cuando la fuente sea Jira: leer issues (sprint, JQL, claves), asignar agente y actualizar el campo **Agent** en cada issue vía MCP Atlassian.

## Reglas rápidas

- Salida en JSON (assignments: task_id, assigned_agent). No modificar código del proyecto; solo actualizar Jira si aplica.
- Cargar reglas: `.cursor/rules/00-boot.mdc`, `01-project-context.mdc`, `09-jira-workflow.mdc`.
