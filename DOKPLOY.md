# Guía de Despliegue en Dokploy

Esta guía detalla el proceso completo para desplegar Moodle Wrapper Assistant en Dokploy.

## 📋 Pre-requisitos

1. **Servidor con Dokploy instalado**
2. **Dominios configurados** apuntando a tu servidor:
   - Frontend: `study.suantechs.com` (o tu dominio)
   - Backend: `study-api.suantechs.com` (o tu dominio)
3. **Puertos abiertos**: 80 (HTTP) y 443 (HTTPS)
4. **Traefik configurado** en Dokploy (viene por defecto)

## 🚀 Pasos de Despliegue

### 1. Crear Aplicación en Dokploy

1. Entra a Dokploy y crea un nuevo proyecto
2. Selecciona **"Docker Compose"** como tipo de aplicación
3. Conecta tu repositorio Git
4. Configura:
   - **Repository URL**: `https://github.com/tu-usuario/moodle-wrapper-assistant`
   - **Branch**: `main` (o tu rama principal)
   - **Compose Path**: `./docker-compose.yml`

### 2. Configurar Variables de Entorno

Ve a la pestaña **Environment** y añade las siguientes variables:

#### Variables Obligatorias

```bash
# Aplicación
PROJECT_NAME=Moodle Wrapper
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/assistant
APP_TIMEZONE=America/Panama

# Seguridad (CAMBIAR ESTOS VALORES)
JWT_SECRET=tu-secreto-super-seguro-cambiar-esto
SERVER_MASTER_KEY=<genera con el comando abajo>

# Moodle Integration
MOODLE_BASE_URL=https://tu-moodle.com
MOODLE_USERNAME=tu-usuario
MOODLE_PASSWORD=tu-password

# Traefik/Dokploy (IMPORTANTE - Ajustar tus dominios)
FRONTEND_DOMAIN=study.suantechs.com
BACKEND_DOMAIN=study-api.suantechs.com
TRAEFIK_CERTRESOLVER=letsencrypt
TRAEFIK_ENABLE_FRONTEND=true
TRAEFIK_ENABLE_BACKEND=true
BACKEND_UPSTREAM=backend:8000

# JWT Config
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=14
```

#### Variables Opcionales (Email)

```bash
MAILERSEND_API_KEY=tu-api-key
MAILERSEND_FROM_EMAIL=noreply@tudominio.com
MAILERSEND_FROM_NAME=Moodle Wrapper
MAILERSEND_TO_EMAIL=admin@tudominio.com
```

### 3. Generar SERVER_MASTER_KEY

Ejecuta este comando en tu terminal local:

```bash
python - <<'PY'
import base64, os
print(base64.urlsafe_b64encode(os.urandom(32)).decode('ascii'))
PY
```

Copia el resultado y pégalo como valor de `SERVER_MASTER_KEY`.

### 4. Verificar Configuración de Traefik

#### Opción A: Usar Traefik Labels (Recomendado)

Esta es la configuración por defecto y más flexible:

1. **NO añadas dominios** en la pestaña "Domains" de Dokploy
2. Los dominios se configuran automáticamente vía las variables:
   - `FRONTEND_DOMAIN`
   - `BACKEND_DOMAIN`
3. El certificado SSL se obtiene automáticamente vía `TRAEFIK_CERTRESOLVER`

**Ventajas:**
- Configuración mediante código (Infrastructure as Code)
- Fácil de versionar y replicar
- Redirección HTTP → HTTPS automática

#### Opción B: Usar la UI de Dokploy

Si prefieres configurar dominios manualmente:

1. Configura las variables:
   ```bash
   TRAEFIK_ENABLE_FRONTEND=false
   TRAEFIK_ENABLE_BACKEND=false
   ```
2. Ve a la pestaña **Domains** en Dokploy
3. Añade el dominio del frontend:
   - **Domain**: `study.suantechs.com`
   - **Container Port**: `80`
   - **Service**: `frontend`
   - **HTTPS**: Activado
   - **Certificate**: Let's Encrypt
4. Añade el dominio del backend (si lo necesitas expuesto):
   - **Domain**: `study-api.suantechs.com`
   - **Container Port**: `8000`
   - **Service**: `backend`
   - **HTTPS**: Activado
   - **Certificate**: Let's Encrypt

**Nota:** En la mayoría de casos, solo necesitas exponer el frontend ya que este hace proxy del backend.

### 5. Verificar Nombre del Cert Resolver

El nombre del cert resolver debe coincidir exactamente con la configuración de Traefik en Dokploy:

1. Por defecto en Dokploy: `letsencrypt` (minúsculas)
2. Si tienes un nombre diferente, actualiza `TRAEFIK_CERTRESOLVER`

Para verificar el cert resolver correcto:
```bash
docker exec -it <traefik-container> cat /etc/traefik/traefik.yml
```

Busca la sección `certificatesResolvers`.

### 6. Desplegar

1. Haz clic en **Deploy**
2. Espera a que se construyan las imágenes (puede tomar 5-10 minutos)
3. Verifica los logs en tiempo real

### 7. Verificación Post-Despliegue

#### Verificar que los contenedores están corriendo

```bash
docker ps | grep -E "(frontend|backend|db)"
```

Deberías ver 3 contenedores:
- `frontend`
- `backend`
- `db` (PostgreSQL)

#### Verificar healthchecks

```bash
# Backend
curl https://study-api.suantechs.com/health

# Frontend
curl https://study.suantechs.com/
```

#### Verificar certificados SSL

