"""
Manejadores globales de errores para la API.

Define el manejo centralizado de excepciones no capturadas
con respuestas consistentes y logging adecuado.
"""

import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.schemas.message import ErrorResponse, ValidationErrorResponse

# Configurar logging
logger = logging.getLogger(__name__)


def translate_validation_message(msg: str, error_type: str, field: str = "") -> str:
    """
    Traducir mensajes de validación de Pydantic al español.
    """
    # Traducciones específicas que aparecen frecuentemente
    direct_translations = {
        "Input should be 'user' or 'system'": "debe ser 'user' o 'system'",
        "String should have at least 1 character": "no puede estar vacío",
        "Field required": "es requerido",
        "field required": "es requerido"
    }
    
    # Buscar traducción directa primero
    if msg in direct_translations:
        return direct_translations[msg]
    
    # Lógica para diferentes tipos de errores
    if error_type == "enum":
        if "'user'" in msg and "'system'" in msg:
            return "debe ser 'user' o 'system'"
        return "no es válido"
    
    if error_type == "string_too_short":
        return "no puede estar vacío"
    
    if error_type == "missing":
        return "es requerido"
    
    if error_type == "value_error":
        return "tiene un valor inválido"
    
    # Fallback: intentar extraer información útil del mensaje
    if "Input should be" in msg:
        import re
        values = re.findall(r"'([^']*)'", msg)
        if values:
            if len(values) == 1:
                return f"debe ser '{values[0]}'"
            else:
                return "debe ser " + " o ".join(f"'{v}'" for v in values)
    
    # Si no hay traducción específica, dar un mensaje genérico
    return "no es válido"


def setup_error_handlers(app: FastAPI):
    """
    Configurar manejadores globales de errores para la aplicación.
    
    Args:
        app: Instancia de FastAPI
    """
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        Manejar errores de validación de Pydantic.
        
        Args:
            request: Request object
            exc: Excepción de validación de Pydantic
            
        Returns:
            JSONResponse: Respuesta formateada con detalles de validación
        """
        # Formatear errores de validación en un solo mensaje
        validation_errors = []
        for error in exc.errors():
            field = ".".join(str(x) for x in error["loc"])
            # Traducir mensaje al español
            translated_msg = translate_validation_message(
                error["msg"], 
                error["type"], 
                field
            )
            # Limpiar el nombre del campo (quitar 'body.')
            clean_field = field.replace("body.", "")
            validation_errors.append(f"El campo '{clean_field}' {translated_msg}")
        
        # Consolidar todos los errores en un solo mensaje
        details_message = "; ".join(validation_errors) if len(validation_errors) > 1 else validation_errors[0]
        
        logger.warning(f"Error de validación en {request.url}: {details_message}")
        
        response = ErrorResponse(
            status="error",
            error={
                "code": "INVALID_FORMAT",
                "message": "Formato de mensaje inválido",
                "details": details_message
            }
        )
        
        return JSONResponse(
            status_code=422,
            content=response.model_dump()
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """
        Manejar excepciones HTTP estándar.
        
        Args:
            request: Request object
            exc: Excepción HTTP
            
        Returns:
            JSONResponse: Respuesta formateada estándar
        """
        # Si ya es un detalle estructurado, devolverlo tal como está
        if isinstance(exc.detail, dict) and "status" in exc.detail:
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.detail
            )
        
        # Formatear respuesta estándar
        error_messages = {
            400: "Solicitud inválida",
            401: "No autorizado", 
            403: "Acceso prohibido",
            404: "Recurso no encontrado",
            405: "Método no permitido",
            409: "Conflicto de recursos",
            429: "Demasiadas solicitudes",
            500: "Error interno del servidor"
        }
        
        response = ErrorResponse(
            status="error",
            error={
                "code": f"HTTP_{exc.status_code}",
                "message": error_messages.get(exc.status_code, "Error del servidor"),
                "details": str(exc.detail) if exc.detail else None
            }
        )
        
        logger.error(f"HTTP {exc.status_code} en {request.url}: {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response.model_dump()
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        """
        Manejar errores de base de datos.
        
        Args:
            request: Request object
            exc: Excepción de SQLAlchemy
            
        Returns:
            JSONResponse: Respuesta de error de base de datos
        """
        logger.error(f"Error de base de datos en {request.url}: {str(exc)}")
        
        response = ErrorResponse(
            status="error",
            error={
                "code": "DATABASE_ERROR",
                "message": "Error de base de datos",
                "details": "Ha ocurrido un problema con la base de datos"
            }
        )
        
        return JSONResponse(
            status_code=500,
            content=response.model_dump()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """
        Manejar excepciones no capturadas.
        
        Args:
            request: Request object
            exc: Excepción general
            
        Returns:
            JSONResponse: Respuesta de error general
        """
        logger.error(f"Error no manejado en {request.url}: {str(exc)}", exc_info=True)
        
        response = ErrorResponse(
            status="error",
            error={
                "code": "INTERNAL_ERROR",
                "message": "Error interno del servidor",
                "details": "Ha ocurrido un error inesperado"
            }
        )
        
        return JSONResponse(
            status_code=500,
            content=response.model_dump()
        )


def configure_logging():
    """Configurar logging básico para la aplicación."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            # Opcional: agregar FileHandler para logs persistentes
            # logging.FileHandler("app.log")
        ]
    )
    
    # Reducir verbosidad de algunos loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)