# Despliegue remoto y acceso del scraper desde casa

Este documento describe cómo desplegar el stack en un servidor remoto y cómo un scraper ejecutado en un equipo en casa (sin IP pública) envía datos al backend mediante **HTTP/HTTPS**. No se usa RabbitMQ ni ningún broker; solo el API REST del backend.

---

## 1. Arquitectura de red

- **Servidor remoto**: puede alojar backend + base de datos en un compose y el frontend en otro (despliegue separado), o todo en el mismo host. Debe tener una **URL pública** (dominio o IP) para que el API sea accesible desde internet.
- **Equipo en casa**: ejecuta el scraper (Docker o script). **No necesita IP pública** ni puertos abiertos; solo debe poder hacer **conexiones salientes** (HTTPS) al servidor remoto.

```
┌─────────────────────────┐         HTTPS (saliente)          ┌──────────────────────────────┐
│  Casa (scraper)          │  ──────────────────────────────►  │  Servidor remoto             │
│  - Sin IP pública        │   POST /api/v1/moodle/ingest       │  - Backend (API)              │
│  - Cron / manual         │   Header: X-API-Key                │  - Frontend + Backend + DB    │
│  - Credenciales locales  │                                   │  - PostgreSQL                │
└─────────────────────────┘                                   └──────────────────────────────┘
```

---

## 2. Despliegue del stack remoto

**`docker-compose.yml`** incluye db, backend y frontend. En un solo servidor basta con desplegar ese compose y asignar tu dominio al servicio **frontend** (puerto 80); el frontend hace proxy de `/api` al backend.

Opcional: **`docker-compose.frontend.yml`** solo tiene el frontend; úsalo si quieres desplegar la app web en otro host (configura `BACKEND_UPSTREAM` con la URL del API).

### 2.1 Servicios (docker-compose.yml)

| Servicio   | Función                    | Puerto (interno) | Notas |
|-----------|----------------------------|------------------|--------|
| `db`      | PostgreSQL                 | 5432             | No exponer a internet. |
| `backend` | API FastAPI (incl. ingest)| 8000             | Debe ser alcanzable por HTTPS desde el scraper. |
| `frontend`| Aplicación web (Nginx)     | 80               | Asignar aquí el dominio; hace proxy de `/api` al backend. |

### 2.2 Variables de entorno en el remoto

En el servidor remoto, configurar al menos:

- `DATABASE_URL`: conexión a PostgreSQL (por defecto la del compose).
- `JWT_SECRET`: secreto para JWT (cambiar en producción).
- `SERVER_MASTER_KEY`: si se usa vault/credenciales en el backend.
- Opcionales: `MOODLE_BASE_URL`, MailerSend, `APP_TIMEZONE`, etc.

No se requieren variables de RabbitMQ; el ingest es solo HTTP.

### 2.3 Exponer el API por HTTPS

El backend escucha en el puerto 8000. Para producción:

1. **Reverse proxy** (Nginx, Caddy o Traefik) delante del backend:
   - Escuchar en 80/443 (HTTPS recomendado).
   - Terminar TLS y reenviar al `backend:8000` (o `localhost:8000` si todo va en la misma máquina).

2. **Dominio y DNS**: apuntar un nombre (ej. `api.tudominio.com`) al servidor remoto.

3. **Firewall**: permitir tráfico entrante en 80 y 443. No es necesario abrir ningún puerto en el equipo de casa.

La **URL base del API** que usará el scraper es la URL pública del backend, por ejemplo:

- `https://api.tudominio.com`

El scraper llamará a `https://api.tudominio.com/api/v1/moodle/ingest`.

---

## 3. Cómo el scraper en casa alcanza la API

- El scraper **solo inicia conexiones salientes** (cliente HTTP). No recibe conexiones entrantes.
- No se necesita IP pública ni abrir puertos en casa.
- Requisitos de red:
  - Salida a internet (HTTPS) hacia la URL pública del backend.
  - Si hay proxy corporativo o firewall saliente, debe permitir HTTPS al dominio del API.

No se usa túnel inverso ni RabbitMQ; el flujo es únicamente **POST HTTPS** desde el scraper al backend.

---

## 4. Configuración del scraper (token/API key y variables)

### 4.1 Obtener la API key de ingest

1. El usuario inicia sesión en la aplicación (frontend) con JWT.
2. Se llama a `POST /api/v1/moodle/ingest-key` (con JWT). El backend devuelve `{"api_key": "..."}` **una sola vez**.
3. Esa API key se guarda de forma segura en el equipo donde corre el scraper (archivo `.env` o variables de entorno) y **no se vuelve a mostrar** en la UI.

Si se pierde la key, se puede generar otra desde la app (la anterior deja de ser válida).

### 4.2 Variables de entorno del scraper

| Variable          | Obligatoria | Descripción |
|-------------------|-------------|-------------|
| `MOODLE_BASE_URL`| Sí          | URL base del sitio Moodle a scrapear. |
| `MOODLE_USERNAME` | Sí          | Usuario Moodle. |
| `MOODLE_PASSWORD`| Sí          | Contraseña Moodle. |
| `USER_ID`         | Sí          | ID del usuario en la BD del backend (el mismo que generó la API key). |
| `INGEST_URL`      | Sí          | **URL pública del backend** (ej. `https://api.tudominio.com`), sin barra final. |
| `INGEST_API_KEY`  | Sí*         | API key de ingest (o usar `API_KEY`). |

\* Una de las dos: `INGEST_API_KEY` o `API_KEY`.

Ejemplo de `.env` del scraper (copiar desde `scraper/.env.example`):

```bash
MOODLE_BASE_URL=https://moodle.ejemplo.edu
MOODLE_USERNAME=mi_usuario
MOODLE_PASSWORD=mi_password
USER_ID=1
INGEST_URL=https://api.tudominio.com
INGEST_API_KEY=la_clave_generada_en_ingest-key
```

### 4.3 Build y ejecución del scraper

- **Build**: desde la raíz del repo:  
  `docker build -f scraper/Dockerfile -t moodle-scraper .`
- **Ejecución**:  
  `docker run --rm --init --ipc=host --env-file scraper/.env moodle-scraper`

Para más detalle (volumen de datos, cron, ejecución local), ver [scraper/README.md](../scraper/README.md).

---

## 5. Resumen de seguridad

- **Autenticación del ingest**: solo requests con header `X-API-Key` válido son aceptados; la key está asociada a un usuario.
- **HTTPS**: usar siempre HTTPS en la URL del backend para que la API key y el payload no vayan en claro.
- **Credenciales en casa**: las credenciales de Moodle y la API key viven en el equipo donde corre el scraper; el backend no almacena credenciales Moodle del scraper.
- **Sin RabbitMQ**: no hay cola ni puertos AMQP que exponer; superficie de ataque reducida al API HTTP existente.

---

## 6. Referencias

- Contrato del payload y del endpoint: [moodle-ingest-spec.md](./moodle-ingest-spec.md).
- Build, variables y cron del scraper: [scraper/README.md](../scraper/README.md).
- Stack remoto: [docker-compose.yml](../docker-compose.yml) (stack completo). Opcional: [docker-compose.frontend.yml](../docker-compose.frontend.yml) para desplegar solo el frontend en otro host.
