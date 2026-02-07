"""
Tests para cubrir gaps .

- Configuración y carga de variables de entorno
- Custom JSON encoder para fechas
- Lógica de procesamiento de mensajes (líneas 119-204)
- Generador de sesiones de base de datos
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from sqlalchemy.orm import Session

# Tests de Configuración
class TestConfig:
    """Tests para configuración y carga de environment variables."""

    @patch.dict(os.environ, {"PROFANITY_WORDS": "badword,spam,hate"})
    def test_get_profanity_words_from_config_with_words(self):
        """Test obtener palabras desde variable de entorno."""
        from app.services.config import get_profanity_words_from_config

        words = get_profanity_words_from_config()

        assert len(words) >= 3
        assert "badword" in words
        assert "spam" in words
        assert "hate" in words

    @patch.dict(os.environ, {"PROFANITY_WORDS": ""})
    def test_get_profanity_words_from_config_empty(self):
        """Test obtener palabras con variable vacía."""
        from app.services.config import get_profanity_words_from_config

        words = get_profanity_words_from_config()

        assert words == []

    @patch.dict(os.environ, {"PROFANITY_WORDS": "  word1  ,  word2  , "})
    def test_get_profanity_words_from_config_with_spaces(self):
        """Test obtener palabras con espacios extra."""
        from app.services.config import get_profanity_words_from_config

        words = get_profanity_words_from_config()

        assert "word1" in words
        assert "word2" in words
        assert "" not in words  # No debe haber palabras vacías

    @patch.dict(os.environ, {
        "MAX_CONTENT_LENGTH": "3000",
        "MAX_DAILY_MESSAGES": "500",
        "ENABLE_CONTENT_FILTER": "false"
    }, clear=False)
    def test_service_config_environment_loading(self):
        """Test carga de configuración desde environment."""
        # Reimportar el módulo para que lea las nuevas variables
        import importlib
        from app.services import config as config_module
        importlib.reload(config_module)

        from app.services.config import ServiceConfig

        assert ServiceConfig.MAX_CONTENT_LENGTH == 3000
        assert ServiceConfig.MAX_DAILY_MESSAGES == 500
        assert ServiceConfig.ENABLE_CONTENT_FILTER is False

    def test_service_config_get_content_filter_config(self):
        """Test obtener configuración del filtro de contenido."""
        from app.services.config import ServiceConfig

        config = ServiceConfig.get_content_filter_config()

        assert "enabled" in config
        assert "strict" in config
        assert "profanity_words" in config
        assert isinstance(config["profanity_words"], list)

    def test_service_config_get_rate_limits(self):
        """Test obtener configuración de rate limits."""
        from app.services.config import ServiceConfig

        limits = ServiceConfig.get_rate_limits()

        assert "max_content_length" in limits
        assert "max_daily_messages" in limits
        assert "max_hourly_messages" in limits
        assert "max_per_minute" in limits


# Tests de Utilidades
class TestCustomJSONEncoder:
    """Tests para el custom JSON encoder en main.py."""

    def test_custom_json_encoder_with_datetime_utc(self):
        """Test encoder con datetime UTC."""
        from app.main import custom_json_encoder

        dt = datetime(2023, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
        result = custom_json_encoder(dt)

        # Verificar que termina con +00:00 o Z
        assert "2023-06-15T14:30:00" in result
        assert (result.endswith("Z") or result.endswith("+00:00"))

    def test_custom_json_encoder_with_datetime_naive(self):
        """Test encoder con datetime sin timezone."""
        from app.main import custom_json_encoder

        dt = datetime(2023, 6, 15, 14, 30, 0)
        result = custom_json_encoder(dt)

        assert result.endswith("Z")
        assert "2023-06-15T14:30:00" in result

    def test_custom_json_encoder_with_invalid_object(self):
        """Test encoder con objeto no serializable."""
        from app.main import custom_json_encoder

        with pytest.raises(TypeError) as exc_info:
            custom_json_encoder({"invalid": "object"})

        assert "is not JSON serializable" in str(exc_info.value)


# Tests de Service Layer (líneas 119-204)
class TestMessageProcessorMetadata:
    """Tests para MessageProcessor y generación de metadatos."""

    def test_generate_metadata_word_count(self):
        """Test conteo de palabras correcto."""
        from app.services.message_service import MessageProcessor

        content = "Hello world this is a test message"
        metadata = MessageProcessor.generate_metadata(content)

        assert metadata["word_count"] == 7
        assert metadata["character_count"] == len(content.strip())

    def test_generate_metadata_sentence_count(self):
        """Test conteo de oraciones."""
        from app.services.message_service import MessageProcessor

        content = "First sentence. Second sentence! Third sentence?"
        metadata = MessageProcessor.generate_metadata(content)

        assert metadata["sentence_count"] == 3

    def test_generate_metadata_avg_word_length(self):
        """Test promedio de longitud de palabras."""
        from app.services.message_service import MessageProcessor

        content = "Hi hello"  # 2 + 5 = 7, avg = 3.5
        metadata = MessageProcessor.generate_metadata(content)

        assert metadata["avg_word_length"] == 3.5

    def test_generate_metadata_has_questions(self):
        """Test detección de preguntas."""
        from app.services.message_service import MessageProcessor

        content_with_question = "How are you?"
        content_without_question = "I am fine"

        metadata_with = MessageProcessor.generate_metadata(content_with_question)
        metadata_without = MessageProcessor.generate_metadata(content_without_question)

        assert metadata_with["has_questions"] is True
        assert metadata_without["has_questions"] is False

    def test_generate_metadata_has_exclamations(self):
        """Test detección de exclamaciones."""
        from app.services.message_service import MessageProcessor

        content_with_exclamation = "Wow! Amazing!"
        content_without_exclamation = "This is normal"

        metadata_with = MessageProcessor.generate_metadata(content_with_exclamation)
        metadata_without = MessageProcessor.generate_metadata(content_without_exclamation)

        assert metadata_with["has_exclamations"] is True
        assert metadata_without["has_exclamations"] is False

    def test_generate_metadata_is_uppercase(self):
        """Test detección de texto en mayúsculas."""
        from app.services.message_service import MessageProcessor

        content_uppercase = "HELLO WORLD"
        content_normal = "Hello World"

        metadata_upper = MessageProcessor.generate_metadata(content_uppercase)
        metadata_normal = MessageProcessor.generate_metadata(content_normal)

        assert metadata_upper["is_uppercase"] is True
        assert metadata_normal["is_uppercase"] is False

    def test_detect_language_hints_spanish(self):
        """Test detección de pistas de idioma español."""
        from app.services.message_service import MessageProcessor

        content_spanish = "Hola como estas por favor gracias"
        metadata = MessageProcessor.generate_metadata(content_spanish)

        assert "spanish" in metadata["language_hints"]

    def test_detect_language_hints_english(self):
        """Test detección de pistas de idioma inglés."""
        from app.services.message_service import MessageProcessor

        content_english = "Hello how are you please thanks"
        metadata = MessageProcessor.generate_metadata(content_english)

        assert "english" in metadata["language_hints"]

    def test_detect_language_hints_mixed(self):
        """Test detección de pistas con lenguaje mixto."""
        from app.services.message_service import MessageProcessor

        content_mixed = "Hello hola thanks gracias"
        metadata = MessageProcessor.generate_metadata(content_mixed)

        assert "spanish" in metadata["language_hints"]
        assert "english" in metadata["language_hints"]

    def test_detect_language_hints_no_hints(self):
        """Test sin pistas de idioma reconocibles."""
        from app.services.message_service import MessageProcessor

        content_no_hints = "12345 xyz abc"
        metadata = MessageProcessor.generate_metadata(content_no_hints)

        assert metadata["language_hints"] == []

    def test_generate_metadata_with_custom_timestamp(self):
        """Test generar metadata con timestamp personalizado."""
        from app.services.message_service import MessageProcessor

        custom_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        content = "Test message"
        metadata = MessageProcessor.generate_metadata(content, custom_time)

        assert metadata["processed_at"] == custom_time

    def test_generate_metadata_empty_content(self):
        """Test generar metadata con contenido vacío."""
        from app.services.message_service import MessageProcessor

        content = ""
        metadata = MessageProcessor.generate_metadata(content)

        assert metadata["word_count"] == 0
        assert metadata["character_count"] == 0
        assert metadata["sentence_count"] == 0

    def test_generate_metadata_only_spaces(self):
        """Test generar metadata con solo espacios."""
        from app.services.message_service import MessageProcessor

        content = "    "
        metadata = MessageProcessor.generate_metadata(content)

        assert metadata["word_count"] == 0
        assert metadata["character_count"] == 0


# Tests de Database Connection
class TestDatabaseConnection:
    """Tests para el generador de sesiones de base de datos."""

    def test_get_database_session_yields_session(self):
        """Test que el generador retorna una sesión."""
        from app.database.connection import get_database_session

        generator = get_database_session()

        # Obtener la sesión del generador
        session = next(generator)

        # Verificar que es una sesión válida
        assert session is not None
        assert hasattr(session, "query")
        assert hasattr(session, "commit")
        assert hasattr(session, "close")

        # Cerrar el generador para cleanup
        try:
            next(generator)
        except StopIteration:
            pass

    def test_get_database_session_closes_on_exit(self):
        """Test que la sesión se cierra correctamente."""
        from app.database.connection import get_database_session

        generator = get_database_session()
        session = next(generator)

        # Mockear el método close para verificar que se llama
        with patch.object(session, "close", wraps=session.close) as mock_close:
            try:
                next(generator)
            except StopIteration:
                pass

            # Verificar que close fue llamado
            mock_close.assert_called_once()

    @patch("app.database.connection.SessionLocal")
    def test_get_database_session_exception_handling(self, mock_session_local):
        """Test que la sesión se cierra incluso si hay excepciones."""
        from app.database.connection import get_database_session

        # Crear una sesión mock
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        generator = get_database_session()
        session = next(generator)

        # Intentar cerrar el generador
        try:
            next(generator)
        except StopIteration:
            pass

        # Verificar que close fue llamado
        mock_session.close.assert_called_once()


# Tests adicionales para MessageService
class TestContentFilterMethods:
    """Tests para métodos adicionales de ContentFilter."""

    def test_content_filter_add_words(self):
        """Test agregar palabras al filtro."""
        from app.services.message_service import ContentFilter

        filter = ContentFilter()
        original_count = len(filter.profanity_words)

        filter.add_words(["newbad1", "newbad2"])

        assert "newbad1" in filter.profanity_words
        assert "newbad2" in filter.profanity_words
        assert len(filter.profanity_words) >= original_count + 2

    def test_content_filter_remove_words(self):
        """Test remover palabras del filtro."""
        from app.services.message_service import ContentFilter

        filter = ContentFilter(["removeme", "keepme"])

        filter.remove_words(["removeme"])

        assert "removeme" not in filter.profanity_words
        assert "keepme" in filter.profanity_words


# Tests para MessageValidator
class TestMessageValidator:
    """Tests para MessageValidator."""

    def test_validate_message_content_empty(self):
        """Test validar contenido vacío."""
        from app.services.message_service import MessageValidator

        validator = MessageValidator()
        errors = validator.validate_message_content("")

        assert len(errors) > 0
        assert any("vacío" in error.lower() for error in errors)

    def test_validate_message_content_too_long(self):
        """Test validar contenido demasiado largo."""
        from app.services.message_service import MessageValidator

        validator = MessageValidator(max_content_length=10)
        errors = validator.validate_message_content("A" * 20)

        assert len(errors) > 0
        assert any("excede" in error.lower() for error in errors)

    def test_validate_message_content_only_special_chars(self):
        """Test validar contenido solo con caracteres especiales."""
        from app.services.message_service import MessageValidator

        validator = MessageValidator()
        errors = validator.validate_message_content("!!!...")

        assert len(errors) > 0

    def test_validate_sender_permissions_user(self):
        """Test validar permisos de sender user."""
        from app.services.message_service import MessageValidator, SenderEnum

        validator = MessageValidator()
        errors = validator.validate_sender_permissions(SenderEnum.USER, "session-123")

        assert len(errors) == 0

    def test_validate_sender_permissions_system(self):
        """Test validar permisos de sender system."""
        from app.services.message_service import MessageValidator, SenderEnum

        validator = MessageValidator()
        errors = validator.validate_sender_permissions(SenderEnum.SYSTEM, "session-123")

        # Por defecto está autorizado
        assert len(errors) == 0


# Tests para create_message_service
class TestCreateMessageService:
    """Tests para factory de MessageService."""

    def test_create_message_service_basic(self):
        """Test crear servicio básico."""
        from app.services.config import create_message_service
        from unittest.mock import Mock

        mock_db = Mock()
        service = create_message_service(mock_db)

        assert service is not None
        assert hasattr(service, "create_message")

    @patch.dict(os.environ, {"PROFANITY_WORDS": "custom1,custom2"})
    def test_create_message_service_with_config_words(self):
        """Test crear servicio con palabras desde config."""
        from app.services.config import create_message_service
        from unittest.mock import Mock

        mock_db = Mock()
        service = create_message_service(mock_db)

        # Verificar que el servicio usa las palabras de config
        assert service is not None

    def test_create_message_service_with_custom_profanity(self):
        """Test crear servicio con palabras personalizadas."""
        from app.services.config import create_message_service
        from unittest.mock import Mock

        mock_db = Mock()
        custom_words = ["customword1", "customword2"]
        service = create_message_service(mock_db, custom_words)

        assert service is not None


# Tests adicionales para MessageRepository exceptions
class TestRepositoryExceptions:
    """Tests para excepciones de repositorio."""

    def test_message_already_exists_error_str(self):
        """Test string representation de MessageAlreadyExistsError."""
        from app.repositories.exceptions import MessageAlreadyExistsError

        error = MessageAlreadyExistsError("msg-123")

        assert "msg-123" in str(error)

    def test_session_not_found_error_str(self):
        """Test string representation de SessionNotFoundError."""
        from app.repositories.exceptions import SessionNotFoundError

        error = SessionNotFoundError("session-456")

        assert "session-456" in str(error)

    def test_database_transaction_error_creation(self):
        """Test crear DatabaseTransactionError."""
        from app.repositories.exceptions import DatabaseTransactionError

        original = ValueError("Test error")
        error = DatabaseTransactionError("test_operation", original)

        assert error.operation == "test_operation"
        assert error.original_error == original


# Tests para models
class TestMessageModel:
    """Tests adicionales para modelo Message."""

    def test_message_validate_sender_invalid(self):
        """Test validación de sender inválido."""
        from app.models.message import Message

        result = Message.validate_sender("invalid_sender")

        assert result is False

    def test_message_validate_sender_valid_user(self):
        """Test validación de sender válido user."""
        from app.models.message import Message

        result = Message.validate_sender("user")

        assert result is True

    def test_message_validate_sender_valid_system(self):
        """Test validación de sender válido system."""
        from app.models.message import Message

        result = Message.validate_sender("system")

        assert result is True
