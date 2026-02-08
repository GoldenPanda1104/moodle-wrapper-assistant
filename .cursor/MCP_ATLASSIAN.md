# Acceso del agente al MCP de Atlassian (Jira)

Esta guía explica cómo configurar Cursor para que el agente (incluido el Planner u otros comandos) pueda usar el **Model Context Protocol (MCP)** de Atlassian y crear/consultar epics y tareas en Jira.

## Resumen: un solo acceso para todos los agentes

El MCP de Atlassian se configura **una vez** (en `.cursor/mcp.json` o en Cursor Settings → MCP). Ese servidor está disponible para **toda la sesión** de Cursor. No se “da acceso por agente” en la configuración: todos los agentes que ejecutes en este proyecto usan el mismo MCP si está activo.

Lo que sí se controla por agente es la sección **Allowed Tools** en cada `AGENT.md`: ahí se define si ese agente puede usar herramientas de Jira y para qué. En este proyecto:

| Agente     | Uso de Jira |
|------------|-------------|
| **Delegator** | Lectura + escritura: asigna tareas y actualiza el campo Agent en cada issue. |
| **Planner**   | Lectura + escritura: crear/actualizar epics, tareas, búsquedas. |
| **Architect** | Lectura + escritura: crear o actualizar tickets de infra si hace falta. |
| **Backend**   | Lectura y actualización: comprobar Agent = "Backend", leer descripción/criterios; actualizar estado, comentarios, worklogs o campos cuando corresponda. |
| **Frontend**  | Lectura y actualización: comprobar Agent = "Frontend", leer descripción/criterios; actualizar estado, comentarios, worklogs o campos cuando corresponda. |
| **Tester**    | Lectura y actualización: comprobar Agent = "Tester", leer descripción/criterios; actualizar estado, comentarios, worklogs o campos cuando corresponda. |

Mientras el MCP esté configurado y autenticado (OAuth la primera vez), todos estos agentes pueden usar Jira dentro de lo que permite su `AGENT.md`.

La extensión **Atlassian for VS Code** (`atlassian.atlascode`) ofrece integración de Jira/Bitbucket en el editor (vistas, enlaces, etc.). El **MCP de Atlassian** es independiente: permite que el *agente de Cursor* llame a Jira/Confluence desde el chat (crear issues, buscar, etc.). Para que el agente tenga ese acceso hace falta configurar un servidor MCP.

---

## 1. Requisitos

- **Node.js v18+** y **npx** (para la opción con proxy).
- Cuenta en un **sitio Atlassian Cloud** con Jira (y opcionalmente Confluence/Compass).
- **Cursor** con soporte MCP (Composer/Agent).

---

## 2. Dónde se configura el MCP en Cursor

Puedes usar **una** de estas dos formas:

### A) Desde la UI de Cursor (recomendado)

1. Abre **Cursor Settings** (`Ctrl + ,`).
2. Ve a **Features → MCP** (o busca "MCP" en la barra de búsqueda).
3. Pulsa **"+ Add New MCP Server"** (o equivalente).
4. Configura:
   - **Name**: p. ej. `Atlassian-MCP-Server` o `mcp-atlassian`.
   - **Type**: **HTTP** / **Server-sent Events (SSE)**.
   - **URL**: `https://mcp.atlassian.com/v1/mcp`
5. Guarda y reinicia el asistente o la sesión del agente si hace falta.

En versiones antiguas de Cursor puede que solo haya tipo "stdio". En ese caso usa la opción B con el proxy.

### B) Archivo de configuración

Cursor puede leer la config desde:

- **Global (usuario)**  
  - Windows: `%USERPROFILE%\.cursor\mcp.json`  
  - macOS/Linux: `~/.cursor/mcp.json`
- **Proyecto**  
  - `D:\Trabajo\Suantechs\Proyectos\suantechs-finance\.cursor\mcp.json`

**Opción por URL (si tu Cursor admite `url` + `type`):**

```json
{
  "mcpServers": {
    "Atlassian-MCP-Server": {
      "url": "https://mcp.atlassian.com/v1/mcp",
      "type": "http"
    }
  }
}
```

**Opción por comando (proxy `mcp-remote`, útil si la URL directa falla o en Cursor antiguo):**

```json
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.atlassian.com/v1/mcp"]
    }
  }
}
```

Si Cursor usa otro esquema (p. ej. `servers` en vez de `mcpServers`), adapta el JSON según lo que muestre la UI al añadir un servidor.

---

## 3. Autenticación

El **Atlassian Rovo MCP Server** usa **OAuth 2.1** frente a tu sitio de Atlassian Cloud:

- La primera vez que el agente use una herramienta de Jira, se abrirá el navegador para iniciar sesión y autorizar.
- Guarda la sesión según las indicaciones de Atlassian.
- Si el token caduca, se te pedirá autorizar de nuevo.

No hace falta poner usuario/contraseña en el `mcp.json`; el flujo OAuth se gestiona en el navegador.

---

## 4. Dar acceso al agente Planner (o a otro agente)

Las herramientas MCP están disponibles para el **Agent/Composer** de Cursor. Si en el agente dice **"Allowed Tools: None"**, no usará ninguna herramienta, tampoco las de Jira.

Para que el agente **Planner** pueda crear epics y tareas en Jira cuando tú se lo pidas:

1. En **`.ai-system/agents/planner/AGENT.md`** se ha de permitir el uso de las herramientas MCP de Atlassian.
2. En la tabla **"Allowed Tools"** hay que incluir algo como:
   - Las tools concretas de Jira MCP (p. ej. `jira_create_issue`, `jira_update_issue`, `jira_search`, etc.), **o**
   - Una fila del estilo:  
     `| MCP Atlassian (Jira) | Cuando el usuario pida crear epics, tareas o buscar en Jira |`

En este proyecto, si quieres que el Planner pueda crear tickets, el `AGENT.md` del planner debe dejar de tener "None" y enumerar o describir el uso de las herramientas de Jira MCP.

---

## 5. Relación con la extensión `atlassian.atlascode`

- **Extensión Atlassian for VS Code** (`atlassian.atlascode`): integración de Jira/Bitbucket en el editor (paneles, enlaces, ver issues, etc.). No es la que expone herramientas al agente.
- **MCP de Atlassian**: otro canal; conecta el **agente de Cursor** con Jira/Confluence vía el protocolo MCP. Para que el agente “tenga acceso” a Jira hay que configurar este MCP (pasos 2 y 4).

Puedes tener la extensión instalada y, además, el MCP configurado: la extensión para tu flujo en la UI, el MCP para que el agente cree/consulte issues desde el chat.

---

## 6. Comprobar que funciona

1. Deja el MCP configurado y, si usas proxy, asegúrate de que `npx` y Node están en el PATH.
2. En **Composer**, escribe algo como: *“Busca en Jira los issues asignados a mí”* o *“Crea un epic de prueba en el proyecto X”*.
3. Cursor debería mostrarte una llamada a una herramienta MCP de Atlassian y pedirte aprobación antes de ejecutarla.
4. La primera vez, se abrirá el navegador para el OAuth de Atlassian.

Si nada de esto aparece, revisa que el servidor MCP esté habilitado en **Cursor Settings → Features → MCP** y que el agente que estás usando permita herramientas (véase apartado 4).

---

## Referencias

- [Setting up IDEs (Atlassian)](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/setting-up-ides/)
- [Cursor – Model Context Protocol (MCP)](https://docs.cursor.com/context/mcp)
- [Atlassian Remote MCP Server – Getting started](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/getting-started-with-the-atlassian-remote-mcp-server/)
