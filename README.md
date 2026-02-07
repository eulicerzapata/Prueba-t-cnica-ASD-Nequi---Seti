# Chat Message API

API RESTful profesional para procesamiento de mensajes de chat desarrollada con FastAPI.

Esta guía proporciona instrucciones step-by-step para clonar, configurar y ejecutar el proyecto. Se recomienda Docker como método principal de despliegue, con instrucciones alternativas para entornos virtuales locales.

## Resumen de opciones

- **Recomendado:** Docker Compose para ejecución y testing
- **Alternativa:** Entorno virtual Python con uvicorn
- **Documentación:** Swagger UI disponible en http://localhost:8000/docs

---

## Paso 1: Clonar el repositorio

Abra una terminal y ejecute:

```bash
git clone <repository-url>
cd chat-api
```

Sustituye `<repository-url>` por la URL real del repositorio.

## Importante: crear `.env` desde `.env.example` (OBLIGATORIO)

El repositorio incluye un archivo de ejemplo de variables de entorno `.env.example`. Es obligatorio crear una copia local llamada `.env` antes de ejecutar la aplicación o los tests.

Windows:

```powershell
copy .env.example .env
```

Linux / macOS:

```bash
cp .env.example .env
```

Luego edita `.env` para ajustar valores sensibles (credenciales, URLs, etc.). Asegúrate de no subir `.env` al repositorio: el proyecto ya ignora `.env` mediante `.gitignore`.

## Paso 2: Ejecutar con Docker (recomendado)

Ejecute los siguientes comandos en orden:

```bash
# Construir y ejecutar en segundo plano
docker compose up --build -d

# Verificar estado de los servicios
docker compose ps

# Ver logs en tiempo real (opcional)
docker compose logs -f
```

La API estará disponible en:
- API: http://localhost:8000
- Documentación: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Para detener los servicios:

```bash
docker compose down
```

## Paso 3: Alternativa - Ejecución local con entorno virtual

Si prefiere no usar Docker, siga estos pasos:

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

La aplicación estará disponible en http://localhost:8000/docs

---

## Paso 4: Ejecutar tests

**Con Docker Compose (recomendado):**

Reemplace `<service>` por el nombre del servicio definido en `docker-compose.yml`:

```bash
# Ejecutar todos los tests
docker compose exec <service> pytest

# Ejecutar tests con reporte de cobertura
docker compose exec <service> pytest --cov=app --cov-report=html --cov-report=term

# Ejecutar test específico
docker compose exec <service> pytest tests/unit/test_message_service_simple.py -v
```

**Ejecución local:**
```bash
pytest
pytest --cov=app --cov-report=html --cov-report=term
```

## Paso 5: Acceder a la documentación

Una vez que la aplicación esté ejecutándose, acceda a:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **API Root:** http://localhost:8000

**Abrir desde terminal:**
```bash
# Windows
start http://localhost:8000/docs

# Linux
xdg-open http://localhost:8000/docs

# macOS
open http://localhost:8000/docs
```

## Comandos de referencia rápida

```bash
# Docker - Operaciones principales
docker compose up --build -d    # Construir y ejecutar
docker compose ps               # Ver estado
docker compose logs -f          # Ver logs
docker compose down             # Detener servicios

# Tests
docker compose exec <service> pytest                    # Todos los tests
docker compose exec <service> pytest --cov=app         # Con cobertura

# Ejecución local
uvicorn app.main:app --reload   # Servidor desarrollo
pytest                          # Tests locales
```

## Solución de problemas comunes

- **Puerto ocupado:** Modifique el puerto en `docker-compose.yml` o use `--port 8080` con uvicorn
- **Servicio no encontrado:** Verifique el nombre del servicio con `docker compose ps`
- **Permisos de base de datos:** Asegúrese de tener permisos de escritura en el directorio del proyecto

---

## Referencia de API y documentación técnica

## Endpoints Principales

### 1. Crear Mensaje

```bash
POST http://localhost:8000/api/messages
```

