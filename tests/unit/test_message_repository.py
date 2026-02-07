"""
Tests unitarios para MessageRepository.

Pruebas de las operaciones CRUD, manejo de errores,
y funcionalidades del repositorio de datos.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from app.repositories.message_repository import MessageRepository
from app.models.message import Message
from app.schemas.message import MessageCreate, SenderEnum
from app.exceptions import MessageNotFoundError, DatabaseError, DuplicateMessageError


class TestMessageRepository:
    """Suite de tests para MessageRepository."""
    
    def _generate_metadata(self, content: str) -> dict:
        """Generar metadatos básicos para testing."""
        return {
            'word_count': len(content.split()) if content.strip() else 0,
            'character_count': len(content),
            'processed_at': datetime.now(timezone.utc)
        }
    
    def test_create_message_success(self, test_db_session):
        """Test creación exitosa de mensaje."""
        # Arrange
        repository = MessageRepository(test_db_session)
        message_data = MessageCreate(
            session_id="test-session",
            content="Test message",
            sender=SenderEnum.USER
        )
        
        # Simular metadatos que normalmente generaría el servicio
        metadata = self._generate_metadata(message_data.content)
        
        # Act
        result = repository.create(message_data, metadata)
        
        # Assert
        assert result.session_id == "test-session"
        assert result.content == "Test message"
        assert result.sender == SenderEnum.USER
        assert result.message_id is not None
        assert result.timestamp is not None
        assert result.word_count == 2
        assert result.character_count == 12
    
    def test_create_message_with_optional_fields(self, test_db_session):
        """Test creación con campos opcionales proporcionados."""
        # Arrange
        repository = MessageRepository(test_db_session)
        custom_timestamp = datetime.now(timezone.utc)
        message_data = MessageCreate(
            message_id="custom-id-123",
            session_id="test-session",
            content="Test with custom fields",
            sender=SenderEnum.SYSTEM,
            timestamp=custom_timestamp
        )
        
        # Act
        result = repository.create(message_data, self._generate_metadata(message_data.content))
        
        # Assert
        assert result.message_id == "custom-id-123"
        assert result.timestamp.replace(tzinfo=None) == custom_timestamp.replace(tzinfo=None)
        assert result.sender == SenderEnum.SYSTEM
    
    def test_create_message_duplicate_id_error(self, test_db_session):
        """Test error al crear mensaje con ID duplicado."""
        # Arrange
        repository = MessageRepository(test_db_session)
        message_data1 = MessageCreate(
            message_id="duplicate-id",
            session_id="test-session",
            content="First message",
            sender=SenderEnum.USER
        )
        message_data2 = MessageCreate(
            message_id="duplicate-id",  # Mismo ID
            session_id="test-session",
            content="Second message", 
            sender=SenderEnum.USER
        )
        
        # Act
        repository.create(message_data1, self._generate_metadata(message_data1.content))  # Primera creación exitosa
        
        # Assert
        with pytest.raises(DuplicateMessageError) as exc_info:
            repository.create(message_data2, self._generate_metadata(message_data2.content))
        
        assert "ya existe" in str(exc_info.value) or "duplicate-id" in str(exc_info.value)
    
    def test_get_by_id_found(self, test_db_session):
        """Test obtener mensaje por ID existente."""
        # Arrange
        repository = MessageRepository(test_db_session)
        message_data = MessageCreate(
            message_id="find-me-123",
            session_id="test-session",
            content="Find this message",
            sender=SenderEnum.USER
        )
        created_message = repository.create(message_data, self._generate_metadata(message_data.content))
        
        # Act
        found_message = repository.get_by_id("find-me-123")
        
        # Assert
        assert found_message is not None
        assert found_message.message_id == "find-me-123"
        assert found_message.content == "Find this message"
        assert found_message.session_id == created_message.session_id
    
    def test_get_by_id_not_found(self, test_db_session):
        """Test obtener mensaje por ID no existente."""
        # Arrange
        repository = MessageRepository(test_db_session)
        
        # Act
        result = repository.get_by_id("non-existent-id")
        
        # Assert
        assert result is None
    
    def test_get_by_session_with_messages(self, test_db_session):
        """Test obtener mensajes por sesión existente."""
        # Arrange
        repository = MessageRepository(test_db_session)
        session_id = "test-pagination"
        
        # Crear múltiples mensajes para la misma sesión
        for i in range(5):
            message_data = MessageCreate(
                session_id=session_id,
                content=f"Message {i}",
                sender=SenderEnum.USER if i % 2 == 0 else SenderEnum.SYSTEM
            )
            repository.create(message_data, self._generate_metadata(message_data.content))
        
        # Act
        messages, total = repository.get_by_session(session_id, page=1, page_size=3)
        
        # Assert
        assert len(messages) == 3  # Página de 3 elementos
        assert total == 5  # Total de mensajes en la sesión
        assert all(msg.session_id == session_id for msg in messages)
    
    def test_get_by_session_pagination(self, test_db_session):
        """Test paginación de mensajes por sesión."""
        # Arrange
        repository = MessageRepository(test_db_session)
        session_id = "pagination-test"
        
        # Crear 10 mensajes
        for i in range(10):
            message_data = MessageCreate(
                session_id=session_id,
                content=f"Paginated message {i}",
                sender=SenderEnum.USER
            )
            repository.create(message_data, self._generate_metadata(message_data.content))
        
        # Act - Primera página
        page1_messages, page1_total = repository.get_by_session(
            session_id, page=1, page_size=4
        )
        
        # Act - Segunda página  
        page2_messages, page2_total = repository.get_by_session(
            session_id, page=2, page_size=4
        )
        
        # Assert
        assert len(page1_messages) == 4
        assert len(page2_messages) == 4
        assert page1_total == page2_total == 10
        
        # Verificar que no hay duplicados entre páginas
        page1_ids = {msg.message_id for msg in page1_messages}
        page2_ids = {msg.message_id for msg in page2_messages}
        assert page1_ids.isdisjoint(page2_ids)
    
    def test_get_by_session_empty_result(self, test_db_session):
        """Test obtener mensajes de sesión no existente."""
        # Arrange
        repository = MessageRepository(test_db_session)
        
        # Act
        messages, total = repository.get_by_session("non-existent-session")
        
        # Assert
        assert messages == []
        assert total == 0
    
    def test_get_by_session_ordering(self, test_db_session):
        """Test que los mensajes se ordenen correctamente por timestamp."""
        # Arrange
        repository = MessageRepository(test_db_session)
        session_id = "ordering-test"
        
        # Crear mensajes con timestamps específicos
        timestamps = [
            datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
        ]
        
        for i, ts in enumerate(timestamps):
            message_data = MessageCreate(
                session_id=session_id,
                content=f"Message at {ts.hour}:00",
                sender=SenderEnum.USER,
                timestamp=ts
            )
            repository.create(message_data, self._generate_metadata(message_data.content))
        
        # Act
        messages, _ = repository.get_by_session(session_id)
        
        # Assert - Debe estar ordenado por timestamp DESC (más reciente primero)
        assert len(messages) == 3
        assert messages[0].timestamp.hour == 12  # Más reciente
        assert messages[1].timestamp.hour == 10  # Intermedio
        assert messages[2].timestamp.hour == 9   # Más antiguo
    
    def test_exists_message_found(self, test_db_session):
        """Test verificar existencia de mensaje existente."""
        # Arrange
        repository = MessageRepository(test_db_session)
        message_data = MessageCreate(
            message_id="exists-test-123",
            session_id="test-session",
            content="This message exists",
            sender=SenderEnum.USER
        )
        repository.create(message_data, self._generate_metadata(message_data.content))
        
        # Act
        exists = repository.exists("exists-test-123")
        
        # Assert
        assert exists is True
    
    def test_exists_message_not_found(self, test_db_session):
        """Test verificar existencia de mensaje no existente."""
        # Arrange
        repository = MessageRepository(test_db_session) 
        
        # Act
        exists = repository.exists("non-existent-message")
        
        # Assert
        assert exists is False
    
    def test_word_count_calculation(self, test_db_session):
        """Test cálculo correcto de word_count."""
        # Arrange
        repository = MessageRepository(test_db_session)
        
        test_cases = [
            ("Una palabra", 2),
            ("Tres palabras exactas", 3),
            ("  Espacios   extra   entre  palabras  ", 4),
            ("x", 1),  # Caracter simple como contenido mínimo
            ("   abc   ", 1),  # Una palabra con espacios
            ("Una-palabra-con-guiones", 1),
            ("Email@domain.com es una dirección", 4)
        ]
        
        for content, expected_count in test_cases:
            # Act
            message_data = MessageCreate(
                session_id="word-count-test",
                content=content,
                sender=SenderEnum.USER
            )
            message = repository.create(message_data, self._generate_metadata(message_data.content))
            
            # Assert
            assert message.word_count == expected_count, \
                f"Content: '{content}' expected {expected_count}, got {message.word_count}"
    
    def test_character_count_calculation(self, test_db_session):
        """Test cálculo correcto de character_count."""
        # Arrange
        repository = MessageRepository(test_db_session)
        
        test_cases = [
            ("Hello", 5),
            ("Hello World!", 12),
            ("x", 1),  # Caracter simple como contenido mínimo
            ("Emojis 🚀🎉", 9),  # Cada emoji cuenta como 1 caracter
            ("Line\nbreak", 10),
            ("Tab\there", 8)
        ]
        
        for content, expected_count in test_cases:
            # Act
            message_data = MessageCreate(
                session_id="char-count-test",
                content=content,
                sender=SenderEnum.USER
            )
            message = repository.create(message_data, self._generate_metadata(message_data.content))
            
            # Assert
            assert message.character_count == expected_count, \
                f"Content: '{content}' expected {expected_count}, got {message.character_count}"
    
    @patch('uuid.uuid4')
    def test_uuid_generation_for_message_id(self, mock_uuid, test_db_session):
        """Test generación automática de UUID para message_id."""
        # Arrange
        # Mock que retorna string directamente
        mock_uuid.return_value = "mockeduuid123456"
        
        repository = MessageRepository(test_db_session)
        message_data = MessageCreate(
            # Sin message_id - debe generar uno automáticamente
            session_id="uuid-test",
            content="Auto UUID test",
            sender=SenderEnum.USER
        )
        
        # Act
        message = repository.create(message_data, self._generate_metadata(message_data.content))
        
        # Assert
        assert message.message_id == "mockeduuid123456"
        mock_uuid.assert_called_once()
    
    def test_database_error_handling(self, test_db_session):
        """Test manejo de errores de base de datos."""
        # Arrange
        repository = MessageRepository(test_db_session)
        
        message_data = MessageCreate(
            session_id="error-test",
            content="This should fail",
            sender=SenderEnum.USER
        )
        
        # Simular error forzando una violación de constraint o error SQL
        # Usamos un mock para simular SQLAlchemyError en el método add
        from unittest.mock import Mock, patch
        from sqlalchemy.exc import SQLAlchemyError
        
        with patch.object(test_db_session, 'add', side_effect=SQLAlchemyError("Simulated DB error")):
            with pytest.raises(DatabaseError):
                repository.create(message_data, self._generate_metadata(message_data.content))
