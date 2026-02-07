"""
Controlador de endpoints para mensajes de chat.

Define los endpoints REST para manejo de mensajes con validación,
procesamiento y respuestas estructuradas.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database.connection import get_database_session
from app.schemas.message import (
    MessageCreate, 
    MessageResponse, 
    MessageCreateResponse,
    MessageListResponse,
    SuccessResponse,
    SenderEnum
)
from app.schemas.query_params import MessageQueryParams
from app.services import create_message_service
from app.services.exceptions import (
    InappropriateContentError,
    MessageValidationError,
    RateLimitExceededError,
    MessageProcessingError
)
from app.repositories.exceptions import MessageAlreadyExistsError

# Crear router para endpoints de mensajes
router = APIRouter()


@router.post(
    "/messages",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo mensaje de chat",
    description="Crea un nuevo mensaje de chat con validación automática, "
                "filtrado de contenido y generación de metadatos.",
    responses={
        201: {
            "description": "Mensaje creado exitosamente",
            "model": SuccessResponse
        },
        400: {
            "description": "Error de validación o contenido inapropiado",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Error de validación en los datos de entrada",
                            "details": "El contenido no puede estar vacío"
                        }
                    }
                }
            }
        },
        409: {
            "description": "Mensaje con ID duplicado",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error", 
                        "error": {
                            "code": "DUPLICATE_MESSAGE",
                            "message": "Ya existe un mensaje con ese ID",
                            "details": "message_id debe ser único"
                        }
                    }
                }
            }
        },
        429: {
            "description": "Límite de tasa excedido",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED", 
                            "message": "Se ha excedido el límite de mensajes",
                            "details": "Máximo 10 mensajes por minuto"
                        }
                    }
                }
            }
        }
    }
)
async def create_message(
    message_data: MessageCreate,
    db: Session = Depends(get_database_session)
):
    """
    Crear un nuevo mensaje de chat.
    
    Este endpoint:
    1. Valida los datos de entrada usando Pydantic
    2. Aplica filtros de contenido inapropiado
    3. Genera metadatos automáticamente (conteo de palabras, etc.)
    4. Almacena el mensaje en la base de datos
    5. Retorna el mensaje creado con todos los metadatos
    
    Args:
        message_data: Datos del mensaje validados por Pydantic
        db: Sesión de base de datos (inyectada automáticamente)
        
    Returns:
        SuccessResponse: Respuesta con el mensaje creado y metadatos
        
    Raises:
        HTTPException: Para diferentes tipos de errores (400, 409, 429)
    """
    try:
        # Crear servicio de mensajes con configuración
        message_service = create_message_service(db)
        
        # Procesar y crear mensaje
        created_message = await message_service.create_message(message_data)
        
        # Retornar respuesta exitosa simplificada
        return SuccessResponse(
            status="success",
            data=created_message
        )
        
    except InappropriateContentError as e:
        # Contenido inapropiado detectado
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "error": {
                    "code": "INAPPROPRIATE_CONTENT",
                    "message": "Contenido inapropiado detectado",
                    "details": f"Palabras prohibidas: {', '.join(e.inappropriate_words)}"
                }
            }
        )
        
    except MessageValidationError as e:
        # Errores de validación de negocio
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Error de validación en los datos",
                    "details": "; ".join(e.validation_errors)
                }
            }
        )
        
    except MessageAlreadyExistsError as e:
        # ID de mensaje duplicado
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "status": "error", 
                "error": {
                    "code": "DUPLICATE_MESSAGE",
                    "message": "Ya existe un mensaje con ese ID",
                    "details": f"message_id '{e.message_id}' ya está en uso"
                }
            }
        )
        
    except RateLimitExceededError as e:
        # Límites de tasa excedidos
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "status": "error",
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Límite de {e.limit_type} excedido",
                    "details": f"Enviados {e.current_count} de {e.max_allowed} permitidos"
                }
            }
        )
        
    except MessageProcessingError as e:
        # Errores durante procesamiento
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "error": {
                    "code": "PROCESSING_ERROR",
                    "message": f"Error durante {e.operation}",
                    "details": str(e.original_error) if e.original_error else "Error interno del servidor"
                }
            }
        )
        
    except Exception as e:
        # Errores inesperados
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "error": {
                    "code": "INTERNAL_ERROR", 
                    "message": "Error interno del servidor",
                    "details": "Ha ocurrido un error inesperado"
                }
            }
        )


@router.get(
    "/messages/{session_id}",
    response_model=MessageListResponse,
    summary="Obtener mensajes por sesión",
    description="Recupera todos los mensajes de una sesión específica con "
                "soporte para paginación y filtrado por remitente.",
    responses={
        200: {
            "description": "Mensajes recuperados exitosamente",
            "model": MessageListResponse
        },
        400: {
            "description": "Parámetros de consulta inválidos",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "error": {
                            "code": "INVALID_PARAMETERS",
                            "message": "Parámetros de consulta inválidos",
                            "details": "limit debe ser entre 1 y 100"
                        }
                    }
                }
            }
        },
        404: {
            "description": "Sesión no encontrada",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "error": {
                            "code": "SESSION_NOT_FOUND", 
                            "message": "Sesión no encontrada",
                            "details": "No existen mensajes para esta sesión"
                        }
                    }
                }
            }
        }
    }
)
async def get_messages_by_session(
    session_id: str,
    limit: int = Query(50, ge=1, le=100, description="Límite de mensajes por página (1-100)"),
    offset: int = Query(0, ge=0, description="Número de mensajes a saltar para paginación"),
    sender: Optional[SenderEnum] = Query(None, description="Filtrar por tipo de remitente"),
    db: Session = Depends(get_database_session)
):
    """
    Obtener mensajes de una sesión específica.
    
    Este endpoint:
    1. Valida los parámetros de consulta
    2. Recupera mensajes con paginación
    3. Aplica filtros opcionales por remitente
    4. Retorna lista paginada con metadatos de paginación
    
    Args:
        session_id: ID único de la sesión de chat  
        limit: Número máximo de mensajes a retornar (1-100)
        offset: Número de mensajes a saltar para paginación
        sender: Filtro opcional por tipo de remitente ('user' o 'system')
        db: Sesión de base de datos (inyectada automáticamente)
        
    Returns:
        MessageListResponse: Lista paginada de mensajes con metadatos
        
    Raises:
        HTTPException: Para errores de parámetros o sesión no encontrada
    """
    try:
        # Validar session_id
        if not session_id or not session_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "error": {
                        "code": "INVALID_SESSION_ID",
                        "message": "session_id inválido",
                        "details": "session_id no puede estar vacío"
                    }
                }
            )
        
        # Crear servicio de mensajes
        message_service = create_message_service(db)
        
        # Obtener mensajes con paginación
        messages_response = message_service.get_messages_by_session(
            session_id=session_id.strip(),
            limit=limit,
            offset=offset,
            sender=sender
        )
        
        # Si no hay mensajes y es la primera página, podría ser sesión no encontrada
        if messages_response.total == 0 and offset == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "error",
                    "error": {
                        "code": "SESSION_NOT_FOUND",
                        "message": "Sesión no encontrada", 
                        "details": f"No se encontraron mensajes para la sesión '{session_id}'"
                    }
                }
            )
        
        return messages_response
        
    except HTTPException:
        # Re-lanzar HTTPExceptions ya formateadas
        raise
        
    except Exception as e:
        # Errores inesperados 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Error interno del servidor",
                    "details": "Error al recuperar mensajes"
                }
            }
        )


@router.get(
    "/messages/{session_id}/stats",
    summary="Estadísticas de sesión",
    description="Obtiene estadísticas completas de una sesión de chat incluyendo "
                "conteos, métricas de palabras y actividad temporal."
)
async def get_session_stats(
    session_id: str,
    db: Session = Depends(get_database_session)
):
    """
    Obtener estadísticas de una sesión de chat.
    
    Returns:
        dict: Estadísticas detalladas de la sesión
    """
    try:
        # Validar session_id
        if not session_id or not session_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "error": {
                        "code": "INVALID_SESSION_ID", 
                        "message": "session_id inválido",
                        "details": "session_id no puede estar vacío"
                    }
                }
            )
        
        # Crear servicio y obtener estadísticas
        message_service = create_message_service(db)
        stats = message_service.get_session_statistics(session_id.strip())
        
        return {
            "status": "success",
            "data": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Error al obtener estadísticas",
                    "details": "Error interno del servidor"
                }
            }
        )


@router.get(
    "/messages/id/{message_id}",
    response_model=MessageResponse,
    summary="Obtener mensaje por ID",
    description="Recupera un mensaje específico usando su ID único."
)
async def get_message_by_id(
    message_id: str,
    db: Session = Depends(get_database_session)
):
    """
    Obtener un mensaje específico por su ID.
    
    Args:
        message_id: ID único del mensaje
        db: Sesión de base de datos
        
    Returns:
        MessageResponse: Mensaje encontrado
        
    Raises:
        HTTPException: Si no se encuentra el mensaje
    """
    try:
        # Validar message_id
        if not message_id or not message_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "error": {
                        "code": "INVALID_MESSAGE_ID",
                        "message": "message_id inválido", 
                        "details": "message_id no puede estar vacío"
                    }
                }
            )
        
        # Crear servicio y buscar mensaje
        message_service = create_message_service(db)
        message = message_service.get_message_by_id(message_id.strip())
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "status": "error",
                    "error": {
                        "code": "MESSAGE_NOT_FOUND",
                        "message": "Mensaje no encontrado",
                        "details": f"No existe un mensaje con ID '{message_id}'"
                    }
                }
            )
        
        return message
        
    except HTTPException:
        raise
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error", 
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Error al buscar mensaje",
                    "details": "Error interno del servidor"
                }
            }
        )