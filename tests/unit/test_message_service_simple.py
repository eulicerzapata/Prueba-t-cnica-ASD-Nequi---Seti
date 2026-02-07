"""
Tests Unitarios Simplificados para MessageService

Versión enfocada en funcionalidad básica sin mocks complejos
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone

from app.services.message_service import MessageService
from app.schemas.message import MessageCreate, SenderEnum
from app.models.message import Message


@pytest.mark.unit
class TestMessageServiceSimple:
    """Tests unitarios simplificados para MessageService."""

    @pytest.fixture
    def simple_message_service(self):
        """Service con mocks simples."""
        mock_repo = Mock()
        mock_filter = Mock()
        
        # Configurar mocks básicos
        mock_filter.get_inappropriate_words.return_value = []
        mock_filter.is_appropriate.return_value = True
        
        service = MessageService(mock_repo, mock_filter)
        return service, mock_repo, mock_filter

    @pytest.mark.asyncio
    async def test_create_message_basic(self, simple_message_service):
        """Test básico de creación de mensaje."""
        service, mock_repo, mock_filter = simple_message_service
        
        # Arrange - Mock with proper attributes
        mock_message = Mock()
        mock_message.message_id = "test-123"
        mock_message.content = "test content" 
        mock_message.session_id = "test-session"
        mock_message.sender = SenderEnum.USER  # Use actual enum value
        mock_message.timestamp = datetime.now(timezone.utc)
        mock_message.word_count = 2
        mock_message.character_count = 12
        mock_message.processed_at = datetime.now(timezone.utc)
        
        mock_repo.create.return_value = mock_message
        
        message_data = MessageCreate(
            session_id="test-session",
            content="test content",
            sender=SenderEnum.USER
        )
        
        # Act
        result = await service.create_message(message_data)
        
        # Assert
        assert result is not None
        assert result.message_id == "test-123"
        mock_repo.create.assert_called_once()

    def test_get_message_by_id_basic(self, simple_message_service):
        """Test básico de obtener mensaje por ID."""
        service, mock_repo, mock_filter = simple_message_service
        
        # Arrange - Mock with proper Message attributes
        test_time = datetime.now(timezone.utc)
        mock_message = Mock()
        mock_message.message_id = "test-123"
        mock_message.content = "test content"
        mock_message.session_id = "test-session"
        mock_message.sender = SenderEnum.USER
        mock_message.timestamp = test_time
        mock_message.word_count = 2
        mock_message.character_count = 12
        mock_message.processed_at = test_time
        mock_message.created_at = test_time  # Add missing field
        mock_message.updated_at = test_time  # Add missing field
        
        mock_repo.get_by_id.return_value = mock_message
        
        # Act
        result = service.get_message_by_id("test-123")
        
        # Assert
        assert result is not None
        assert result.message_id == "test-123"
        mock_repo.get_by_id.assert_called_once_with("test-123")

    def test_get_messages_by_session_basic(self, simple_message_service):
        """Test básico de obtener mensajes por sesión."""
        service, mock_repo, mock_filter = simple_message_service
        
        # Arrange - Mock messages with proper attributes
        test_time = datetime.now(timezone.utc)
        
        mock_message_1 = Mock()
        mock_message_1.message_id = "msg-1"
        mock_message_1.content = "content 1"
        mock_message_1.session_id = "test-session"
        mock_message_1.sender = SenderEnum.USER
        mock_message_1.timestamp = test_time
        mock_message_1.word_count = 2
        mock_message_1.character_count = 9
        mock_message_1.processed_at = test_time
        mock_message_1.created_at = test_time
        mock_message_1.updated_at = test_time
        
        mock_message_2 = Mock()
        mock_message_2.message_id = "msg-2"
        mock_message_2.content = "content 2"
        mock_message_2.session_id = "test-session"
        mock_message_2.sender = SenderEnum.SYSTEM
        mock_message_2.timestamp = test_time
        mock_message_2.word_count = 2
        mock_message_2.character_count = 9
        mock_message_2.processed_at = test_time
        mock_message_2.created_at = test_time
        mock_message_2.updated_at = test_time
        
        mock_messages = [mock_message_1, mock_message_2]
        mock_repo.get_by_session.return_value = (mock_messages, 2)
        
        # Act
        result = service.get_messages_by_session("test-session")
        
        # Assert
        assert result is not None
        assert result.total == 2
        assert len(result.messages) == 2
        mock_repo.get_by_session.assert_called_once()