**Ejemplo con curl:**
```bash
curl -X POST "http://localhost:8000/api/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-123",
    "content": "Hola, ¿cómo estás?",
    "sender": "user"
  }'
```

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "message_id": "uuid-generado",
    "session_id": "session-123",
    "content": "Hola, ¿cómo estás?",
    "sender": "user",
    "timestamp": "2024-01-15T10:30:00Z",
    "metadata": {
      "word_count": 3,
      "character_count": 18,
      "processed_at": "2024-01-15T10:30:00Z"
    }
  }
}
```

### 2. Obtener Mensajes por Sesión

```bash
GET http://localhost:8000/api/messages/{session_id}?limit=10&offset=0&sender=user
```

**Ejemplo con curl:**
```bash
curl "http://localhost:8000/api/messages/session-123?limit=10&offset=0"
```

### 3. Obtener Estadísticas de Sesión

```bash
GET http://localhost:8000/api/messages/{session_id}/stats
```

**Ejemplo con curl:**
```bash
curl "http://localhost:8000/api/messages/session-123/stats"
```

### 4. Obtener Mensaje por ID

```bash
GET http://localhost:8000/api/messages/id/{message_id}
```

### 5. Health Check

```bash
GET http://localhost:8000/health
```

## Estructura del Proyecto

```
chat-api/
├── app/
│   ├── controllers/          # Controladores de endpoints
│   │   └── message_controller.py
│   ├── services/            # Lógica de negocio
│   │   ├── message_service.py
│   │   ├── config.py
│   │   └── exceptions.py
│   ├── repositories/        # Acceso a datos
│   │   ├── message_repository.py
│   │   ├── utils.py
│   │   └── exceptions.py
│   ├── models/             # Modelos de BD
│   │   └── message.py
│   ├── schemas/            # Esquemas Pydantic
│   │   ├── message.py
│   │   └── query_params.py
│   ├── database/           # Configuración de BD
│   │   └── connection.py
│   ├── utils/              # Utilidades
│   │   └── content_filter.py
│   ├── error_handlers.py   # Manejo de errores
│   ├── exceptions.py       # Excepciones custom
│   └── main.py            # Punto de entrada
├── tests/
│   ├── unit/              # Tests unitarios
│   ├── integration/       # Tests de integración
│   ├── fixtures/          # Datos de prueba
│   └── conftest.py       # Configuración de pytest
├── .env                   # Variables de entorno
├── .gitignore
├── requirements.txt       # Dependencias
├── pytest.ini            # Configuración de pytest
└── README.md             # Este archivo
```

## Tecnologías

- **FastAPI 0.104.1** - Framework web moderno y rápido
- **SQLAlchemy 2.0.23** - ORM para manejo de base de datos
- **SQLite** - Base de datos embebida
- **Pydantic 2.5.0** - Validación de datos
- **Uvicorn 0.24.0** - Servidor ASGI
- **Pytest 7.4.3** - Framework de testing
- **Python-dotenv 1.0.0** - Gestión de variables de entorno

## Comandos Útiles Rápidos

```bash
# Instalar todo
pip install -r requirements.txt

# Ejecutar aplicación
uvicorn app.main:app --reload

# Ejecutar tests
pytest

# Ver cobertura
pytest --cov=app --cov-report=term

# Abrir docs (Windows)
start http://localhost:8000/docs

# Limpiar cache de Python (Linux/Mac)
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Ver estructura del proyecto (Linux/Mac)
tree -I 'venv|__pycache__|*.pyc|htmlcov'
```

## Solución de Problemas Comunes

### Error: "No module named 'app'"

**Solución:** Verifique que esté en el directorio `chat-api` y que el entorno virtual esté activado.

### Error: "Address already in use"

**Solución:** El puerto 8000 está ocupado. Utilice otro puerto:
```bash
uvicorn app.main:app --reload --port 8080
```

### Error al importar módulos

**Solución:** Reinstale las dependencias:
```bash
pip install --upgrade -r requirements.txt
```

### Base de datos no se crea

**Solución:** Verifique los permisos de escritura en la carpeta del proyecto.

## Licencia

Este proyecto está bajo la Licencia MIT.