"""
Tests para las excepciones del servicio de mensajes (services/exceptions).
Cubre todas las clases de excepción .
"""
import pytest

from app.services.exceptions import (
    MessageServiceError,
    ContentFilterError,
    InappropriateContentError,
    RateLimitExceededError,
    MessageValidationError,
    UnauthorizedSenderError,
    MessageProcessingError
)


class TestMessageServiceError:
    """Tests para la excepción base MessageServiceError."""
    
    def test_inheritance(self):
        """Test que hereda de Exception."""
        # Arrange & Act
        error = MessageServiceError("Test error")
        
        # Assert
        assert isinstance(error, Exception)
        assert isinstance(error, MessageServiceError)

    def test_message(self):
        """Test que maneja mensaje correctamente."""
        # Arrange
        message = "Test error message"
        
        # Act
        error = MessageServiceError(message)
        
        # Assert
        assert str(error) == message

    def test_can_be_raised(self):
        """Test que puede ser lanzada y capturada."""
        # Arrange & Act & Assert
        with pytest.raises(MessageServiceError) as exc_info:
            raise MessageServiceError("Test error")
        
        assert str(exc_info.value) == "Test error"


class TestContentFilterError:
    """Tests para ContentFilterError."""
    
    def test_inheritance(self):
        """Test que hereda de MessageServiceError."""
        # Arrange & Act
        error = ContentFilterError("Test error")
        
        # Assert
        assert isinstance(error, MessageServiceError)
        assert isinstance(error, ContentFilterError)

    def test_init_with_message_only(self):
        """Test inicialización solo con mensaje."""
        # Arrange
        message = "Content filter error"
        
        # Act
        error = ContentFilterError(message)
        
        # Assert
        assert str(error) == message
        assert error.inappropriate_words == []

    def test_init_with_message_and_words(self):
        """Test inicialización con mensaje y palabras inapropiadas."""
        # Arrange
        message = "Content blocked"
        words = ["bad", "inappropriate"]
        
        # Act
        error = ContentFilterError(message, words)
        
        # Assert
        assert str(error) == message
        assert error.inappropriate_words == words

    def test_init_with_none_words(self):
        """Test inicialización con palabras None."""
        # Arrange
        message = "Content error"
        
        # Act
        error = ContentFilterError(message, None)
        
        # Assert
        assert str(error) == message
        assert error.inappropriate_words == []

    def test_can_be_raised(self):
        """Test que puede ser lanzada y capturada."""
        # Arrange & Act & Assert
        with pytest.raises(ContentFilterError) as exc_info:
            raise ContentFilterError("Filter error", ["bad"])
        
        assert "Filter error" in str(exc_info.value)
        assert exc_info.value.inappropriate_words == ["bad"]


class TestInappropriateContentError:
    """Tests para InappropriateContentError."""
    
    def test_inheritance(self):
        """Test que hereda de ContentFilterError."""
        # Arrange & Act
        error = InappropriateContentError(["bad"])
        
        # Assert
        assert isinstance(error, ContentFilterError)
        assert isinstance(error, InappropriateContentError)

    def test_init_single_word(self):
        """Test inicialización con una palabra."""
        # Arrange
        words = ["inappropriate"]
        
        # Act
        error = InappropriateContentError(words)
        
        # Assert
        expected_message = "Contenido inapropiado detectado: inappropriate"
        assert str(error) == expected_message
        assert error.inappropriate_words == words

    def test_init_multiple_words(self):
        """Test inicialización con múltiples palabras."""
        # Arrange
        words = ["bad", "inappropriate", "offensive"]
        
        # Act
        error = InappropriateContentError(words)
        
        # Assert
        expected_message = "Contenido inapropiado detectado: bad, inappropriate, offensive"
        assert str(error) == expected_message
        assert error.inappropriate_words == words

    def test_init_empty_list(self):
        """Test inicialización con lista vacía."""
        # Arrange
        words = []
        
        # Act
        error = InappropriateContentError(words)
        
        # Assert
        expected_message = "Contenido inapropiado detectado: "
        assert str(error) == expected_message
        assert error.inappropriate_words == words

    def test_can_be_raised(self):
        """Test que puede ser lanzada y capturada."""
        # Arrange & Act & Assert
        with pytest.raises(InappropriateContentError) as exc_info:
            raise InappropriateContentError(["test", "words"])
        
        assert "Contenido inapropiado detectado: test, words" in str(exc_info.value)
        assert exc_info.value.inappropriate_words == ["test", "words"]


