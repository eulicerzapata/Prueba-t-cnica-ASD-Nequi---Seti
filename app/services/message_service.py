"""
Servicio principal para procesamiento de mensajes de chat.

Contiene la lógica de negocio, filtrado de contenido, 
generación de metadatos y validaciones.
"""

import os
import re
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.message import Message
from app.schemas.message import MessageCreate, MessageResponse, MessageListResponse, SenderEnum
from app.repositories.message_repository import MessageRepository
from app.repositories.exceptions import MessageAlreadyExistsError, MessageNotFoundError
from .exceptions import (
    InappropriateContentError,
    MessageValidationError,
    MessageProcessingError,
    RateLimitExceededError
)


class ContentFilter:
    """Filtro de contenido inapropiado para mensajes."""
    
    def __init__(self, profanity_words: Optional[List[str]] = None):
        """
        Inicializar filtro de contenido.
        
        Args:
            profanity_words: Lista de palabras inapropiadas (opcional)
        """
        # Palabras por defecto + palabras desde configuración
        default_words = [
            'spam', 'malo', 'prohibido', 'ofensivo', 'inappropriate',
            'badword', 'vulgar', 'toxic', 'hate', 'abuse'
        ]
        
        self.profanity_words = set(
            (profanity_words or []) + default_words
        )
    
    def contains_inappropriate_content(self, content: str) -> bool:
        """
        Verificar si el contenido contiene palabras inapropiadas.
        
        Args:
            content: Contenido del mensaje
            
        Returns:
            bool: True si contiene contenido inapropiado
        """
        # Convertir a minúsculas y dividir en palabras
        words = re.findall(r'\b\w+\b', content.lower())
        
        # Verificar cada palabra
        for word in words:
            if word in self.profanity_words:
                return True
        
        return False
    
    def get_inappropriate_words(self, content: str) -> List[str]:
        """
        Obtener lista de palabras inapropiadas encontradas.
        
        Args:
            content: Contenido del mensaje
            
        Returns:
            List[str]: Lista de palabras inapropiadas encontradas
        """
        words = re.findall(r'\b\w+\b', content.lower())
        inappropriate = []
        
        for word in words:
            if word in self.profanity_words:
                inappropriate.append(word)
        
        return inappropriate
    
    def add_words(self, words: List[str]) -> None:
        """Agregar nuevas palabras al filtro."""
        self.profanity_words.update(word.lower() for word in words)
    
    def remove_words(self, words: List[str]) -> None:
        """Quitar palabras del filtro."""
        for word in words:
            self.profanity_words.discard(word.lower())


