# Agentes y contexto AI — Moodle Wrapper

Antes de responder a cualquier tarea:

1. **Leer esta guía** y determinar el agente adecuado (Orchestrator, Planner, Delegator, Backend, Frontend, Tester, Architect).
2. **Cargar el sistema base** desde `.ai-system/` — ver [.ai-system/AGENT.md](.ai-system/AGENT.md) para regla de arranque, agentes y skills.
3. **Aplicar reglas de Cursor:** `.cursor/rules/00-boot.mdc` (obligatorio) y `01-project-context.mdc` (obligatorio); el resto por path/globs.
4. **Cargar skills** definidos en `ai/ai.profile.json`; las reglas en `.cursor/rules/` indican qué skills aplicar por tipo de archivo.
5. **Respetar** visión y restricciones en `ai/ai.project.md`.

## Entrada rápida

- **Reglas:** `.cursor/rules/` (00-boot y 01-project-context siempre; 02–09 por globs).
- **Agentes Cursor:** `.cursor/agents/` (orchestrator, planner, delegator, backend, frontend, tester, architect).
- **Definiciones canónicas:** `.ai-system/agents/` y `.ai-system/agents/registry.yaml`.
- **Perfil del proyecto:** `ai/ai.profile.json`, `ai/ai.project.md`.

Este proyecto usa el **Suantechs AI System**; la configuración generada conecta Cursor con ese sistema vía `.ai-system/` y `.cursor/`.