class TestRateLimitExceededError:
    """Tests para RateLimitExceededError."""
    
    def test_inheritance(self):
        """Test que hereda de MessageServiceError."""
        # Arrange & Act
        error = RateLimitExceededError("per_minute", 101, 100)
        
        # Assert
        assert isinstance(error, MessageServiceError)
        assert isinstance(error, RateLimitExceededError)

    def test_init_with_parameters(self):
        """Test inicialización con todos los parámetros.""" 
        # Arrange
        limit_type = "per_minute"
        current_count = 150
        max_allowed = 100
        
        # Act
        error = RateLimitExceededError(limit_type, current_count, max_allowed)
        
        # Assert
        expected_message = "Límite de per_minute excedido: 150/100"
        assert str(error) == expected_message
        assert error.limit_type == limit_type
        assert error.current_count == current_count
        assert error.max_allowed == max_allowed

    def test_init_different_limit_types(self):
        """Test con diferentes tipos de límite."""
        # Test cases
        test_cases = [
            ("per_second", 11, 10),
            ("per_hour", 1001, 1000),
            ("daily", 50001, 50000)
        ]
        
        for limit_type, current, max_val in test_cases:
            # Act
            error = RateLimitExceededError(limit_type, current, max_val)
            
            # Assert
            expected_message = f"Límite de {limit_type} excedido: {current}/{max_val}"
            assert str(error) == expected_message
            assert error.limit_type == limit_type
            assert error.current_count == current
            assert error.max_allowed == max_val

    def test_can_be_raised(self):
        """Test que puede ser lanzada y capturada."""
        # Arrange & Act & Assert
        with pytest.raises(RateLimitExceededError) as exc_info:
            raise RateLimitExceededError("test_limit", 5, 3)
        
        assert "Límite de test_limit excedido: 5/3" in str(exc_info.value)
        assert exc_info.value.current_count == 5
        assert exc_info.value.max_allowed == 3


class TestMessageValidationError:
    """Tests para MessageValidationError."""
    
    def test_inheritance(self):
        """Test que hereda de MessageServiceError."""
        # Arrange & Act
        error = MessageValidationError(["Error 1"])
        
        # Assert
        assert isinstance(error, MessageServiceError)
        assert isinstance(error, MessageValidationError)

    def test_init_single_error(self):
        """Test inicialización con un error."""
        # Arrange
        errors = ["Content cannot be empty"]
        
        # Act
        error = MessageValidationError(errors)
        
        # Assert
        expected_message = "Errores de validación: Content cannot be empty"
        assert str(error) == expected_message
        assert error.validation_errors == errors

    def test_init_multiple_errors(self):
        """Test inicialización con múltiples errores."""
        # Arrange
        errors = [
            "Content cannot be empty",
            "Sender must be user or system", 
            "Session ID is required"
        ]
        
        # Act
        error = MessageValidationError(errors)
        
        # Assert
        expected_message = "Errores de validación: Content cannot be empty; Sender must be user or system; Session ID is required"
        assert str(error) == expected_message
        assert error.validation_errors == errors

    def test_init_empty_errors(self):
        """Test inicialización con lista vacía de errores."""
        # Arrange
        errors = []
        
        # Act
        error = MessageValidationError(errors)
        
        # Assert
        expected_message = "Errores de validación: "
        assert str(error) == expected_message
        assert error.validation_errors == errors

    def test_can_be_raised(self):
        """Test que puede ser lanzada y capturada."""
        # Arrange & Act & Assert
        with pytest.raises(MessageValidationError) as exc_info:
            raise MessageValidationError(["Error 1", "Error 2"])
        
        assert "Errores de validación: Error 1; Error 2" in str(exc_info.value)
        assert exc_info.value.validation_errors == ["Error 1", "Error 2"]


