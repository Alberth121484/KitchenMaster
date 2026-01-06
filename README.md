# KitchenMaster AI - Agente de Diseño de Cocinas Integrales

Sistema de diseño de cocinas integrales impulsado por IA con generación de imágenes usando Google Gemini.

## Características

- **Generación de diseños**: Crea prototipos visuales de cocinas basados en metros lineales y preferencias
- **Edición iterativa**: Modifica y mejora diseños existentes con memoria de conversación
- **Multi-usuario**: Sistema de autenticación con historial separado por usuario
- **Chat estilo ChatGPT**: Interfaz conversacional con artifacts visuales
- **Especificaciones técnicas**: Genera detalles de materiales, medidas y costos estimados

## Stack Tecnológico

### Backend
- **FastAPI** - Framework web async
- **LangGraph** - Orquestación del agente con memoria
- **Google Gemini** - Razonamiento (gemini-2.0-flash) e imágenes (Imagen 3)
- **PostgreSQL + pgvector** - Base de datos con embeddings
- **Redis** - Cache y sesiones

### Frontend
- **Next.js 14** - Framework React con App Router
- **shadcn/ui** - Componentes UI
- **Tailwind CSS** - Estilos
- **Zustand** - Estado global

## Requisitos Previos

- Docker y Docker Compose
- Google API Key con acceso a Gemini API
- Red de Traefik existente (para producción)

## Configuración

### 1. Variables de Entorno

```bash
cp .env.example .env
```

Edita `.env` con tus valores:

```env
# Requerido
GOOGLE_API_KEY=tu-api-key-de-google

# Seguridad (cambiar en producción)
JWT_SECRET=tu-secret-jwt-muy-largo-minimo-32-caracteres
POSTGRES_PASSWORD=contraseña-segura
```

### 2. Desarrollo Local

```bash
# Crear red de Docker si no existe
docker network create traefik-network

# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### 3. URLs de Acceso

- **Frontend**: http://cocinas.localhost
- **API**: http://api.cocinas.localhost
- **API Docs**: http://api.cocinas.localhost/docs

## Estructura del Proyecto

```
KitchenMaster/
├── backend/
│   ├── app/
│   │   ├── agent/           # Agente LangGraph
│   │   │   ├── kitchen_agent.py
│   │   │   ├── tools.py
│   │   │   └── prompts.py
│   │   ├── api/             # Endpoints FastAPI
│   │   ├── models/          # Modelos SQLAlchemy
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Lógica de negocio
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Pages Next.js
│   │   ├── components/      # Componentes React
│   │   ├── lib/             # Utilidades y API client
│   │   └── store/           # Estado Zustand
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── .env.example
```

## API Endpoints

### Autenticación
- `POST /api/v1/auth/register` - Registro de usuario
- `POST /api/v1/auth/login` - Inicio de sesión
- `POST /api/v1/auth/refresh` - Renovar token
- `GET /api/v1/auth/me` - Perfil del usuario

### Conversaciones
- `GET /api/v1/conversations` - Listar conversaciones
- `POST /api/v1/conversations` - Crear conversación
- `GET /api/v1/conversations/{id}` - Obtener conversación
- `DELETE /api/v1/conversations/{id}` - Eliminar conversación

### Chat
- `POST /api/v1/chat` - Enviar mensaje al agente
- `WS /api/v1/chat/ws/{conversation_id}` - WebSocket para streaming
- `GET /api/v1/chat/history/{id}/designs` - Historial de diseños

## Uso del Agente

El agente entiende solicitudes en español. Ejemplos:

```
"Quiero una cocina moderna de 4 metros lineales en forma de L"

"Diseña una cocina rústica de 3 metros con madera de roble"

"Cambia el color de los gabinetes a blanco"

"Agrega una isla central al diseño"
```

## Despliegue en Producción (Portainer + Traefik)

### 1. Configurar Stack en Portainer

1. Crear nuevo Stack
2. Copiar contenido de `docker-compose.yml`
3. Agregar variables de entorno en Portainer
4. Ajustar labels de Traefik con tu dominio real

### 2. Labels de Traefik para HTTPS

```yaml
labels:
  - "traefik.http.routers.kitchenmaster-api.rule=Host(`api.tudominio.com`)"
  - "traefik.http.routers.kitchenmaster-api.tls.certresolver=letsencrypt"
```

### 3. Volúmenes Persistentes

Asegúrate de que los volúmenes de PostgreSQL y Redis estén configurados para persistencia.

## Solución de Problemas

### Error de conexión a la base de datos
```bash
docker-compose logs postgres
docker-compose exec postgres psql -U kitchenmaster -c "\dt"
```

### Error de Gemini API
- Verifica que tu API Key tenga acceso a Gemini e Imagen 3
- Revisa los límites de rate en Google Cloud Console

### Frontend no carga
```bash
docker-compose logs frontend
docker-compose exec frontend npm run build
```

## Licencia

MIT License - Uso libre para proyectos personales y comerciales.
