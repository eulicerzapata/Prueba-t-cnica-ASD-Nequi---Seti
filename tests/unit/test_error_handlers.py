"""
Tests para el módulo de manejo de errores (error_handlers).
Cubre todas las funciones y manejadores de errores .
"""
import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import JSONResponse

from app.error_handlers import (
    translate_validation_message,
    setup_error_handlers,
    configure_logging
)


class TestTranslateValidationMessage:
    """Tests para la función de traducción de mensajes de validación."""
    
    def test_direct_translations_exact_match(self):
        """Test traducciones directas exactas."""
        # Arrange & Act & Assert
        assert translate_validation_message(
            "Input should be 'user' or 'system'", "enum"
        ) == "debe ser 'user' o 'system'"
        
        assert translate_validation_message(
            "String should have at least 1 character", "string_too_short"
        ) == "no puede estar vacío"
        
        assert translate_validation_message(
            "Field required", "missing"
        ) == "es requerido"
        
        assert translate_validation_message(
            "field required", "missing"
        ) == "es requerido"

    def test_enum_error_type_with_user_system(self):
        """Test tipo de error enum conteniendo 'user' y 'system'."""
        # Arrange & Act & Assert
        assert translate_validation_message(
            "Input should be 'user' or 'system'", "enum"
        ) == "debe ser 'user' o 'system'"
        
        assert translate_validation_message(
            "Value must be 'user' or 'system'", "enum"
        ) == "debe ser 'user' o 'system'"

    def test_enum_error_type_without_user_system(self):
        """Test tipo de error enum sin 'user' y 'system'."""
        # Arrange & Act & Assert
        assert translate_validation_message(
            "Invalid enum value", "enum"
        ) == "no es válido"

    def test_string_too_short_error_type(self):
        """Test tipo de error string_too_short."""
        # Arrange & Act & Assert
        assert translate_validation_message(
            "String too short", "string_too_short"
        ) == "no puede estar vacío"

    def test_missing_error_type(self):
        """Test tipo de error missing."""
        # Arrange & Act & Assert
        assert translate_validation_message(
            "Missing field", "missing"
        ) == "es requerido"

    def test_value_error_type(self):
        """Test tipo de error value_error."""
        # Arrange & Act & Assert
        assert translate_validation_message(
            "Invalid value", "value_error"
        ) == "tiene un valor inválido"

    def test_input_should_be_pattern_single_value(self):
        """Test patrón 'Input should be' con un valor."""
        # Arrange & Act & Assert
        assert translate_validation_message(
            "Input should be 'active'", "unknown"
        ) == "debe ser 'active'"

    def test_input_should_be_pattern_multiple_values(self):
        """Test patrón 'Input should be' con múltiples valores."""
        # Arrange & Act & Assert
        assert translate_validation_message(
            "Input should be 'active' or 'inactive' or 'pending'", "unknown"
        ) == "debe ser 'active' o 'inactive' o 'pending'"

    def test_fallback_message(self):
        """Test mensaje de fallback cuando no hay traducción."""
        # Arrange & Act & Assert
        assert translate_validation_message(
            "Some unknown error", "unknown"
        ) == "no es válido"


