"""
Repositorio para operaciones CRUD de mensajes.

Maneja el acceso a datos de la entidad Message con soporte para
filtrado, paginación y transacciones.
"""

from typing import List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from sqlalchemy.exc import SQLAlchemyError

from app.models.message import Message
from app.schemas.message import MessageCreate, SenderEnum


class MessageRepository:
    """Repositorio para operaciones de base de datos con mensajes."""
    
    def __init__(self, db: Session):
        """
        Inicializar repositorio con sesión de base de datos.
        
        Args:
            db: Sesión de SQLAlchemy
        """
        self.db = db

    def create(self, message_data: MessageCreate, metadata: dict) -> Message:
        """
        Crear un nuevo mensaje en la base de datos.
        
        Args:
            message_data: Datos del mensaje validados
            metadata: Metadatos procesados (word_count, character_count, etc.)
            
        Returns:
            Message: Mensaje creado
            
        Raises:
            SQLAlchemyError: Si hay error en la base de datos
        """
        try:
            # Usar message_id proporcionado o generar uno nuevo
            if message_data.message_id:
                message_id = message_data.message_id
            else:
                import uuid
                message_id = str(uuid.uuid4())
            
            # Usar timestamp proporcionado o generar uno nuevo
            if message_data.timestamp:
                current_timestamp = message_data.timestamp
            else:
                current_timestamp = datetime.now(timezone.utc)
            
            # Crear instancia del modelo
            db_message = Message(
                message_id=message_id,
                session_id=message_data.session_id,
                content=message_data.content,
                timestamp=current_timestamp,
                sender=message_data.sender.value,
                word_count=metadata.get('word_count', 0),
                character_count=metadata.get('character_count', 0),
                processed_at=metadata.get('processed_at', datetime.now(timezone.utc))
            )
            
            # Agregar a la sesión
            self.db.add(db_message)
            self.db.commit()
            self.db.refresh(db_message)
            
            return db_message
            
        except SQLAlchemyError as e:
            self.db.rollback()
            # Manejar específicamente violaciones de constraint único
            error_msg = str(e)
            if "UNIQUE constraint failed: messages.message_id" in error_msg:
                from app.repositories.exceptions import MessageAlreadyExistsError
                raise MessageAlreadyExistsError(message_id)
            # Para otros errores de SQLAlchemy, convertir a DatabaseError
            from app.exceptions import DatabaseError
            raise DatabaseError(f"Error de base de datos al crear mensaje: {str(e)}")

    def get_by_id(self, message_id: str) -> Optional[Message]:
        """
        Obtener mensaje por su ID único.
        
        Args:
            message_id: ID del mensaje
            
        Returns:
            Message o None si no existe
        """
        return self.db.query(Message).filter(
            Message.message_id == message_id
        ).first()

    def get_by_session(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
        sender: Optional[SenderEnum] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None
    ) -> Tuple[List[Message], int]:
        """
        Obtener mensajes por session_id con paginación y filtrado.
        
        Args:
            session_id: ID de la sesión
            limit: Número máximo de mensajes a retornar
            offset: Número de mensajes a saltar
            sender: Filtrar por tipo de remitente (opcional)
            page: Número de página (alternativa a offset)
            page_size: Tamaño de página (alternativa a limit)
            
        Returns:
            Tuple[List[Message], int]: Lista de mensajes y total de mensajes
        """
        # Si se usan page y page_size, convertir a limit y offset
        if page is not None and page_size is not None:
            limit = page_size
            offset = (page - 1) * page_size
        
        # Query base
        query = self.db.query(Message).filter(Message.session_id == session_id)
        
        # Aplicar filtro de sender si se proporciona
        if sender:
            query = query.filter(Message.sender == sender.value)
        
        # Contar total antes de aplicar paginación
        total_count = query.count()
        
        # Aplicar paginación y ordenamiento
        messages = query.order_by(desc(Message.timestamp))\
                       .offset(offset)\
                       .limit(limit)\
                       .all()
        
        return messages, total_count

    def get_all_by_session(self, session_id: str) -> List[Message]:
        """
        Obtener todos los mensajes de una sesión sin paginación.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            List[Message]: Lista completa de mensajes de la sesión
        """
        return self.db.query(Message)\
                     .filter(Message.session_id == session_id)\
                     .order_by(desc(Message.timestamp))\
                     .all()

    def update(self, message_id: str, update_data: dict) -> Optional[Message]:
        """
        Actualizar un mensaje existente.
        
        Args:
            message_id: ID del mensaje a actualizar
            update_data: Datos a actualizar
            
        Returns:
            Message actualizado o None si no existe
            
        Raises:
            SQLAlchemyError: Si hay error en la base de datos
        """
        try:
            db_message = self.get_by_id(message_id)
            if not db_message:
                return None
            
            # Actualizar campos proporcionados
            for field, value in update_data.items():
                if hasattr(db_message, field):
                    setattr(db_message, field, value)
            
            # Actualizar timestamp de modificación
            db_message.updated_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(db_message)
            
            return db_message
            
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    def exists(self, message_id: str) -> bool:
        """
        Verificar si existe un mensaje con el ID dado.
        
        Args:
            message_id: ID del mensaje
            
        Returns:
            bool: True si existe, False si no
        """
        return self.db.query(Message.message_id)\
                     .filter(Message.message_id == message_id)\
                     .first() is not None

    def count_by_session(self, session_id: str, sender: Optional[SenderEnum] = None) -> int:
        """
        Contar mensajes en una sesión con filtro opcional.
        
        Args:
            session_id: ID de la sesión
            sender: Filtrar por tipo de remitente (opcional)
            
        Returns:
            int: Número de mensajes
        """
        query = self.db.query(Message).filter(Message.session_id == session_id)
        
        if sender:
            query = query.filter(Message.sender == sender.value)
        
        return query.count()

    def get_recent_messages(
        self,
        session_id: str,
        minutes: int = 60,
        limit: int = 10
    ) -> List[Message]:
        """
        Obtener mensajes recientes de una sesión.
        
        Args:
            session_id: ID de la sesión
            minutes: Minutos hacia atrás para considerar "reciente"
            limit: Número máximo de mensajes
            
        Returns:
            List[Message]: Mensajes recientes ordenados por timestamp
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        return self.db.query(Message)\
                     .filter(
                         and_(
                             Message.session_id == session_id,
                             Message.created_at >= cutoff_time
                         )
                     )\
                     .order_by(desc(Message.timestamp))\
                     .limit(limit)\
                     .all()

    def get_session_stats(self, session_id: str) -> dict:
        """
        Obtener estadísticas de una sesión de chat.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            dict: Estadísticas de la sesión
        """
        # Consultas agregadas
        stats = self.db.query(
            func.count(Message.id).label('total_messages'),
            func.sum(Message.word_count).label('total_words'),
            func.sum(Message.character_count).label('total_characters'),
            func.min(Message.timestamp).label('first_message'),
            func.max(Message.timestamp).label('last_message')
        ).filter(Message.session_id == session_id).first()
        
        # Contar por tipo de sender
        user_count = self.count_by_session(session_id, SenderEnum.USER)
        system_count = self.count_by_session(session_id, SenderEnum.SYSTEM)
        
        return {
            'session_id': session_id,
            'total_messages': stats.total_messages or 0,
            'total_words': stats.total_words or 0,
            'total_characters': stats.total_characters or 0,
            'user_messages': user_count,
            'system_messages': system_count,
            'first_message_at': stats.first_message,
            'last_message_at': stats.last_message
        }

    def batch_create(self, messages_data: List[dict]) -> List[Message]:
        """
        Crear múltiples mensajes en una transacción.
        
        Args:
            messages_data: Lista de datos de mensajes
            
        Returns:
            List[Message]: Mensajes creados
            
        Raises:
            SQLAlchemyError: Si hay error en la base de datos
        """
        try:
            db_messages = []
            
            for msg_data in messages_data:
                db_message = Message(**msg_data)
                self.db.add(db_message)
                db_messages.append(db_message)
            
            self.db.commit()
            
            # Refresh todos los objetos
            for msg in db_messages:
                self.db.refresh(msg)
            
            return db_messages
            
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e