class MessageProcessor:
    """Procesador de metadatos para mensajes."""
    
    @staticmethod
    def generate_metadata(content: str, processed_at: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Generar metadatos para un mensaje.
        
        Args:
            content: Contenido del mensaje
            processed_at: Timestamp de procesamiento (opcional)
            
        Returns:
            Dict: Metadatos generados
        """
        if processed_at is None:
            processed_at = datetime.now(timezone.utc)
        
        # Contar palabras (dividir por espacios y filtrar vacíos)
        words = [word for word in content.split() if word.strip()]
        word_count = len(words)
        
        # Contar caracteres (excluyendo espacios al inicio/final)
        character_count = len(content.strip())
        
        # Métricas adicionales
        sentence_count = len([s for s in re.split(r'[.!?]+', content) if s.strip()])
        avg_word_length = sum(len(word) for word in words) / max(word_count, 1)
        
        return {
            'word_count': word_count,
            'character_count': character_count,
            'processed_at': processed_at,
            'sentence_count': sentence_count,
            'avg_word_length': round(avg_word_length, 2),
            'has_questions': '?' in content,
            'has_exclamations': '!' in content,
            'is_uppercase': content.isupper() if content else False,
            'language_hints': MessageProcessor._detect_language_hints(content)
        }
    
    @staticmethod
    def _detect_language_hints(content: str) -> List[str]:
        """Detectar pistas de idioma basado en palabras comunes."""
        hints = []
        
        # Palabras comunes en español
        spanish_words = {'hola', 'gracias', 'por', 'favor', 'como', 'estas', 'muy', 'bien'}
        # Palabras comunes en inglés  
        english_words = {'hello', 'thanks', 'please', 'how', 'are', 'you', 'very', 'good'}
        
        content_lower = content.lower()
        
        if any(word in content_lower for word in spanish_words):
            hints.append('spanish')
        if any(word in content_lower for word in english_words):
            hints.append('english')
            
        return hints


class MessageValidator:
    """Validador de reglas de negocio para mensajes."""
    
    def __init__(self, max_content_length: int = 5000, max_daily_messages: int = 1000):
        """
        Inicializar validador.
        
        Args:
            max_content_length: Longitud máxima del contenido
            max_daily_messages: Máximo de mensajes por sesión por día
        """
        self.max_content_length = max_content_length
        self.max_daily_messages = max_daily_messages
    
    def validate_message_content(self, content: str) -> List[str]:
        """
        Validar contenido del mensaje.
        
        Args:
            content: Contenido a validar
            
        Returns:
            List[str]: Lista de errores encontrados
        """
        errors = []
        
        if not content or not content.strip():
            errors.append("El contenido no puede estar vacío")
        
        if len(content) > self.max_content_length:
            errors.append(f"El contenido excede el límite de {self.max_content_length} caracteres")
        
        # Validar que no sea solo espacios o caracteres especiales
        if content and not re.search(r'\w', content):
            errors.append("El contenido debe contener al menos una palabra válida")
        
        return errors
    
    def validate_sender_permissions(self, sender: SenderEnum, session_id: str) -> List[str]:
        """
        Validar permisos del remitente.
        
        Args:
            sender: Tipo de remitente
            session_id: ID de la sesión
            
        Returns:
            List[str]: Lista de errores de permisos
        """
        errors = []
        
        # Ejemplo: validaciones específicas por tipo de sender
        if sender == SenderEnum.SYSTEM:
            # Solo ciertos servicios pueden enviar como sistema
            if not self._is_system_authorized(session_id):
                errors.append("No autorizado para enviar mensajes como sistema")
        
        return errors
    
    def _is_system_authorized(self, session_id: str) -> bool:
        """Verificar si está autorizado para enviar como sistema."""
        # Aquí iría lógica de autorización real
        # Por ahora, permitir todos los mensajes de sistema
        return True
    
    async def validate_rate_limit(self, session_id: str, repository: MessageRepository) -> None:
        """
        Validar límites de tasa de mensajes.
        
        Args:
            session_id: ID de la sesión
            repository: Repositorio para consultas
            
        Raises:
            RateLimitExceededError: Si se excede algún límite
        """
        try:
            # Obtener mensajes recientes (últimos 60 minutos)
            recent_messages = repository.get_recent_messages(session_id, minutes=60)
            
            if len(recent_messages) >= 100:  # Límite por hora
                raise RateLimitExceededError("hora", len(recent_messages), 100)
            
            # Verificar mensajes muy recientes (anti-spam)
            very_recent = repository.get_recent_messages(session_id, minutes=1)
            if len(very_recent) >= 10:  # Máximo 10 mensajes por minuto
                raise RateLimitExceededError("minuto", len(very_recent), 10)
                
        except RateLimitExceededError:
            # Re-lanzar excepciones de rate limit
            raise
        except Exception:
            # Si no se puede verificar, permitir el mensaje
            pass


class MessageService:
    """Servicio principal para manejo de mensajes de chat."""
    
    def __init__(self, db, content_filter=None):
        """
        Inicializar servicio de mensajes.
        
        Args:
            db: Repositorio de mensajes o sesión de base de datos
            content_filter: Filtro de contenido personalizado (opcional)
        """
        # Si db es ya un repositorio, usarlo directamente
        if hasattr(db, 'create'):
            self.repository = db
            self.db = None
        else:
            # Si db es una sesión, crear repository
            self.db = db
            self.repository = MessageRepository(db)
        
        # Usar content_filter proporcionado o crear uno nuevo
        if content_filter is not None:
            self.content_filter = content_filter
        else:
            # Obtener palabras desde configuración de entorno
            profanity_words_str = os.getenv("PROFANITY_WORDS", "")
            profanity_words = [word.strip() for word in profanity_words_str.split(",") if word.strip()] if profanity_words_str else None
            self.content_filter = ContentFilter(profanity_words)
        
        self.processor = MessageProcessor()
        self.validator = MessageValidator()
    
    async def create_message(self, message_data: MessageCreate) -> 'MessageCreateResponse':
        """
        Crear un nuevo mensaje con procesamiento completo.
        
        Args:
            message_data: Datos del mensaje validados por Pydantic
            
        Returns:
            MessageResponse: Mensaje creado con metadatos
            
        Raises:
            ValueError: Si el mensaje no pasa las validaciones
            MessageAlreadyExistsError: Si ya existe un mensaje con ese ID
        """
        # 1. Validaciones de negocio
        await self._validate_message(message_data)
        
        # 2. Filtrar contenido inapropiado
        inappropriate_words = self.content_filter.get_inappropriate_words(message_data.content)
        if inappropriate_words:
            raise InappropriateContentError(inappropriate_words)
        
        # 3. Generar metadatos usando timestamp proporcionado si existe
        provided_timestamp = message_data.timestamp if message_data.timestamp else None
        metadata = self.processor.generate_metadata(message_data.content, provided_timestamp)
        
        # 4. Crear mensaje en base de datos
        try:
            db_message = self.repository.create(message_data, metadata)
            
            # 5. Convertir a response schema simplificado
            return self._convert_to_create_response(db_message)
            
        except MessageAlreadyExistsError:
            # Re-lanzar directamente para que el controller lo maneje
            raise
        except Exception as e:
            raise MessageProcessingError("crear mensaje", e)
    
    def get_message_by_id(self, message_id: str) -> Optional[MessageResponse]:
        """
        Obtener mensaje por ID.
        
        Args:
            message_id: ID del mensaje
            
        Returns:
            MessageResponse o None si no existe
        """
        db_message = self.repository.get_by_id(message_id)
        if not db_message:
            return None
        
        return self._convert_to_response(db_message)
    
    def get_messages_by_session(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
        sender: Optional[SenderEnum] = None
    ) -> MessageListResponse:
        """
        Obtener mensajes de una sesión con paginación.
        
        Args:
            session_id: ID de la sesión
            limit: Límite de mensajes por página
            offset: Mensajes a saltar
            sender: Filtrar por tipo de sender (opcional)
            
        Returns:
            MessageListResponse: Lista paginada de mensajes
        """
        # Obtener mensajes con paginación
        messages, total_count = self.repository.get_by_session(
            session_id, limit, offset, sender
        )
        
        # Convertir a response schemas
        message_responses = [
            self._convert_to_response(msg) for msg in messages
        ]
        
        # Calcular si hay más mensajes
        has_more = (offset + limit) < total_count
        
        return MessageListResponse(
            messages=message_responses,
            total=total_count,
            limit=limit,
            offset=offset,
            has_more=has_more
        )
    
    def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """
        Obtener estadísticas de una sesión.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Dict: Estadísticas de la sesión
        """
        stats = self.repository.get_session_stats(session_id)
        
        # Agregar métricas adicionales procesadas
        if stats['total_messages'] > 0:
            stats['avg_words_per_message'] = round(
                stats['total_words'] / stats['total_messages'], 2
            )
            stats['avg_chars_per_message'] = round(
                stats['total_characters'] / stats['total_messages'], 2
            )
        else:
            stats['avg_words_per_message'] = 0
            stats['avg_chars_per_message'] = 0
        
        return stats
    
    async def _validate_message(self, message_data: MessageCreate) -> None:
        """Validar mensaje antes de creación."""
        errors = []
        
        # Validar si message_id ya existe (solo si el usuario lo proporciona)
        if message_data.message_id:
            if self.repository.exists(message_data.message_id):
                raise MessageAlreadyExistsError(message_data.message_id)
        
        # Validar contenido
        content_errors = self.validator.validate_message_content(message_data.content)
        errors.extend(content_errors)
        
        # Validar permisos del sender
        sender_errors = self.validator.validate_sender_permissions(
            message_data.sender, message_data.session_id
        )
        errors.extend(sender_errors)
        
        # Si hay errores de validación básica, lanzar excepción
        if errors:
            raise MessageValidationError(errors)
        
        # Validar límites de tasa (puede lanzar RateLimitExceededError)
        await self.validator.validate_rate_limit(
            message_data.session_id, self.repository
        )
    
    def _convert_to_response(self, db_message: Message) -> MessageResponse:
        """Convertir modelo de DB a response schema completo."""
        from app.schemas.message import MessageMetadata  # Import local para evitar circular imports
        
        return MessageResponse(
            message_id=db_message.message_id,
            session_id=db_message.session_id,
            content=db_message.content,
            timestamp=db_message.timestamp,
            sender=SenderEnum(db_message.sender),
            metadata=MessageMetadata(
                word_count=db_message.word_count,
                character_count=db_message.character_count,
                processed_at=db_message.processed_at
            ),
            created_at=db_message.created_at,
            updated_at=db_message.updated_at
        )

    def _convert_to_create_response(self, db_message: Message) -> 'MessageCreateResponse':
        """Convertir modelo de DB a response schema simplificado para creación."""
        from app.schemas.message import MessageMetadata, MessageCreateResponse
        
        return MessageCreateResponse(
            message_id=db_message.message_id,
            session_id=db_message.session_id,
            content=db_message.content,
            timestamp=db_message.timestamp,
            sender=SenderEnum(db_message.sender),
            metadata=MessageMetadata(
                word_count=db_message.word_count,
                character_count=db_message.character_count,
                processed_at=db_message.processed_at
            )
        )