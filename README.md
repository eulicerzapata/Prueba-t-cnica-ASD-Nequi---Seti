# 💬 Chat Message API

API RESTful profesional para procesamiento de mensajes de chat desarrollada con FastAPI.

---

## ⚡ Inicio Rápido (5 minutos)

Para iniciar el proyecto rápidamente, siga los siguientes pasos:

### 1. Verificar instalación de Python 3.10+
```bash
python --version
```

### 2. Navegar a la carpeta del proyecto
```bash
cd chat-api
```

### 3. Crear y activar el entorno virtual

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Instalar las dependencias
```bash
pip install -r requirements.txt
```

### 5. Ejecutar la aplicación
```bash
uvicorn app.main:app --reload
```

### 6. Acceder a la documentación

**Windows:**
```bash
start http://localhost:8000/docs
```

**Linux:**
```bash
xdg-open http://localhost:8000/docs
```

**Mac:**
```bash
open http://localhost:8000/docs
```

La API estará disponible en http://localhost:8000

---

## 📋 Tabla de Contenidos

- [⚡ Inicio Rápido](#-inicio-rápido-5-minutos)
- [Características](#-características)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación Paso a Paso](#-instalación-paso-a-paso)
- [Configuración](#-configuración)
- [Ejecución de la Aplicación](#-ejecución-de-la-aplicación)
- [Acceder a la Documentación](#-acceder-a-la-documentación)
- [Ejecutar Tests](#-ejecutar-tests)
- [Endpoints Principales](#-endpoints-principales)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Tecnologías](#-tecnologías)
- [Comandos Útiles](#-comandos-útiles-rápidos)
- [Solución de Problemas](#-solución-de-problemas-comunes)

## ✨ Características

- ✅ Recepción y validación de mensajes de chat
- ✅ Procesamiento automático de contenido (conteo de palabras, caracteres, etc.)
- ✅ Filtrado de contenido inapropiado configurable
- ✅ Rate limiting (límites por minuto y por hora)
- ✅ Almacenamiento en base de datos SQLite
- ✅ Recuperación de mensajes con paginación
- ✅ Filtrado por tipo de remitente (user/system)
- ✅ Estadísticas de sesión
- ✅ Manejo robusto de errores con mensajes en español
- ✅ Documentación automática interactiva (Swagger UI y ReDoc)
- ✅ Logging estructurado
- ✅ Cobertura de tests >90%

## 🔧 Requisitos Previos

Antes de comenzar, verifique que tenga instalado lo siguiente:

### 1. Python 3.10 o superior

**Verificar si Python está instalado:**
```bash
python --version
```

**Si no está instalado, descárgalo desde:**
- Windows/Mac: https://www.python.org/downloads/
- Linux (Ubuntu/Debian):
  ```bash
  sudo apt update
  sudo apt install python3.10 python3.10-venv python3-pip
  ```

### 2. Git

**Verificar si Git está instalado:**
```bash
git --version
```

**Si no está instalado, descárgalo desde:** https://git-scm.com/downloads

## 📦 Instalación Paso a Paso

### Paso 1: Clonar el repositorio

```bash
git clone <repository-url>
cd chat-api
```

### Paso 2: Crear entorno virtual

**En Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**En Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

Se mostrará `(venv)` al inicio de la terminal cuando esté activado.

### Paso 3: Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 4: Verificar instalación

```bash
python -c "import fastapi; print('FastAPI instalado correctamente')"
```

## ⚙️ Configuración

### Configurar archivo .env (Opcional)

El proyecto incluye un archivo `.env` con valores por defecto. Es posible personalizarlo según las necesidades:

```bash
# Configuración de la aplicación
APP_NAME=Chat Message API
APP_VERSION=1.0.0
APP_DESCRIPTION=API RESTful para procesamiento de mensajes de chat

# Configuración del servidor
API_HOST=127.0.0.1
API_PORT=8000
API_DEBUG=true

# Base de datos
DATABASE_URL=sqlite:///./chat_messages.db

# Filtro de contenido (palabras separadas por comas)
PROFANITY_WORDS=spam,malo,prohibido,ofensivo

# Límites de tasa
MAX_CONTENT_LENGTH=5000
MAX_HOURLY_MESSAGES=100
MAX_MESSAGES_PER_MINUTE=10
```

## 🚀 Ejecución de la Aplicación

### Método 1: Con Uvicorn directamente (Recomendado para desarrollo)

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Método 2: Con Python directamente

```bash
python -m app.main
```

### Método 3: Con hot reload y configuración personalizada

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

**Salida esperada:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## 📚 Acceder a la Documentación

### Opción 1: Abrir manualmente en el navegador

Una vez que la aplicación esté corriendo, abre tu navegador en:

- **Swagger UI (Interactiva):** http://localhost:8000/docs
- **ReDoc (Alternativa):** http://localhost:8000/redoc
- **API Root:** http://localhost:8000/

### Opción 2: Abrir automáticamente desde terminal

**En Windows:**
```bash
start http://localhost:8000/docs
```

**En Linux:**
```bash
xdg-open http://localhost:8000/docs
```

**En Mac:**
```bash
open http://localhost:8000/docs
```

### Opción 3: Abrir múltiples URLs

**En Windows:**
```bash
start http://localhost:8000/docs && start http://localhost:8000/redoc && start http://localhost:8000/
```

**En Linux:**
```bash
xdg-open http://localhost:8000/docs && xdg-open http://localhost:8000/redoc
```

**En Mac:**
```bash
open http://localhost:8000/docs && open http://localhost:8000/redoc
```

## 🧪 Ejecutar Tests

### Tests completos con cobertura

```bash
# Ejecutar todos los tests
pytest

# Con cobertura de código
pytest --cov=app --cov-report=html --cov-report=term

# Ver reporte HTML de cobertura
# Windows:
start htmlcov/index.html
# Linux:
xdg-open htmlcov/index.html
# Mac:
open htmlcov/index.html
```

### Tests específicos

```bash
# Solo tests unitarios
pytest tests/unit/ -v

# Solo tests de integración
pytest tests/integration/ -v

# Test específico
pytest tests/unit/test_message_service_simple.py -v

# Tests con marcadores
pytest -m unit  # Solo unitarios
pytest -m integration  # Solo integración
```

### Tests con salida detallada

```bash
# Muy verboso con prints
pytest -vv -s

# Mostrar 10 tests más lentos
pytest --durations=10

# Fallar en el primer error
pytest -x
```

## 📡 Endpoints Principales

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

## 📁 Estructura del Proyecto

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

## 🛠️ Tecnologías

- **FastAPI 0.104.1** - Framework web moderno y rápido
- **SQLAlchemy 2.0.23** - ORM para manejo de base de datos
- **SQLite** - Base de datos embebida
- **Pydantic 2.5.0** - Validación de datos
- **Uvicorn 0.24.0** - Servidor ASGI
- **Pytest 7.4.3** - Framework de testing
- **Python-dotenv 1.0.0** - Gestión de variables de entorno

## 🔍 Comandos Útiles Rápidos

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

# Limpiar cache de Python
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Ver estructura del proyecto
tree -I 'venv|__pycache__|*.pyc|htmlcov'  # Linux/Mac
```

## ⚡ Solución de Problemas Comunes

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

## 📝 Licencia

Este proyecto está bajo la Licencia MIT.