class TestUnauthorizedSenderError:
    """Tests para UnauthorizedSenderError."""
    
    def test_inheritance(self):
        """Test que hereda de MessageServiceError."""
        # Arrange & Act
        error = UnauthorizedSenderError("test_user", "session_123")
        
        # Assert
        assert isinstance(error, MessageServiceError)
        assert isinstance(error, UnauthorizedSenderError)

    def test_init_with_parameters(self):
        """Test inicialización con parámetros."""
        # Arrange
        sender = "unauthorized_user"
        session_id = "session_abc123"
        
        # Act
        error = UnauthorizedSenderError(sender, session_id)
        
        # Assert
        expected_message = f"Sender '{sender}' no autorizado para sesión '{session_id}'"
        assert str(error) == expected_message
        assert error.sender == sender
        assert error.session_id == session_id

    def test_init_with_different_values(self):
        """Test con diferentes valores de sender y session."""
        # Test cases
        test_cases = [
            ("admin", "admin_session"),
            ("guest_user", "temp_session_456"),
            ("system", "system_session")
        ]
        
        for sender, session_id in test_cases:
            # Act
            error = UnauthorizedSenderError(sender, session_id)
            
            # Assert
            expected_message = f"Sender '{sender}' no autorizado para sesión '{session_id}'"
            assert str(error) == expected_message
            assert error.sender == sender
            assert error.session_id == session_id

    def test_can_be_raised(self):
        """Test que puede ser lanzada y capturada."""
        # Arrange & Act & Assert
        with pytest.raises(UnauthorizedSenderError) as exc_info:
            raise UnauthorizedSenderError("bad_user", "protected_session")
        
        assert "Sender 'bad_user' no autorizado para sesión 'protected_session'" in str(exc_info.value)
        assert exc_info.value.sender == "bad_user"
        assert exc_info.value.session_id == "protected_session"


class TestMessageProcessingError:
    """Tests para MessageProcessingError."""
    
    def test_inheritance(self):
        """Test que hereda de MessageServiceError."""
        # Arrange & Act
        error = MessageProcessingError("test_operation")
        
        # Assert
        assert isinstance(error, MessageServiceError)
        assert isinstance(error, MessageProcessingError)

    def test_init_operation_only(self):
        """Test inicialización solo con operación."""
        # Arrange
        operation = "database_insert"
        
        # Act
        error = MessageProcessingError(operation)
        
        # Assert
        expected_message = f"Error durante {operation}"
        assert str(error) == expected_message
        assert error.operation == operation
        assert error.original_error is None

    def test_init_with_original_error(self):
        """Test inicialización con error original."""
        # Arrange
        operation = "content_filtering"
        original_error = ValueError("Invalid content format")
        
        # Act
        error = MessageProcessingError(operation, original_error)
        
        # Assert
        expected_message = f"Error durante {operation}: Invalid content format"
        assert str(error) == expected_message
        assert error.operation == operation
        assert error.original_error == original_error

    def test_init_with_none_original_error(self):
        """Test inicialización con error original None."""
        # Arrange
        operation = "validation"
        
        # Act
        error = MessageProcessingError(operation, None)
        
        # Assert
        expected_message = f"Error durante {operation}"
        assert str(error) == expected_message
        assert error.operation == operation
        assert error.original_error is None

    def test_init_with_different_error_types(self):
        """Test con diferentes tipos de errores originales."""
        # Test cases
        original_errors = [
            Exception("Generic error"),
            ValueError("Value error"),
            RuntimeError("Runtime error"),
            TimeoutError("Timeout occurred")
        ]
        
        operation = "test_operation"
        
        for original_error in original_errors:
            # Act
            error = MessageProcessingError(operation, original_error)
            
            # Assert
            expected_message = f"Error durante {operation}: {str(original_error)}"
            assert str(error) == expected_message
            assert error.operation == operation
            assert error.original_error == original_error

    def test_can_be_raised(self):
        """Test que puede ser lanzada y capturada."""
        # Arrange
        original_error = ConnectionError("Database connection lost")
        
        # Act & Assert
        with pytest.raises(MessageProcessingError) as exc_info:
            raise MessageProcessingError("db_transaction", original_error)
        
        assert "Error durante db_transaction: Database connection lost" in str(exc_info.value)
        assert exc_info.value.operation == "db_transaction"
        assert exc_info.value.original_error == original_error