```bash
curl -vI https://study.suantechs.com 2>&1 | grep -i "SSL certificate"
```

Deberías ver el certificado de Let's Encrypt.

## 🔧 Troubleshooting

### Error: 404 en ambos servicios (frontend y backend)

**Causa:** Las etiquetas de Traefik no están activas o los dominios no están configurados.

**Solución:**
1. Verifica que `TRAEFIK_ENABLE_FRONTEND=true` y `TRAEFIK_ENABLE_BACKEND=true`
2. Verifica que `FRONTEND_DOMAIN` y `BACKEND_DOMAIN` estén configurados correctamente
3. Verifica los logs de Traefik:
   ```bash
   docker logs <traefik-container> 2>&1 | grep -i error
   ```

### Error: Solo el frontend da 404

**Causa:** Conflicto de routers en Traefik o configuración incorrecta del dominio del frontend.

**Solución:**
1. Verifica que `FRONTEND_DOMAIN` esté correctamente configurado
2. Si añadiste dominios en la UI de Dokploy, quítalos (o deshabilita Traefik labels)
3. Redespliega la aplicación

### Error: No se obtiene certificado SSL

**Causas posibles:**
- El dominio no apunta correctamente al servidor
- El puerto 80 o 443 está bloqueado
- El nombre del cert resolver es incorrecto

**Solución:**
1. Verifica DNS:
   ```bash
   dig study.suantechs.com
   ```
2. Verifica que apunte a la IP de tu servidor
3. Verifica puertos abiertos:
   ```bash
   nc -zv localhost 80
   nc -zv localhost 443
   ```
4. Verifica el cert resolver:
   ```bash
   docker exec -it <traefik-container> cat /etc/traefik/traefik.yml | grep -A 5 certificatesResolvers
   ```
5. Si el nombre es diferente a `letsencrypt`, actualiza `TRAEFIK_CERTRESOLVER`

### Error: 502 Bad Gateway

**Causa:** El backend no está corriendo o no puede conectar con la base de datos.

**Solución:**
1. Verifica logs del backend:
   ```bash
   docker logs <backend-container>
   ```
2. Verifica que todas las variables obligatorias estén configuradas
3. Verifica que el contenedor `db` esté corriendo:
   ```bash
   docker ps | grep db
   ```
4. Verifica la conexión a la base de datos:
   ```bash
   docker exec -it <backend-container> python -c "from app.core.database import engine; engine.connect()"
   ```

### Error: Backend could not be resolved (en logs del frontend)

**Causa:** El frontend no puede resolver el nombre del backend en la red Docker.

**Solución:**
1. Verifica que `BACKEND_UPSTREAM=backend:8000`
2. Verifica que ambos servicios estén en las mismas redes:
   ```bash
   docker network inspect dokploy-network
   docker network inspect app-network
   ```
3. Ambos contenedores (`frontend` y `backend`) deben aparecer en ambas redes

### Error: Conflict - router already exists

**Causa:** Routers duplicados en Traefik (UI + labels).

**Solución:**
1. Si usas Traefik labels, NO añadas dominios en la UI de Dokploy
2. O viceversa: si usas la UI, deshabilita las labels:
   ```bash
   TRAEFIK_ENABLE_FRONTEND=false
   TRAEFIK_ENABLE_BACKEND=false
   ```

## 📊 Monitoreo

### Ver logs en tiempo real

```bash
# Frontend
docker logs -f <frontend-container>

# Backend
docker logs -f <backend-container>

# Database
docker logs -f <db-container>
```

### Verificar uso de recursos

```bash
docker stats
```

## 🔄 Actualización

Para actualizar la aplicación:

1. Haz push de tus cambios al repositorio
2. En Dokploy, haz clic en **Redeploy**
3. Verifica los logs para asegurar que el despliegue fue exitoso

## 🔐 Seguridad

### Recomendaciones

1. **Nunca uses los valores por defecto** de `JWT_SECRET` y `SERVER_MASTER_KEY`
2. **Usa secretos fuertes** (al menos 32 caracteres aleatorios)
3. **Limita el acceso** al panel de Dokploy
4. **Usa HTTPS siempre** (configurado por defecto)
5. **Actualiza regularmente** las imágenes de Docker
6. **Monitorea los logs** para detectar actividad sospechosa

### Generar secretos seguros

```bash
# JWT_SECRET
openssl rand -base64 32

# SERVER_MASTER_KEY
python - <<'PY'
import base64, os
print(base64.urlsafe_b64encode(os.urandom(32)).decode('ascii'))
PY
```

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs de los contenedores
2. Verifica la sección de Troubleshooting
3. Consulta la documentación de Dokploy
4. Crea un issue en el repositorio

## ✅ Checklist de Despliegue

- [ ] Servidor con Dokploy instalado
- [ ] Dominios configurados y apuntando al servidor
- [ ] Puertos 80 y 443 abiertos
- [ ] Variables de entorno configuradas
- [ ] `JWT_SECRET` generado (no usar valor por defecto)
- [ ] `SERVER_MASTER_KEY` generado
- [ ] `FRONTEND_DOMAIN` y `BACKEND_DOMAIN` configurados
- [ ] `TRAEFIK_CERTRESOLVER` verificado
- [ ] Opción de configuración de dominios seleccionada (Labels o UI)
- [ ] Aplicación desplegada
- [ ] Healthchecks verificados
- [ ] Certificados SSL obtenidos
- [ ] Frontend accesible vía HTTPS
- [ ] Backend accesible vía HTTPS (si es necesario)
- [ ] Redirección HTTP → HTTPS funcionando
