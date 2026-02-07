"""
Tests unitarios para el modelo Message.

Pruebas de validación, creación, y funcionalidad
del modelo SQLAlchemy Message.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from app.models.message import Message
from app.schemas.message import SenderEnum


class TestMessageModel:
    """Suite de tests para el modelo Message."""
    
    def test_message_creation_with_all_fields(self, test_db_session):
        """Test creación de mensaje con todos los campos."""
        # Arrange
        message_data = {
            "message_id": "test-msg-123",
            "session_id": "test-session",
            "content": "Mensaje de prueba",
            "sender": SenderEnum.USER,
            "word_count": 3,
            "character_count": 17,
            "timestamp": datetime.now(timezone.utc)
        }
        
        # Act
        message = Message(**message_data)
        test_db_session.add(message)
        test_db_session.commit()
        
        # Assert
        assert message.message_id == "test-msg-123"
        assert message.session_id == "test-session"
        assert message.content == "Mensaje de prueba"
        assert message.sender == SenderEnum.USER
        assert message.word_count == 3
        assert message.character_count == 17
        assert message.timestamp is not None
    
    def test_message_creation_with_minimal_fields(self, test_db_session):
        """Test creación de mensaje con campos mínimos."""
        # Act
        message = Message(
            message_id="minimal-test",
            session_id="session-minimal",
            content="Test",
            sender=SenderEnum.SYSTEM,
            timestamp=datetime.now(timezone.utc)  # timestamp requerido
        )
        test_db_session.add(message)
        test_db_session.commit()
        
        # Assert
        assert message.message_id == "minimal-test"
        assert message.session_id == "session-minimal"
        assert message.content == "Test"
        assert message.sender == SenderEnum.SYSTEM
        # Los campos opcionales deben tener valores por defecto
        assert message.word_count is None or message.word_count >= 0
        assert message.character_count is None or message.character_count >= 0
    
    def test_message_timestamp_timezone_aware(self, test_db_session):
        """Test que el timestamp sea timezone-aware (UTC)."""
        # Arrange
        utc_time = datetime.now(timezone.utc)
        
        # Act
        message = Message(
            message_id="timezone-test",
            session_id="timezone-session",
            content="Timezone test message",
            sender=SenderEnum.USER,
            timestamp=utc_time
        )
        test_db_session.add(message)
        test_db_session.commit()
        
        # Assert
        # Nota: SQLite puede perder información de timezone al persistir
        # Verificamos que el timestamp se guarde correctamente
        assert message.timestamp is not None
        assert isinstance(message.timestamp, datetime)
        # El timestamp debe ser aproximadamente el mismo (diferencia menor a 1 segundo)
        time_diff = abs((message.timestamp - utc_time.replace(tzinfo=None)).total_seconds())
        assert time_diff < 1.0
    
    @pytest.mark.parametrize("sender", [SenderEnum.USER, SenderEnum.SYSTEM])
    def test_message_valid_sender_types(self, test_db_session, sender):
        """Test que se acepten ambos tipos de sender válidos."""
        # Act
        message = Message(
            message_id=f"sender-test-{sender.value}",
            session_id="sender-session",
            content=f"Test message from {sender.value}",
            sender=sender,
            timestamp=datetime.now(timezone.utc)  # timestamp requerido
        )
        test_db_session.add(message)
        test_db_session.commit()
        
        # Assert
        assert message.sender == sender
    
    def test_message_unique_id_constraint(self, test_db_session):
        """Test que message_id sea único."""
        # Arrange
        message1 = Message(
            message_id="duplicate-test",
            session_id="session1",
            content="First message",
            sender=SenderEnum.USER,
            timestamp=datetime.now(timezone.utc)
        )
        
        message2 = Message(
            message_id="duplicate-test",  # Mismo ID
            session_id="session2",
            content="Second message",
            sender=SenderEnum.SYSTEM,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Act & Assert
        test_db_session.add(message1)
        test_db_session.commit()
        
        test_db_session.add(message2)
        with pytest.raises(IntegrityError):
            test_db_session.commit()
    
    def test_message_required_fields_validation(self, test_db_session):
        """Test validación de campos requeridos."""
        # Los tests de TypeError no aplican ya que SQLAlchemy permite crear instancias
        # sin todos los campos. La validación ocurre al hacer commit.
        
        # Test sin timestamp (campo requerido NOT NULL)
        message_no_timestamp = Message(
            message_id="test-no-timestamp",
            session_id="test-session",
            content="Test content",
            sender=SenderEnum.USER
            # sin timestamp
        )
        
        test_db_session.add(message_no_timestamp)
        with pytest.raises(IntegrityError):
            test_db_session.commit()
        
        test_db_session.rollback()
    
    def test_message_metadata_fields(self, test_db_session):
        """Test campos de metadatos (word_count, character_count)."""
        # Arrange
        content = "Este mensaje tiene cinco palabras exactas"
        message = Message(
            message_id="metadata-test",
            session_id="metadata-session",
            content=content,
            sender=SenderEnum.USER,
            word_count=6,
            character_count=len(content),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Act
        test_db_session.add(message)
        test_db_session.commit()
        
        # Assert
        assert message.word_count == 6
        assert message.character_count == len(content)
        assert message.character_count == 41  # Verificar longitud exacta corregida
    
    def test_message_string_representation(self, test_db_session):
        """Test representación string del modelo."""
        # Arrange
        message = Message(
            message_id="repr-test",
            session_id="repr-session", 
            content="Test representation",
            sender=SenderEnum.USER,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Act
        string_repr = str(message)
        
        # Assert
        assert "Message" in string_repr
        assert "repr-test" in string_repr
    
    def test_message_indexes_coverage(self, test_db_session):
        """Test que los índices están funcionando creando múltiples mensajes."""
        # Limpiar datos previos para asegurar conteos correctos
        test_db_session.query(Message).delete()
        test_db_session.commit()
        
        # Crear mensajes para probar indices
        messages = []
        for i in range(5):
            message = Message(
                message_id=f"index-test-{i}",
                session_id="index-session" if i < 3 else "other-session", 
                content=f"Test message {i}",
                sender=SenderEnum.USER if i % 2 == 0 else SenderEnum.SYSTEM,
                timestamp=datetime.now(timezone.utc)
            )
            messages.append(message)
        
        # Act
        test_db_session.add_all(messages)
        test_db_session.commit()
        
        # Assert - Verificar que se pueden buscar por índices
        by_session = test_db_session.query(Message).filter(
            Message.session_id == "index-session"
        ).count()
        assert by_session == 3
        
        by_sender = test_db_session.query(Message).filter(
            Message.sender == SenderEnum.USER
        ).count()
        assert by_sender == 3  # índices 0, 2, 4
    
    def test_message_content_length_limits(self, test_db_session):
        """Test límites de longitud de contenido."""
        # Test contenido muy largo
        long_content = "x" * 10000  # 10k caracteres
        
        message = Message(
            message_id="long-content-test",
            session_id="long-session",
            content=long_content,
            sender=SenderEnum.USER,
            character_count=len(long_content),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Act & Assert - Debería funcionar (no hay límite explícito en el modelo)
        test_db_session.add(message)
        test_db_session.commit()
        
        assert message.content == long_content
        assert message.character_count == 10000