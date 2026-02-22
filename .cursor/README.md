# Cursor — Suantechs AI System

- **Entrada:** Lee [AGENTS.md](../AGENTS.md) en la raíz del proyecto.
- **Reglas:** [.cursor/rules/](rules/) — `00-boot.mdc` y `01-project-context.mdc` siempre; el resto por path (backend, frontend, testing, docker, etc.).
- **Agentes:** [.cursor/agents/](agents/) — orchestrator, planner, delegator, backend, frontend, tester, architect. Definiciones canónicas en [.ai-system/agents/](../.ai-system/agents/).
- **Skills:** [.cursor/skills/](skills/) — referencias al catálogo en [.ai-system/skills/](../.ai-system/skills/).
- **Comandos:** [.cursor/commands/](commands/) — invocación de agentes; deben respetar las reglas anteriores y AGENTS.md.
