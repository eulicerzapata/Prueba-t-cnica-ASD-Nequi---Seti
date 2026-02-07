"""
Configuración y utilidades para servicios.

Configura filtros de contenido y otros servicios desde variables de entorno.
"""

import os
from typing import List, Optional
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from .message_service import MessageService, ContentFilter

# Cargar variables de entorno
load_dotenv()


def get_profanity_words_from_config() -> List[str]:
    """
    Obtener palabras inapropiadas desde configuración.
    
    Returns:
        List[str]: Lista de palabras inapropiadas configuradas
    """
    # Obtener desde variable de entorno
    profanity_config = os.getenv("PROFANITY_WORDS", "")
    
    if not profanity_config:
        return []
    
    # Dividir por comas y limpiar espacios
    words = [word.strip().lower() for word in profanity_config.split(",")]
    
    # Filtrar palabras vacías
    return [word for word in words if word]


def create_message_service(db: Session, custom_profanity: Optional[List[str]] = None) -> MessageService:
    """
    Factory function para crear servicio de mensajes.

    Args:
        db: Sesión de base de datos
        custom_profanity: Palabras adicionales para filtro (opcional)

    Returns:
        MessageService: Instancia configurada del servicio
    """
    # Obtener palabras desde configuración
    config_words = get_profanity_words_from_config()

    # Combinar con palabras personalizadas si se proporcionan
    if custom_profanity:
        config_words.extend(custom_profanity)

    # Crear ContentFilter con las palabras configuradas
    content_filter = ContentFilter(config_words) if config_words else None

    return MessageService(db, content_filter)


class ServiceConfig:
    """Configuración global para servicios."""
    
    # Límites desde variables de entorno
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "5000"))
    MAX_DAILY_MESSAGES = int(os.getenv("MAX_DAILY_MESSAGES", "1000")) 
    MAX_HOURLY_MESSAGES = int(os.getenv("MAX_HOURLY_MESSAGES", "100"))
    MAX_MESSAGES_PER_MINUTE = int(os.getenv("MAX_MESSAGES_PER_MINUTE", "10"))
    
    # Configuración de filtro de contenido
    ENABLE_CONTENT_FILTER = os.getenv("ENABLE_CONTENT_FILTER", "true").lower() == "true"
    STRICT_FILTERING = os.getenv("STRICT_FILTERING", "false").lower() == "true"
    
    # Configuración de procesamiento
    ENABLE_LANGUAGE_DETECTION = os.getenv("ENABLE_LANGUAGE_DETECTION", "true").lower() == "true"
    ENABLE_SENTIMENT_ANALYSIS = os.getenv("ENABLE_SENTIMENT_ANALYSIS", "false").lower() == "true"
    
    @classmethod
    def get_content_filter_config(cls) -> dict:
        """Obtener configuración del filtro de contenido."""
        return {
            'enabled': cls.ENABLE_CONTENT_FILTER,
            'strict': cls.STRICT_FILTERING,
            'profanity_words': get_profanity_words_from_config()
        }
    
    @classmethod
    def get_rate_limits(cls) -> dict:
        """Obtener configuración de límites de tasa."""
        return {
            'max_content_length': cls.MAX_CONTENT_LENGTH,
            'max_daily_messages': cls.MAX_DAILY_MESSAGES,
            'max_hourly_messages': cls.MAX_HOURLY_MESSAGES,
            'max_per_minute': cls.MAX_MESSAGES_PER_MINUTE
        }