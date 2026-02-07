"""
Archivo principal de la aplicación FastAPI para el Chat Message API.

Este módulo inicializa la aplicación FastAPI, configura middleware,
rutas y manejadores de errores para la API de mensajes de chat.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
from datetime import datetime
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

from app.database.connection import create_tables
from app.models.message import Message
from app.controllers.message_controller import router as message_router
from app.error_handlers import setup_error_handlers, configure_logging

# Configurar el sistema de logs de la aplicación
configure_logging()

# Crear las tablas de la base de datos solo si no estamos en modo testing
if not os.getenv("TESTING", "false").lower() == "true":
    create_tables()

def custom_json_encoder(obj):
    """
    Codificador personalizado para objetos datetime en JSON.

    Convierte objetos datetime a formato ISO 8601 con sufijo 'Z' para UTC.

    Args:
        obj: Objeto a codificar

    Returns:
        str: Fecha en formato ISO 8601

    Raises:
        TypeError: Si el objeto no es serializable a JSON
    """
    if isinstance(obj, datetime):
        return obj.isoformat() + ('Z' if obj.tzinfo is None else '')
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

# Configuración de la aplicación desde variables de entorno
app_name = os.getenv("APP_NAME", "Chat Message API")
app_version = os.getenv("APP_VERSION", "1.0.0")
app_description = os.getenv("APP_DESCRIPTION", "API RESTful para procesamiento de mensajes de chat")

# Crear instancia de la aplicación FastAPI con toda la configuración
app = FastAPI(
    title=app_name,
    version=app_version,
    description=app_description,
    docs_url="/docs",  # Documentación Swagger UI
    redoc_url=None,  # Deshabilitamos para configurarlo manualmente
    json_encoders={
        # Codificador personalizado para fechas en formato ISO 8601
        datetime: lambda v: v.isoformat() + ('Z' if v.tzinfo is None else '')
    },
    # Etiquetas para organizar los endpoints en la documentación
    openapi_tags=[
        {
            "name": "messages",
            "description": "Operaciones con mensajes de chat. Incluye creación, "
                         "consulta con paginación, filtrado y estadísticas."
        },
        {
            "name": "health",
            "description": "Endpoints de verificación de salud y estado de la API."
        }
    ]
)

# Configurar middleware CORS para permitir peticiones desde cualquier origen
# NOTA: En producción, deberías especificar orígenes permitidos específicos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas las URLs de origen
    allow_credentials=True,  # Permite el envío de cookies y credenciales
    allow_methods=["*"],  # Permite todos los métodos HTTP (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos los headers
)

# Configurar los manejadores de errores globales
setup_error_handlers(app)

# Registrar las rutas del controlador de mensajes bajo el prefijo /api
app.include_router(message_router, prefix="/api", tags=["messages"])

@app.get("/health", tags=["health"])
async def health_check():
    """
    Endpoint para verificar el estado de salud de la API.

    Returns:
        dict: Información del estado de la API incluyendo:
            - status: Estado general (ok)
            - message: Mensaje descriptivo
            - version: Versión de la API
            - database: Estado de la conexión a base de datos
    """
    return {
        "status": "ok",
        "message": "Chat API is running",
        "version": app_version,
        "database": "connected"
    }

@app.get("/", tags=["health"])
async def root():
    """
    Endpoint raíz que proporciona información general de la API.

    Returns:
        dict: Información de bienvenida y lista de endpoints disponibles
    """
    return {
        "message": "Bienvenido a Chat Message API",
        "version": app_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "endpoints": {
            "create_message": "POST /api/messages",
            "get_messages": "GET /api/messages/{session_id}",
            "get_message_by_id": "GET /api/messages/id/{message_id}",
            "session_stats": "GET /api/messages/{session_id}/stats"
        }
    }

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """
    Endpoint para documentación ReDoc con CDN estable.

    Usa un CDN alternativo que garantiza disponibilidad.
    """
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app_name} - ReDoc",
        redoc_js_url="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js",
    )

if __name__ == "__main__":
    # Iniciar el servidor solo si se ejecuta directamente (no en tests)
    import uvicorn

    # Obtener configuración desde variables de entorno
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", 8000))
    debug = os.getenv("API_DEBUG", "true").lower() == "true"

    # Ejecutar servidor con recarga automática si está en modo debug
    uvicorn.run("main:app", host=host, port=port, reload=debug)