class TestErrorHandlers:
    """Tests para los manejadores de errores."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.app = FastAPI()
        self.mock_request = Mock(spec=Request)
        self.mock_request.url = "http://test.com/api/test"

    def test_setup_error_handlers(self):
        """Test configuración de manejadores de errores."""
        # Arrange
        app = FastAPI()
        
        # Act
        setup_error_handlers(app)
        
        # Assert - Verificar que se agregaron los handlers
        assert len(app.exception_handlers) >= 4  # Al menos 4 handlers

    @pytest.mark.asyncio
    @patch('app.error_handlers.logger')
    async def test_validation_exception_handler_single_error(self, mock_logger):
        """Test manejo de error de validación con un solo error."""
        # Arrange
        setup_error_handlers(self.app)
        
        mock_exc = Mock(spec=RequestValidationError)
        mock_exc.errors.return_value = [
            {
                "loc": ("body", "content"),
                "msg": "Field required",
                "type": "missing"
            }
        ]
        
        # Act
        handler = self.app.exception_handlers[RequestValidationError]
        response = await handler(self.mock_request, mock_exc)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422
        mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.error_handlers.logger')
    async def test_validation_exception_handler_multiple_errors(self, mock_logger):
        """Test manejo de error de validación con múltiples errores.""" 
        # Arrange
        setup_error_handlers(self.app)
        
        mock_exc = Mock(spec=RequestValidationError)
        mock_exc.errors.return_value = [
            {
                "loc": ("body", "content"),
                "msg": "Field required", 
                "type": "missing"
            },
            {
                "loc": ("body", "sender"),
                "msg": "Input should be 'user' or 'system'",
                "type": "enum"
            }
        ]
        
        # Act
        handler = self.app.exception_handlers[RequestValidationError]
        response = await handler(self.mock_request, mock_exc)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422
        mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.error_handlers.logger')
    async def test_http_exception_handler_structured_detail(self, mock_logger):
        """Test manejo de HTTPException con detail estructurado."""
        # Arrange
        setup_error_handlers(self.app)
        
        structured_detail = {
            "status": "error",
            "error": {
                "code": "CUSTOM_ERROR",
                "message": "Custom error message"
            }
        }
        mock_exc = StarletteHTTPException(
            status_code=400, 
            detail=structured_detail
        )
        
        # Act
        handler = self.app.exception_handlers[StarletteHTTPException]
        response = await handler(self.mock_request, mock_exc)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400

    @pytest.mark.asyncio
    @patch('app.error_handlers.logger')
    async def test_http_exception_handler_standard_errors(self, mock_logger):
        """Test manejo de HTTPException con errores estándar."""
        # Arrange
        setup_error_handlers(self.app)
        
        test_cases = [
            (400, "Bad Request"),
            (401, "Unauthorized"), 
            (403, "Forbidden"),
            (404, "Not Found"),
            (405, "Method Not Allowed"),
            (409, "Conflict"),
            (429, "Too Many Requests"),
            (500, "Internal Server Error"),
            (999, "Unknown Error")  # Código no estándar
        ]
        
        for status_code, detail in test_cases:
            # Act
            mock_exc = StarletteHTTPException(
                status_code=status_code,
                detail=detail
            )
            handler = self.app.exception_handlers[StarletteHTTPException]
            response = await handler(self.mock_request, mock_exc)
            
            # Assert
            assert isinstance(response, JSONResponse)
            assert response.status_code == status_code
            mock_logger.error.assert_called()

    @pytest.mark.asyncio
    @patch('app.error_handlers.logger')
    async def test_http_exception_handler_no_detail(self, mock_logger):
        """Test manejo de HTTPException sin detail."""
        # Arrange
        setup_error_handlers(self.app)
        
        mock_exc = StarletteHTTPException(status_code=400, detail=None)
        
        # Act
        handler = self.app.exception_handlers[StarletteHTTPException]
        response = await handler(self.mock_request, mock_exc)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    @patch('app.error_handlers.logger')
    async def test_database_exception_handler(self, mock_logger):
        """Test manejo de errores de base de datos."""
        # Arrange
        setup_error_handlers(self.app)
        
        mock_exc = SQLAlchemyError("Database connection error")
        
        # Act
        handler = self.app.exception_handlers[SQLAlchemyError]
        response = await handler(self.mock_request, mock_exc)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.error_handlers.logger')
    async def test_general_exception_handler(self, mock_logger):
        """Test manejo de excepciones generales."""
        # Arrange
        setup_error_handlers(self.app)
        
        mock_exc = Exception("Unexpected error")
        
        # Act
        handler = self.app.exception_handlers[Exception]
        response = await handler(self.mock_request, mock_exc)
        
        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        mock_logger.error.assert_called_once_with(
            f"Error no manejado en {self.mock_request.url}: Unexpected error",
            exc_info=True
        )


class TestConfigureLogging:
    """Tests para la configuración de logging."""
    
    @patch('app.error_handlers.logging.basicConfig')
    @patch('app.error_handlers.logging.getLogger')
    def test_configure_logging(self, mock_get_logger, mock_basic_config):
        """Test configuración básica de logging."""
        # Arrange
        mock_uvicorn_logger = Mock()
        mock_sqlalchemy_logger = Mock()
        
        def get_logger_side_effect(name):
            if name == "uvicorn.access":
                return mock_uvicorn_logger
            elif name == "sqlalchemy.engine":
                return mock_sqlalchemy_logger
            return Mock()
        
        mock_get_logger.side_effect = get_logger_side_effect
        
        # Act
        configure_logging()
        
        # Assert
        mock_basic_config.assert_called_once()
        # Verificar que se configuró nivel INFO
        args, kwargs = mock_basic_config.call_args
        assert kwargs['level'] == logging.INFO
        
        # Verificar que se configuró formato
        assert 'format' in kwargs
        assert 'handlers' in kwargs
        
        # Verificar que se configuraron niveles específicos para otros loggers
        mock_uvicorn_logger.setLevel.assert_called_once_with(logging.WARNING)
        mock_sqlalchemy_logger.setLevel.assert_called_once_with(logging.WARNING)

    @patch('app.error_handlers.logging.basicConfig')
    @patch('app.error_handlers.logging.getLogger')
    def test_configure_logging_format_and_handlers(self, mock_get_logger, mock_basic_config):
        """Test que la configuración incluye el formato y handlers correctos."""
        # Arrange
        mock_get_logger.return_value = Mock()
        
        # Act
        configure_logging()
        
        # Assert
        args, kwargs = mock_basic_config.call_args
        
        # Verificar formato específico
        expected_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        assert kwargs['format'] == expected_format
        
        # Verificar que hay al menos un StreamHandler
        assert len(kwargs['handlers']) >= 1
        assert any(isinstance(h, logging.StreamHandler) for h in kwargs['handlers'])