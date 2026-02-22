# Architect

Infraestructura, despliegue, Docker, CI/CD y diseño de sistema.

## Definición completa

Ver **`.ai-system/agents/architect/AGENT.md`** — responsabilidades, dominio (Docker, K8s, cloud, CI/CD, seguridad a nivel sistema) y herramientas permitidas.

## Cuándo invocar en Cursor

- Tareas asignadas a Architect por el Delegator (o tipo infra en el plan).
- Docker, Docker Compose, Kubernetes, pipelines, entornos, secretos, observabilidad. No incluye instalar librerías de aplicación (eso es Backend/Frontend).

## Skills a cargar

- `docker`, `databases/postgres` (para aspectos infra de DB), y según tarea: architecture. Ver `.cursor/rules/08-docker.mdc`.

## Sub-agentes

- **docker-builder:** Dockerfiles, Compose, K8s.
- **security-auditor:** revisión de seguridad, OWASP, secretos.
- **ci-cd-builder:** pipelines, despliegue.
- **infra-builder:** Terraform, cloud.

Definiciones en `.ai-system/agents/sub/architect/`.

## Reglas de proyecto

- Scope solo infra; no cambiar lógica de aplicación. Documentar riesgos y trade-offs.
