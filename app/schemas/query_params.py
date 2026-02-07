"""
Esquemas para parámetros de consulta (query parameters).

Define los parámetros que se pueden usar en los endpoints GET.
"""

from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.message import SenderEnum


class MessageQueryParams(BaseModel):
    """Parámetros de consulta para el endpoint GET /api/messages/{session_id}"""
    
    limit: int = Field(
        default=50, 
        ge=1, 
        le=100,
        description="Número máximo de mensajes a retornar (1-100)"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Número de mensajes a saltar para paginación"
    )
    sender: Optional[SenderEnum] = Field(
        default=None,
        description="Filtrar por tipo de remitente: 'user' o 'system'"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "limit": 50,
                "offset": 0,
                "sender": "user"
            }
        }