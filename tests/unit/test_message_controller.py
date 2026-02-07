"""
Tests para el controlador de mensajes (MessageController).
Cubre todos los endpoints y manejo de errores .
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.main import app
from app.schemas.message import (
    MessageResponse,
    MessageListResponse,
    MessageMetadata,
    MessageCreateResponse,
    SenderEnum
)
from app.services.exceptions import (
    InappropriateContentError,
    RateLimitExceededError,
    MessageProcessingError,
    MessageValidationError
)


class TestMessageController:
    """Tests para el controlador de mensajes."""

    def setup_method(self):
        """Setup para cada test."""
        self.client = TestClient(app)
        self.test_time = datetime.now(timezone.utc)

        # Mock message data
        self.mock_message_data = {
            "content": "Test message",
            "session_id": "test-session-123",
            "sender": "user"
        }

        # Mock metadata
        self.mock_metadata = MessageMetadata(
            word_count=2,
            character_count=12,
            processed_at=self.test_time
        )

        # Mock MessageCreateResponse (para POST)
        self.mock_create_response = MessageCreateResponse(
            message_id="msg-123",
            session_id="test-session-123",
            content="Test message",
            timestamp=self.test_time,
            sender=SenderEnum.USER,
            metadata=self.mock_metadata
        )

        # Mock MessageResponse (para GET)
        self.mock_message_response = MessageResponse(
            message_id="msg-123",
            session_id="test-session-123",
            content="Test message",
            timestamp=self.test_time,
            sender=SenderEnum.USER,
            metadata=self.mock_metadata,
            created_at=self.test_time,
            updated_at=self.test_time
        )

    @patch('app.controllers.message_controller.create_message_service')
    def test_create_message_success(self, mock_create_service):
        """Test creación exitosa de mensaje - 201."""
        # Arrange
        mock_service = Mock()
        mock_service.create_message = AsyncMock(return_value=self.mock_create_response)
        mock_create_service.return_value = mock_service

        # Act
        response = self.client.post(
            "/api/messages",
            json=self.mock_message_data
        )

        # Assert
        assert response.status_code == 201
        assert response.json()["status"] == "success"
        assert "data" in response.json()
        assert response.json()["data"]["message_id"] == "msg-123"

    @patch('app.controllers.message_controller.create_message_service')
    def test_create_message_inappropriate_content_error(self, mock_create_service):
        """Test error de contenido inapropiado - 400."""
        # Arrange
        mock_service = Mock()
        mock_service.create_message = AsyncMock(
            side_effect=InappropriateContentError(["badword", "spam"])
        )
        mock_create_service.return_value = mock_service

        # Act
        response = self.client.post(
            "/api/messages",
            json=self.mock_message_data
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["status"] == "error"
        assert response.json()["error"]["code"] == "INAPPROPRIATE_CONTENT"

    @patch('app.controllers.message_controller.create_message_service')
    def test_create_message_validation_error(self, mock_create_service):
        """Test error de validación - 400."""
        # Arrange
        mock_service = Mock()
        mock_service.create_message = AsyncMock(
            side_effect=MessageValidationError(["Content is empty"])
        )
        mock_create_service.return_value = mock_service

        # Act
        response = self.client.post(
            "/api/messages",
            json=self.mock_message_data
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["status"] == "error"
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    @patch('app.controllers.message_controller.create_message_service')
    def test_create_message_rate_limit_error(self, mock_create_service):
        """Test error de límite de tasa - 429."""
        # Arrange
        mock_service = Mock()
        mock_service.create_message = AsyncMock(
            side_effect=RateLimitExceededError(
                limit_type="minuto",
                current_count=11,
                max_allowed=10
            )
        )
        mock_create_service.return_value = mock_service

        # Act
        response = self.client.post(
            "/api/messages",
            json=self.mock_message_data
        )

        # Assert
        assert response.status_code == 429
        assert response.json()["status"] == "error"
        assert response.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"

    @patch('app.controllers.message_controller.create_message_service')
    def test_create_message_processing_error(self, mock_create_service):
        """Test error de procesamiento - 500."""
        # Arrange
        mock_service = Mock()
        mock_service.create_message = AsyncMock(
            side_effect=MessageProcessingError(
                operation="create",
                original_error=Exception("DB error")
            )
        )
        mock_create_service.return_value = mock_service

        # Act
        response = self.client.post(
            "/api/messages",
            json=self.mock_message_data
        )

        # Assert
        assert response.status_code == 500
        assert response.json()["status"] == "error"
        assert response.json()["error"]["code"] == "PROCESSING_ERROR"

    @patch('app.controllers.message_controller.create_message_service')
    def test_create_message_unexpected_error(self, mock_create_service):
        """Test error inesperado - 500."""
        # Arrange
        mock_service = Mock()
        mock_service.create_message = AsyncMock(
            side_effect=Exception("Unexpected error")
        )
        mock_create_service.return_value = mock_service

        # Act
        response = self.client.post(
            "/api/messages",
            json=self.mock_message_data
        )

        # Assert
        assert response.status_code == 500
        assert response.json()["status"] == "error"
        assert response.json()["error"]["code"] == "INTERNAL_ERROR"

    @patch('app.controllers.message_controller.create_message_service')
    def test_get_messages_success(self, mock_create_service):
        """Test obtener mensajes exitosamente - 200."""
        # Arrange
        mock_service = Mock()
        mock_list_response = MessageListResponse(
            messages=[self.mock_message_response],
            total=1,
            limit=50,
            offset=0,
            has_more=False
        )
        mock_service.get_messages_by_session = Mock(return_value=mock_list_response)
        mock_create_service.return_value = mock_service

        # Act
        response = self.client.get("/api/messages/test-session-123")

        # Assert
        assert response.status_code == 200
        assert len(response.json()["messages"]) == 1
        assert response.json()["total"] == 1

    @patch('app.controllers.message_controller.create_message_service')
    def test_get_messages_with_pagination(self, mock_create_service):
        """Test obtener mensajes con paginación - 200."""
        # Arrange
        mock_service = Mock()
        mock_list_response = MessageListResponse(
            messages=[],
            total=5,
            limit=2,
            offset=2,
            has_more=True
        )
        mock_service.get_messages_by_session = Mock(return_value=mock_list_response)
        mock_create_service.return_value = mock_service

        # Act
        response = self.client.get("/api/messages/test-session-123?limit=2&offset=2")

        # Assert
        assert response.status_code == 200
        assert response.json()["limit"] == 2
        assert response.json()["offset"] == 2
        assert response.json()["has_more"] is True

    @patch('app.controllers.message_controller.create_message_service')
    def test_get_messages_session_not_found(self, mock_create_service):
        """Test sesión no encontrada - 404."""
        # Arrange
        mock_service = Mock()
        mock_list_response = MessageListResponse(
            messages=[],
            total=0,
            limit=50,
            offset=0,
            has_more=False
        )
        mock_service.get_messages_by_session = Mock(return_value=mock_list_response)
        mock_create_service.return_value = mock_service

        # Act
        response = self.client.get("/api/messages/nonexistent-session")

        # Assert
        assert response.status_code == 404
        assert response.json()["status"] == "error"
        assert response.json()["error"]["code"] == "SESSION_NOT_FOUND"

    @patch('app.controllers.message_controller.create_message_service')
    def test_get_messages_service_error(self, mock_create_service):
        """Test error del servicio al obtener mensajes - 500."""
        # Arrange
        mock_service = Mock()
        mock_service.get_messages_by_session = Mock(
            side_effect=Exception("Database error")
        )
        mock_create_service.return_value = mock_service

        # Act
        response = self.client.get("/api/messages/test-session-123")

        # Assert
        assert response.status_code == 500
        assert response.json()["status"] == "error"
        assert response.json()["error"]["code"] == "INTERNAL_ERROR"

    def test_create_message_invalid_json(self):
        """Test creación con JSON inválido - 422."""
        # Act
        response = self.client.post(
            "/api/messages",
            json={"invalid": "data"}
        )

        # Assert
        assert response.status_code == 422
