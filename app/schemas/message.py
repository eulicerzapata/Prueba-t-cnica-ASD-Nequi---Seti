"""
Esquemas Pydantic para validación de mensajes de chat.

Define los modelos de entrada y salida para la API REST.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class SenderEnum(str, Enum):
    """Enum para tipos de sender válidos."""
    USER = "user"
    SYSTEM = "system"


class MessageMetadata(BaseModel):
    """Metadatos de procesamiento del mensaje."""
    word_count: int = Field(ge=0, description="Número de palabras en el mensaje")
    character_count: int = Field(ge=0, description="Número de caracteres en el mensaje")
    processed_at: datetime = Field(description="Timestamp de cuando se procesó el mensaje")

    class Config:
        # Serializar fechas en formato ISO
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v.tzinfo is None else v.isoformat()
        }


class MessageCreate(BaseModel):
    """Esquema para crear un nuevo mensaje (POST request)."""
    
    session_id: str = Field(
        min_length=1, 
        max_length=255,
        description="Identificador de la sesión de chat"
    )
    content: str = Field(
        min_length=1,
        description="Contenido del mensaje"
    )
    sender: SenderEnum = Field(
        description="Remitente del mensaje: 'user' o 'system'"
    )
    # Campos opcionales que el cliente puede enviar (pero se ignorarán si se generan automáticamente)
    message_id: Optional[str] = Field(None, description="ID del mensaje (opcional, se genera automáticamente si no se proporciona)")
    timestamp: Optional[datetime] = Field(None, description="Timestamp del mensaje (opcional, se genera automáticamente si no se proporciona)")

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """Validar que el contenido no esté vacío después de strip."""
        if not v.strip():
            raise ValueError('El contenido no puede estar vacío')
        return v.strip()

    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v):
        """Validar que el session_id no contenga solo espacios."""
        if not v.strip():
            raise ValueError('El session_id no puede estar vacío')
        return v.strip()

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "title": "Ejemplo básico (recomendado)",
                    "summary": "Solo campos requeridos - el servidor genera automáticamente message_id y timestamp",
                    "value": {
                        "session_id": "session-abcdef",
                        "content": "Hola, ¿cómo puedo ayudarte hoy?",
                        "sender": "user"
                    }
                },
                {
                    "title": "Ejemplo completo (opcional)",
                    "summary": "Incluye todos los campos - útil si necesitas IDs específicos",
                    "value": {
                        "message_id": "msg-123456",
                        "session_id": "session-abcdef", 
                        "content": "Hola, ¿cómo puedo ayudarte hoy?",
                        "timestamp": "2023-06-15T14:30:00Z",
                        "sender": "system"
                    }
                }
            ]
        }


class MessageResponse(BaseModel):
    """Esquema para respuesta de mensaje (API response)."""
    
    message_id: str
    session_id: str
    content: str
    timestamp: datetime
    sender: SenderEnum
    metadata: MessageMetadata
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Para convertir desde modelos SQLAlchemy
        # Serializar fechas en formato ISO
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v.tzinfo is None else v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "message_id": "msg-123456",
                "session_id": "session-abcdef",
                "content": "Hola, ¿cómo puedo ayudarte hoy?",
                "timestamp": "2023-06-15T14:30:00Z",
                "sender": "system",
                "metadata": {
                    "word_count": 6,
                    "character_count": 32,
                    "processed_at": "2023-06-15T14:30:01Z"
                },
                "created_at": "2023-06-15T14:30:01Z",
                "updated_at": "2023-06-15T14:30:01Z"
            }
        }


class MessageListResponse(BaseModel):
    """Esquema para respuesta de lista de mensajes con paginación."""
    
    messages: list[MessageResponse]
    total: int = Field(ge=0, description="Total de mensajes en la sesión")
    limit: int = Field(ge=1, description="Límite de mensajes por página")
    offset: int = Field(ge=0, description="Número de mensajes saltados")
    has_more: bool = Field(description="Indica si hay más mensajes disponibles")

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {
                        "message_id": "msg-123456",
                        "session_id": "session-abcdef",
                        "content": "Hola, ¿cómo puedo ayudarte hoy?",
                        "timestamp": "2023-06-15T14:30:00Z",
                        "sender": "system",
                        "metadata": {
                            "word_count": 6,
                            "character_count": 32,
                            "processed_at": "2023-06-15T14:30:01Z"
                        },
                        "created_at": "2023-06-15T14:30:01Z",
                        "updated_at": "2023-06-15T14:30:01Z"
                    }
                ],
                "total": 1,
                "limit": 50,
                "offset": 0,
                "has_more": False
            }
        }


class MessageCreateResponse(BaseModel):
    """Esquema simplificado para respuesta de creación de mensaje."""
    
    message_id: str
    session_id: str
    content: str
    timestamp: datetime
    sender: SenderEnum
    metadata: MessageMetadata

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v.tzinfo is None else v.isoformat()
        }


class SuccessResponse(BaseModel):
    """Esquema para respuestas exitosas estándar."""
    
    status: Literal["success"] = "success"
    data: MessageCreateResponse

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "data": {
                    "message_id": "msg-123456",
                    "session_id": "session-abcdef",
                    "content": "Hola, ¿cómo puedo ayudarte hoy?",
                    "timestamp": "2023-06-15T14:30:00Z",
                    "sender": "system",
                    "metadata": {
                        "word_count": 6,
                        "character_count": 32,
                        "processed_at": "2023-06-15T14:30:01Z"
                    }
                }
            }
        }


class ErrorDetail(BaseModel):
    """Detalle de un error específico."""
    
    code: str = Field(description="Código de error específico")
    message: str = Field(description="Mensaje descriptivo del error")
    details: Optional[str] = Field(default=None, description="Detalles adicionales del error")


class ErrorResponse(BaseModel):
    """Esquema para respuestas de error estándar."""
    
    status: Literal["error"] = "error"
    error: ErrorDetail

    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "error": {
                    "code": "INVALID_FORMAT",
                    "message": "Formato de mensaje inválido",
                    "details": "El campo 'sender' debe ser 'user' o 'system'"
                }
            }
        }


class ValidationErrorResponse(BaseModel):
    """Esquema para errores de validación con detalles específicos."""
    
    status: Literal["error"] = "error"
    error: ErrorDetail
    validation_errors: list[dict] = Field(description="Lista detallada de errores de validación")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Error de validación en los datos de entrada"
                },
                "validation_errors": [
                    {
                        "field": "sender",
                        "message": "El valor debe ser 'user' o 'system'",
                        "received_value": "invalid"
                    }
                ]
            }
        }