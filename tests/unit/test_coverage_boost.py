"""

Cubre las áreas con baja cobertura identificadas:
- MessageRepository: métodos sin cobertura (update, count_by_session, get_recent_messages, etc.)
- MessageService: flujos de error, rate limiting, session statistics
- MessageController: endpoints get_session_stats, get_message_by_id
- ContentFilter (utils): remove_word, clear, __repr__, get_word_count
- Main: endpoints health y root
- Database connection: drop_tables
- Schemas y exceptions con baja cobertura
"""

import pytest
import os
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import SQLAlchemyError

from app.models.message import Message
from app.schemas.message import MessageCreate, SenderEnum, MessageMetadata


# =============================================================================
# REPOSITORY TESTS - Cubrir métodos faltantes
# =============================================================================

class TestMessageRepositoryExtended:
    """Tests extendidos para MessageRepository para cubrir gaps de cobertura."""

    def test_get_all_by_session(self, test_db_session):
        """Test obtener todos los mensajes de una sesión sin paginación."""
        from app.repositories.message_repository import MessageRepository

        repo = MessageRepository(test_db_session)
        session_id = "all-messages-session"

        # Crear 5 mensajes
        for i in range(5):
            msg = Message(
                message_id=f"all-msg-{i}",
                session_id=session_id,
                content=f"Message {i}",
                sender="user",
                timestamp=datetime.now(timezone.utc),
                word_count=2,
                character_count=9,
                processed_at=datetime.now(timezone.utc),
            )
            test_db_session.add(msg)
        test_db_session.commit()

        # Act
        messages = repo.get_all_by_session(session_id)

        # Assert
        assert len(messages) == 5
        assert all(m.session_id == session_id for m in messages)

    def test_get_all_by_session_empty(self, test_db_session):
        """Test obtener mensajes de sesión inexistente."""
        from app.repositories.message_repository import MessageRepository

        repo = MessageRepository(test_db_session)
        messages = repo.get_all_by_session("nonexistent-session")

        assert messages == []

    def test_update_success(self, test_db_session):
        """Test actualizar un mensaje exitosamente."""
        from app.repositories.message_repository import MessageRepository

        repo = MessageRepository(test_db_session)

        # Crear mensaje
        msg = Message(
            message_id="update-msg-1",
            session_id="update-session",
            content="Original content",
            sender="user",
            timestamp=datetime.now(timezone.utc),
            word_count=2,
            character_count=16,
            processed_at=datetime.now(timezone.utc),
        )
        test_db_session.add(msg)
        test_db_session.commit()

        # Act
        updated = repo.update("update-msg-1", {"content": "Updated content"})

        # Assert
        assert updated is not None
        assert updated.content == "Updated content"
        assert updated.updated_at is not None

    def test_update_not_found(self, test_db_session):
        """Test actualizar un mensaje inexistente retorna None."""
        from app.repositories.message_repository import MessageRepository

        repo = MessageRepository(test_db_session)
        result = repo.update("nonexistent-msg", {"content": "New content"})

        assert result is None

    def test_update_sqlalchemy_error(self, test_db_session):
        """Test actualización con error de SQLAlchemy hace rollback."""
        from app.repositories.message_repository import MessageRepository

        repo = MessageRepository(test_db_session)

        # Crear mensaje
        msg = Message(
            message_id="update-err-msg",
            session_id="update-err-session",
            content="Content",
            sender="user",
            timestamp=datetime.now(timezone.utc),
            word_count=1,
            character_count=7,
            processed_at=datetime.now(timezone.utc),
        )
        test_db_session.add(msg)
        test_db_session.commit()

        # Forzar error al hacer commit
        with patch.object(test_db_session, "commit", side_effect=SQLAlchemyError("DB error")):
            with pytest.raises(SQLAlchemyError):
                repo.update("update-err-msg", {"content": "fail"})

    def test_count_by_session_no_filter(self, test_db_session):
        """Test contar mensajes por sesión sin filtro de sender."""
        from app.repositories.message_repository import MessageRepository

        repo = MessageRepository(test_db_session)
        session_id = "count-session"

        for i in range(3):
            msg = Message(
                message_id=f"count-msg-{i}",
                session_id=session_id,
                content=f"Msg {i}",
                sender="user" if i < 2 else "system",
                timestamp=datetime.now(timezone.utc),
                word_count=1,
                character_count=5,
                processed_at=datetime.now(timezone.utc),
            )
            test_db_session.add(msg)
        test_db_session.commit()

        count = repo.count_by_session(session_id)
        assert count == 3

    def test_count_by_session_with_sender_filter(self, test_db_session):
        """Test contar mensajes por sesión con filtro de sender."""
        from app.repositories.message_repository import MessageRepository

        repo = MessageRepository(test_db_session)
        session_id = "count-filter-session"

        for i in range(4):
            msg = Message(
                message_id=f"count-filter-{i}",
                session_id=session_id,
                content=f"Msg {i}",
                sender="user" if i < 3 else "system",
                timestamp=datetime.now(timezone.utc),
                word_count=1,
                character_count=5,
                processed_at=datetime.now(timezone.utc),
            )
            test_db_session.add(msg)
        test_db_session.commit()

        user_count = repo.count_by_session(session_id, SenderEnum.USER)
        system_count = repo.count_by_session(session_id, SenderEnum.SYSTEM)

        assert user_count == 3
        assert system_count == 1

    def test_get_recent_messages(self, test_db_session):
        """Test obtener mensajes recientes de una sesión."""
        from app.repositories.message_repository import MessageRepository

        repo = MessageRepository(test_db_session)
        session_id = "recent-session"

        # Crear message reciente
        msg = Message(
            message_id="recent-msg-1",
            session_id=session_id,
            content="Recent message",
            sender="user",
            timestamp=datetime.now(timezone.utc),
            word_count=2,
            character_count=14,
            processed_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        test_db_session.add(msg)
        test_db_session.commit()

        recent = repo.get_recent_messages(session_id, minutes=60)

        assert len(recent) >= 1

    def test_get_recent_messages_empty(self, test_db_session):
        """Test obtener mensajes recientes de sesión vacía."""
        from app.repositories.message_repository import MessageRepository

        repo = MessageRepository(test_db_session)
        recent = repo.get_recent_messages("empty-recent-session", minutes=60)

        assert recent == []

    def test_get_session_stats(self, test_db_session):
        """Test obtener estadísticas de una sesión."""
        from app.repositories.message_repository import MessageRepository

        repo = MessageRepository(test_db_session)
        session_id = "stats-session"

        for i in range(3):
            msg = Message(
                message_id=f"stats-msg-{i}",
                session_id=session_id,
                content=f"Message number {i} for stats",
                sender="user" if i < 2 else "system",
                timestamp=datetime.now(timezone.utc),
                word_count=5,
                character_count=25,
                processed_at=datetime.now(timezone.utc),
            )
            test_db_session.add(msg)
        test_db_session.commit()

        stats = repo.get_session_stats(session_id)

        assert stats["session_id"] == session_id
        assert stats["total_messages"] == 3
        assert stats["total_words"] == 15
        assert stats["total_characters"] == 75
        assert stats["user_messages"] == 2
        assert stats["system_messages"] == 1
        assert stats["first_message_at"] is not None
        assert stats["last_message_at"] is not None

    def test_get_session_stats_empty(self, test_db_session):
        """Test obtener estadísticas de sesión vacía."""
        from app.repositories.message_repository import MessageRepository

        repo = MessageRepository(test_db_session)
        stats = repo.get_session_stats("empty-stats-session")

        assert stats["total_messages"] == 0
        assert stats["total_words"] == 0
        assert stats["total_characters"] == 0

    def test_batch_create_success(self, test_db_session):
        """Test crear múltiples mensajes en batch exitosamente."""
        from app.repositories.message_repository import MessageRepository

        repo = MessageRepository(test_db_session)
        messages_data = []

        for i in range(3):
            messages_data.append({
                "message_id": f"batch-msg-{i}",
                "session_id": "batch-session",
                "content": f"Batch message {i}",
                "sender": "user",
                "timestamp": datetime.now(timezone.utc),
                "word_count": 3,
                "character_count": 15,
                "processed_at": datetime.now(timezone.utc),
            })

        result = repo.batch_create(messages_data)

        assert len(result) == 3
        assert all(isinstance(m, Message) for m in result)

    def test_batch_create_error(self, test_db_session):
        """Test batch create con error hace rollback."""
        from app.repositories.message_repository import MessageRepository

        repo = MessageRepository(test_db_session)

        with patch.object(test_db_session, "commit", side_effect=SQLAlchemyError("Batch error")):
            with pytest.raises(SQLAlchemyError):
                repo.batch_create([{
                    "message_id": "batch-err-1",
                    "session_id": "batch-err-session",
                    "content": "Fail",
                    "sender": "user",
                    "timestamp": datetime.now(timezone.utc),
                    "word_count": 1,
                    "character_count": 4,
                    "processed_at": datetime.now(timezone.utc),
                }])

    def test_get_by_session_with_page_params(self, test_db_session):
        """Test obtener mensajes usando page y page_size en lugar de limit/offset."""
        from app.repositories.message_repository import MessageRepository

        repo = MessageRepository(test_db_session)
        session_id = "page-session"

        for i in range(8):
            msg = Message(
                message_id=f"page-msg-{i}",
                session_id=session_id,
                content=f"Page message {i}",
                sender="user",
                timestamp=datetime.now(timezone.utc) + timedelta(seconds=i),
                word_count=3,
                character_count=14,
                processed_at=datetime.now(timezone.utc),
            )
            test_db_session.add(msg)
        test_db_session.commit()

        # Página 1, tamaño 3
        messages, total = repo.get_by_session(session_id, page=1, page_size=3)

        assert total == 8
        assert len(messages) == 3

        # Página 2, tamaño 3
        messages_p2, total_p2 = repo.get_by_session(session_id, page=2, page_size=3)

        assert total_p2 == 8
        assert len(messages_p2) == 3

    def test_get_by_session_with_sender_filter(self, test_db_session):
        """Test obtener mensajes filtrando por sender."""
        from app.repositories.message_repository import MessageRepository

        repo = MessageRepository(test_db_session)
        session_id = "sender-filter-session"

        for i in range(6):
            msg = Message(
                message_id=f"sf-msg-{i}",
                session_id=session_id,
                content=f"Filter message {i}",
                sender="user" if i < 4 else "system",
                timestamp=datetime.now(timezone.utc),
                word_count=3,
                character_count=16,
                processed_at=datetime.now(timezone.utc),
            )
            test_db_session.add(msg)
        test_db_session.commit()

        user_msgs, user_total = repo.get_by_session(session_id, sender=SenderEnum.USER)
        system_msgs, system_total = repo.get_by_session(session_id, sender=SenderEnum.SYSTEM)

        assert user_total == 4
        assert system_total == 2

    def test_create_message_already_exists_error(self, test_db_session):
        """Test crear mensaje con ID duplicado lanza MessageAlreadyExistsError."""
        from app.repositories.message_repository import MessageRepository
        from app.repositories.exceptions import MessageAlreadyExistsError

        repo = MessageRepository(test_db_session)
        msg_data = MessageCreate(
            session_id="dup-session",
            content="Duplicate test",
            sender=SenderEnum.USER,
            message_id="dup-id-123",
        )
        metadata = {
            "word_count": 2,
            "character_count": 14,
            "processed_at": datetime.now(timezone.utc),
        }

        # Crear el primer mensaje
        repo.create(msg_data, metadata)

        # Intentar crear con mismo ID
        with pytest.raises(MessageAlreadyExistsError):
            repo.create(msg_data, metadata)


# =============================================================================
# SERVICE TESTS - Cubrir flujos de error y métodos faltantes
# =============================================================================

class TestMessageServiceExtended:
    """Tests extendidos para MessageService."""

    def _make_mock_message(self, **overrides):
        """Helper para crear un mock de Message."""
        defaults = {
            "message_id": "svc-msg-1",
            "session_id": "svc-session",
            "content": "Test content",
            "timestamp": datetime.now(timezone.utc),
            "sender": "user",
            "word_count": 2,
            "character_count": 12,
            "processed_at": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        defaults.update(overrides)
        mock_msg = Mock(spec=Message)
        for k, v in defaults.items():
            setattr(mock_msg, k, v)
        return mock_msg

    def test_init_with_session(self):
        """Test inicializar MessageService con sesión de DB (no repositorio)."""
        from app.services.message_service import MessageService

        mock_session = Mock(spec=["query", "add", "commit"])
        # No tiene atributo 'create', así que se tratará como sesión
        service = MessageService(mock_session)

        assert service.repository is not None
        assert service.db == mock_session

    def test_init_with_repository(self):
        """Test inicializar MessageService con repositorio directamente."""
        from app.services.message_service import MessageService

        mock_repo = Mock()
        mock_repo.create = Mock()
        service = MessageService(mock_repo)

        assert service.repository == mock_repo
        assert service.db is None

    def test_get_message_by_id_found(self):
        """Test obtener mensaje por ID cuando existe."""
        from app.services.message_service import MessageService

        mock_repo = Mock()
        mock_msg = self._make_mock_message()
        mock_repo.get_by_id.return_value = mock_msg

        service = MessageService(mock_repo)
        result = service.get_message_by_id("svc-msg-1")

        assert result is not None
        assert result.message_id == "svc-msg-1"
        mock_repo.get_by_id.assert_called_once_with("svc-msg-1")

    def test_get_message_by_id_not_found(self):
        """Test obtener mensaje por ID cuando no existe."""
        from app.services.message_service import MessageService

        mock_repo = Mock()
        mock_repo.get_by_id.return_value = None

        service = MessageService(mock_repo)
        result = service.get_message_by_id("nonexistent")

        assert result is None

    def test_get_messages_by_session(self):
        """Test obtener mensajes por sesión con paginación."""
        from app.services.message_service import MessageService

        mock_repo = Mock()
        mock_msgs = [self._make_mock_message(message_id=f"msg-{i}") for i in range(3)]
        mock_repo.get_by_session.return_value = (mock_msgs, 10)

        service = MessageService(mock_repo)
        result = service.get_messages_by_session("session-1", limit=3, offset=0)

        assert result.total == 10
        assert len(result.messages) == 3
        assert result.has_more is True

    def test_get_messages_by_session_no_more(self):
        """Test obtener mensajes cuando no hay más páginas."""
        from app.services.message_service import MessageService

        mock_repo = Mock()
        mock_msgs = [self._make_mock_message(message_id=f"msg-{i}") for i in range(2)]
        mock_repo.get_by_session.return_value = (mock_msgs, 2)

        service = MessageService(mock_repo)
        result = service.get_messages_by_session("session-1", limit=50, offset=0)

        assert result.has_more is False

    def test_get_session_statistics_with_messages(self):
        """Test obtener estadísticas con mensajes existentes."""
        from app.services.message_service import MessageService

        mock_repo = Mock()
        mock_repo.get_session_stats.return_value = {
            "session_id": "stats-session",
            "total_messages": 10,
            "total_words": 50,
            "total_characters": 300,
            "user_messages": 7,
            "system_messages": 3,
            "first_message_at": datetime.now(timezone.utc),
            "last_message_at": datetime.now(timezone.utc),
        }

        service = MessageService(mock_repo)
        stats = service.get_session_statistics("stats-session")

        assert stats["avg_words_per_message"] == 5.0
        assert stats["avg_chars_per_message"] == 30.0

    def test_get_session_statistics_empty(self):
        """Test obtener estadísticas sin mensajes."""
        from app.services.message_service import MessageService

        mock_repo = Mock()
        mock_repo.get_session_stats.return_value = {
            "session_id": "empty-session",
            "total_messages": 0,
            "total_words": 0,
            "total_characters": 0,
            "user_messages": 0,
            "system_messages": 0,
            "first_message_at": None,
            "last_message_at": None,
        }

        service = MessageService(mock_repo)
        stats = service.get_session_statistics("empty-session")

        assert stats["avg_words_per_message"] == 0
        assert stats["avg_chars_per_message"] == 0

    @pytest.mark.asyncio
    async def test_create_message_already_exists_reraise(self):
        """Test que create_message re-lanza MessageAlreadyExistsError."""
        from app.services.message_service import MessageService
        from app.repositories.exceptions import MessageAlreadyExistsError

        mock_repo = Mock()
        mock_repo.exists.return_value = False
        mock_repo.create.side_effect = MessageAlreadyExistsError("dup-id")
        mock_repo.get_recent_messages.return_value = []

        mock_filter = Mock()
        mock_filter.get_inappropriate_words.return_value = []

        service = MessageService(mock_repo, mock_filter)

        msg_data = MessageCreate(
            session_id="test-session",
            content="Valid content",
            sender=SenderEnum.USER,
        )

        with pytest.raises(MessageAlreadyExistsError):
            await service.create_message(msg_data)

    @pytest.mark.asyncio
    async def test_create_message_generic_exception_wraps(self):
        """Test que create_message envuelve Exception genérica en MessageProcessingError."""
        from app.services.message_service import MessageService
        from app.services.exceptions import MessageProcessingError

        mock_repo = Mock()
        mock_repo.exists.return_value = False
        mock_repo.create.side_effect = RuntimeError("unexpected error")
        mock_repo.get_recent_messages.return_value = []

        mock_filter = Mock()
        mock_filter.get_inappropriate_words.return_value = []

        service = MessageService(mock_repo, mock_filter)

        msg_data = MessageCreate(
            session_id="test-session",
            content="Valid content",
            sender=SenderEnum.USER,
        )

        with pytest.raises(MessageProcessingError) as exc_info:
            await service.create_message(msg_data)
        assert "crear mensaje" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_message_existing_id(self):
        """Test _validate_message lanza error si message_id ya existe."""
        from app.services.message_service import MessageService
        from app.repositories.exceptions import MessageAlreadyExistsError

        mock_repo = Mock()
        mock_repo.exists.return_value = True
        mock_repo.get_recent_messages.return_value = []

        service = MessageService(mock_repo)

        msg_data = MessageCreate(
            session_id="test-session",
            content="Valid content",
            sender=SenderEnum.USER,
            message_id="existing-id",
        )

        with pytest.raises(MessageAlreadyExistsError):
            await service._validate_message(msg_data)


# =============================================================================
# RATE LIMIT TESTS
# =============================================================================

class TestMessageValidatorRateLimit:
    """Tests para validate_rate_limit del MessageValidator."""

    @pytest.mark.asyncio
    async def test_rate_limit_hourly_exceeded(self):
        """Test rate limit por hora excedido."""
        from app.services.message_service import MessageValidator
        from app.services.exceptions import RateLimitExceededError

        validator = MessageValidator()
        mock_repo = Mock()
        mock_repo.get_recent_messages.return_value = [Mock()] * 100

        with pytest.raises(RateLimitExceededError) as exc_info:
            await validator.validate_rate_limit("session-1", mock_repo)
        assert exc_info.value.limit_type == "hora"

    @pytest.mark.asyncio
    async def test_rate_limit_minute_exceeded(self):
        """Test rate limit por minuto excedido."""
        from app.services.message_service import MessageValidator
        from app.services.exceptions import RateLimitExceededError

        validator = MessageValidator()
        mock_repo = Mock()
        # Primero, mensajes recientes en 60 min < 100
        # Luego, mensajes recientes en 1 min >= 10
        mock_repo.get_recent_messages.side_effect = [
            [Mock()] * 50,   # 60 min: 50 (OK)
            [Mock()] * 10,   # 1 min: 10 (EXCEDE)
        ]

        with pytest.raises(RateLimitExceededError) as exc_info:
            await validator.validate_rate_limit("session-1", mock_repo)
        assert exc_info.value.limit_type == "minuto"

    @pytest.mark.asyncio
    async def test_rate_limit_exception_fallthrough(self):
        """Test que excepciones genéricas en rate limit se ignoran silenciosamente."""
        from app.services.message_service import MessageValidator

        validator = MessageValidator()
        mock_repo = Mock()
        mock_repo.get_recent_messages.side_effect = RuntimeError("DB down")

        # No debería lanzar excepción
        await validator.validate_rate_limit("session-1", mock_repo)

    @pytest.mark.asyncio
    async def test_rate_limit_passes(self):
        """Test rate limit pasa cuando está dentro de los límites."""
        from app.services.message_service import MessageValidator

        validator = MessageValidator()
        mock_repo = Mock()
        mock_repo.get_recent_messages.return_value = [Mock()] * 5

        # No debería lanzar excepción
        await validator.validate_rate_limit("session-1", mock_repo)


# =============================================================================
# SERVICE CONTENT FILTER TESTS
# =============================================================================

class TestServiceContentFilter:
    """Tests para ContentFilter en message_service.py."""

    def test_contains_inappropriate_content_true(self):
        """Test detectar contenido inapropiado."""
        from app.services.message_service import ContentFilter

        cf = ContentFilter()
        assert cf.contains_inappropriate_content("This is spam content") is True

    def test_contains_inappropriate_content_false(self):
        """Test contenido apropiado."""
        from app.services.message_service import ContentFilter

        cf = ContentFilter()
        assert cf.contains_inappropriate_content("This is fine") is False

    def test_get_inappropriate_words_service(self):
        """Test obtener palabras inapropiadas encontradas."""
        from app.services.message_service import ContentFilter

        cf = ContentFilter()
        words = cf.get_inappropriate_words("spam and toxic content")

        assert "spam" in words
        assert "toxic" in words

    def test_custom_profanity_words(self):
        """Test con palabras personalizadas."""
        from app.services.message_service import ContentFilter

        cf = ContentFilter(profanity_words=["custom1", "custom2"])
        # Las custom words se suman a las default
        assert cf.contains_inappropriate_content("custom1 message") is True


# =============================================================================
# CONTROLLER TESTS - Cubrir endpoints faltantes
# =============================================================================

class TestMessageControllerExtended:
    """Tests extendidos para endpoints del controller."""

    def setup_method(self):
        """Setup para cada test."""
        from app.main import app
        from fastapi.testclient import TestClient
        self.app = app
        self.client = TestClient(app)

    @patch("app.controllers.message_controller.create_message_service")
    def test_get_session_stats_success(self, mock_create_service):
        """Test obtener estadísticas de sesión exitosamente."""
        mock_service = Mock()
        mock_service.get_session_statistics.return_value = {
            "session_id": "stats-session-1",
            "total_messages": 5,
            "total_words": 25,
            "total_characters": 150,
            "user_messages": 3,
            "system_messages": 2,
            "first_message_at": None,
            "last_message_at": None,
            "avg_words_per_message": 5.0,
            "avg_chars_per_message": 30.0,
        }
        mock_create_service.return_value = mock_service

        response = self.client.get("/api/messages/stats-session-1/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["total_messages"] == 5

    @patch("app.controllers.message_controller.create_message_service")
    def test_get_session_stats_error(self, mock_create_service):
        """Test obtener estadísticas con error interno."""
        mock_create_service.side_effect = Exception("Stats error")

        response = self.client.get("/api/messages/stats-err-session/stats")

        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "INTERNAL_ERROR"

    @patch("app.controllers.message_controller.create_message_service")
    def test_get_message_by_id_success(self, mock_create_service):
        """Test obtener mensaje por ID exitosamente."""
        mock_service = Mock()
        now = datetime.now(timezone.utc)
        mock_response = Mock()
        mock_response.model_dump.return_value = {
            "message_id": "find-msg-1",
            "session_id": "find-session",
            "content": "Found message",
            "timestamp": now.isoformat(),
            "sender": "user",
            "metadata": {
                "word_count": 2,
                "character_count": 13,
                "processed_at": now.isoformat(),
            },
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        # Para FastAPI, el response_model necesita un objeto Pydantic
        from app.schemas.message import MessageResponse, MessageMetadata
        msg_response = MessageResponse(
            message_id="find-msg-1",
            session_id="find-session",
            content="Found message",
            timestamp=now,
            sender=SenderEnum.USER,
            metadata=MessageMetadata(
                word_count=2,
                character_count=13,
                processed_at=now,
            ),
            created_at=now,
            updated_at=now,
        )
        mock_service.get_message_by_id.return_value = msg_response
        mock_create_service.return_value = mock_service

        response = self.client.get("/api/messages/id/find-msg-1")

        assert response.status_code == 200
        data = response.json()
        assert data["message_id"] == "find-msg-1"

    @patch("app.controllers.message_controller.create_message_service")
    def test_get_message_by_id_not_found(self, mock_create_service):
        """Test obtener mensaje por ID cuando no existe."""
        mock_service = Mock()
        mock_service.get_message_by_id.return_value = None
        mock_create_service.return_value = mock_service

        response = self.client.get("/api/messages/id/nonexistent-msg")

        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "MESSAGE_NOT_FOUND"

    @patch("app.controllers.message_controller.create_message_service")
    def test_get_message_by_id_internal_error(self, mock_create_service):
        """Test obtener mensaje por ID con error interno."""
        mock_service = Mock()
        mock_service.get_message_by_id.side_effect = RuntimeError("DB crash")
        mock_create_service.return_value = mock_service

        response = self.client.get("/api/messages/id/error-msg")

        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "INTERNAL_ERROR"

    @patch("app.controllers.message_controller.create_message_service")
    def test_get_messages_by_session_with_sender_filter(self, mock_create_service):
        """Test obtener mensajes filtrando por sender."""
        from app.schemas.message import MessageListResponse, MessageResponse, MessageMetadata

        mock_service = Mock()
        now = datetime.now(timezone.utc)
        msg = MessageResponse(
            message_id="filter-msg-1",
            session_id="filter-session",
            content="Filtered message",
            timestamp=now,
            sender=SenderEnum.USER,
            metadata=MessageMetadata(word_count=2, character_count=16, processed_at=now),
            created_at=now,
            updated_at=now,
        )
        mock_service.get_messages_by_session.return_value = MessageListResponse(
            messages=[msg],
            total=1,
            limit=50,
            offset=0,
            has_more=False,
        )
        mock_create_service.return_value = mock_service

        response = self.client.get("/api/messages/filter-session?sender=user")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @patch("app.controllers.message_controller.create_message_service")
    def test_create_message_duplicate_409(self, mock_create_service):
        """Test crear mensaje con ID duplicado retorna 409."""
        from app.repositories.exceptions import MessageAlreadyExistsError

        mock_service = Mock()
        mock_service.create_message = AsyncMock(
            side_effect=MessageAlreadyExistsError("dup-msg-id")
        )
        mock_create_service.return_value = mock_service

        response = self.client.post(
            "/api/messages",
            json={
                "session_id": "test-session",
                "content": "Duplicate test message",
                "sender": "user",
                "message_id": "dup-msg-id",
            },
        )

        assert response.status_code == 409
        data = response.json()
        assert data["error"]["code"] == "DUPLICATE_MESSAGE"


# =============================================================================
# CONTENT FILTER UTILS TESTS
# =============================================================================

class TestContentFilterUtils:
    """Tests para métodos faltantes de ContentFilter en utils."""

    def test_remove_word_exists(self):
        """Test remover palabra que existe."""
        from app.utils.content_filter import ContentFilter

        cf = ContentFilter(custom_words=["spam", "malware", "test"])
        result = cf.remove_word("spam")

        assert result is True
        assert "spam" not in cf.inappropriate_words

    def test_remove_word_not_exists(self):
        """Test remover palabra que no existe."""
        from app.utils.content_filter import ContentFilter

        cf = ContentFilter(custom_words=["spam"])
        result = cf.remove_word("nonexistent")

        assert result is False

    def test_clear(self):
        """Test limpiar todas las palabras del filtro."""
        from app.utils.content_filter import ContentFilter

        cf = ContentFilter()
        cf.clear()

        assert len(cf.inappropriate_words) == 0
        assert cf.get_word_count() == 0

    def test_repr(self):
        """Test representación string del filtro."""
        from app.utils.content_filter import ContentFilter

        cf = ContentFilter(custom_words=["a", "b", "c"])
        repr_str = repr(cf)

        assert "ContentFilter" in repr_str
        assert "3" in repr_str

    def test_get_word_count(self):
        """Test contar palabras en el filtro."""
        from app.utils.content_filter import ContentFilter

        cf = ContentFilter(custom_words=["one", "two", "three"])
        assert cf.get_word_count() == 3

    def test_is_appropriate_empty_content(self):
        """Test contenido vacío es apropiado."""
        from app.utils.content_filter import ContentFilter

        cf = ContentFilter()
        assert cf.is_appropriate("") is True
        assert cf.is_appropriate("   ") is True

    def test_get_inappropriate_words_empty_content(self):
        """Test obtener palabras inapropiadas de contenido vacío."""
        from app.utils.content_filter import ContentFilter

        cf = ContentFilter()
        words = cf.get_inappropriate_words("")

        assert words == []

    def test_get_inappropriate_words_whitespace_content(self):
        """Test obtener palabras inapropiadas de contenido con solo espacios."""
        from app.utils.content_filter import ContentFilter

        cf = ContentFilter()
        words = cf.get_inappropriate_words("   \t\n  ")

        assert words == []


# =============================================================================
# MAIN APP TESTS
# =============================================================================

class TestMainEndpoints:
    """Tests para endpoints de main.py."""

    def setup_method(self):
        from app.main import app
        from fastapi.testclient import TestClient
        self.client = TestClient(app)

    def test_health_check(self):
        """Test endpoint de health check."""
        response = self.client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_root_endpoint(self):
        """Test endpoint raíz."""
        response = self.client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data
        assert "version" in data


# =============================================================================
# DATABASE CONNECTION TESTS
# =============================================================================

class TestDatabaseConnectionExtended:
    """Tests extendidos para conexión de base de datos."""

    def test_drop_tables(self):
        """Test drop_tables se ejecuta sin error."""
        from app.database.connection import drop_tables, create_tables, Base

        # Verificar que no lanza excepción
        drop_tables()

        # Recrear tablas para que otros tests no fallen
        create_tables()


# =============================================================================
# EXCEPTIONS TESTS
# =============================================================================

class TestExceptionsExtended:
    """Tests extendidos para excepciones."""

    def test_message_not_found_error(self):
        """Test MessageNotFoundError."""
        from app.repositories.exceptions import MessageNotFoundError

        error = MessageNotFoundError("msg-404")

        assert error.message_id == "msg-404"
        assert "msg-404" in str(error)

    def test_database_transaction_error_without_original(self):
        """Test DatabaseTransactionError sin error original."""
        from app.repositories.exceptions import DatabaseTransactionError

        error = DatabaseTransactionError("insert")

        assert error.operation == "insert"
        assert error.original_error is None
        assert "insert" in str(error)

    def test_database_transaction_error_with_original(self):
        """Test DatabaseTransactionError con error original."""
        from app.repositories.exceptions import DatabaseTransactionError

        original = ValueError("bad value")
        error = DatabaseTransactionError("update", original)

        assert error.original_error == original
        assert "bad value" in str(error)


# =============================================================================
# SCHEMA TESTS
# =============================================================================

class TestSchemaExtended:
    """Tests extendidos para schemas."""

    def test_error_detail_creation(self):
        """Test crear ErrorDetail."""
        from app.schemas.message import ErrorDetail

        detail = ErrorDetail(code="TEST_ERROR", message="Test error message")

        assert detail.code == "TEST_ERROR"
        assert detail.message == "Test error message"
        assert detail.details is None

    def test_error_detail_with_details(self):
        """Test crear ErrorDetail con detalles."""
        from app.schemas.message import ErrorDetail

        detail = ErrorDetail(
            code="ERR", message="Error", details="Extra info"
        )

        assert detail.details == "Extra info"

    def test_error_response_creation(self):
        """Test crear ErrorResponse."""
        from app.schemas.message import ErrorResponse, ErrorDetail

        response = ErrorResponse(
            error=ErrorDetail(code="TEST", message="Test error")
        )

        assert response.status == "error"
        assert response.error.code == "TEST"

    def test_validation_error_response_creation(self):
        """Test crear ValidationErrorResponse."""
        from app.schemas.message import ValidationErrorResponse, ErrorDetail

        response = ValidationErrorResponse(
            error=ErrorDetail(code="VALIDATION", message="Validation failed"),
            validation_errors=[{"field": "content", "message": "required"}],
        )

        assert response.status == "error"
        assert len(response.validation_errors) == 1


# =============================================================================
# MODEL TESTS - to_dict con Nones
# =============================================================================

class TestMessageModelExtended:
    """Tests extendidos para modelo Message."""

    def test_to_dict_full(self, test_db_session):
        """Test to_dict con todos los campos."""
        now = datetime.now(timezone.utc)
        msg = Message(
            message_id="dict-msg-1",
            session_id="dict-session",
            content="Dict test",
            sender="user",
            timestamp=now,
            word_count=2,
            character_count=9,
            processed_at=now,
            created_at=now,
            updated_at=now,
        )

        d = msg.to_dict()

        assert d["message_id"] == "dict-msg-1"
        assert d["timestamp"] is not None
        assert d["metadata"]["word_count"] == 2
        assert d["created_at"] is not None
        assert d["updated_at"] is not None

    def test_to_dict_with_none_timestamps(self):
        """Test to_dict cuando timestamps son None."""
        msg = Message(
            message_id="dict-none-1",
            session_id="dict-none-session",
            content="None test",
            sender="user",
            timestamp=None,
            word_count=2,
            character_count=9,
            processed_at=None,
            created_at=None,
            updated_at=None,
        )

        d = msg.to_dict()

        assert d["timestamp"] is None
        assert d["metadata"]["processed_at"] is None
        assert d["created_at"] is None
        assert d["updated_at"] is None

    def test_repr(self, test_db_session):
        """Test representación string del modelo."""
        msg = Message(
            message_id="repr-msg-1",
            session_id="repr-session",
            content="Repr test",
            sender="user",
            timestamp=datetime.now(timezone.utc),
            word_count=2,
            character_count=9,
            processed_at=datetime.now(timezone.utc),
        )

        repr_str = repr(msg)

        assert "repr-msg-1" in repr_str
        assert "Message" in repr_str
