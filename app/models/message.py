"""
Modelo de datos para mensajes de chat.

Define la estructura de la tabla 'messages' en la base de datos
y los métodos relacionados con el manejo de mensajes.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Index, Text
from sqlalchemy.sql import func

from app.database.connection import Base


class Message(Base):
    """
    Modelo de mensaje de chat que representa un mensaje en la base de datos.

    Atributos:
        id (int): Identificador único autoincremental (clave primaria)
        message_id (str): Identificador único del mensaje
        session_id (str): Identificador de la sesión de chat
        content (str): Contenido del mensaje
        timestamp (datetime): Fecha y hora del mensaje original
        sender (str): Remitente del mensaje ('user' o 'system')
        word_count (int): Número de palabras en el mensaje
        character_count (int): Número de caracteres en el mensaje
        processed_at (datetime): Fecha y hora del procesamiento del mensaje
        created_at (datetime): Fecha y hora de creación del registro
        updated_at (datetime): Fecha y hora de última actualización
    """
    __tablename__ = "messages"

    # Identificadores principales
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message_id = Column(String(255), unique=True, nullable=False, index=True)
    session_id = Column(String(255), nullable=False, index=True)

    # Datos del mensaje
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    sender = Column(String(10), nullable=False)

    # Metadatos de procesamiento
    word_count = Column(Integer, nullable=False, default=0)
    character_count = Column(Integer, nullable=False, default=0)
    processed_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Auditoría
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Índices compuestos para mejorar el rendimiento de las consultas
    __table_args__ = (
        Index('idx_session_sender', 'session_id', 'sender'),  # Para filtrar por sesión y remitente
        Index('idx_session_timestamp', 'session_id', 'timestamp'),  # Para ordenar por fecha
        Index('idx_processed_at', 'processed_at'),  # Para consultas de procesamiento
    )

    def __repr__(self) -> str:
        """
        Representación del objeto Message en formato texto.

        Returns:
            str: Cadena descriptiva del mensaje
        """
        return (
            f"<Message(message_id='{self.message_id}', "
            f"session_id='{self.session_id}', "
            f"sender='{self.sender}', "
            f"content_length={self.character_count})>"
        )

    def to_dict(self) -> dict:
        """
        Convierte el mensaje a un diccionario.

        Returns:
            dict: Representación del mensaje con todos sus atributos
        """
        return {
            "message_id": self.message_id,
            "session_id": self.session_id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "sender": self.sender,
            "metadata": {
                "word_count": self.word_count,
                "character_count": self.character_count,
                "processed_at": self.processed_at.isoformat() if self.processed_at else None
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def validate_sender(cls, sender: str) -> bool:
        """
        Valida que el remitente sea válido.

        Args:
            sender (str): El remitente a validar

        Returns:
            bool: True si el remitente es válido ('user' o 'system'), False en caso contrario
        """
        return sender in ["user", "system"]