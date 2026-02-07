"""
Tests para las utilidades del repositorio (repositories/utils).
Cubre todas las funciones y clases .
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.repositories.utils import (
    get_message_repository,
    handle_repository_errors,
    RepositoryContext,
    with_repository_transaction
)
from app.repositories.message_repository import MessageRepository
from app.repositories.exceptions import (
    MessageAlreadyExistsError,
    DatabaseTransactionError
)


class TestGetMessageRepository:
    """Tests para la factory function del repositorio."""
    
    def test_get_message_repository_returns_instance(self):
        """Test que retorna instancia correcta de MessageRepository."""
        # Arrange
        mock_db = Mock(spec=Session)
        
        # Act
        repository = get_message_repository(mock_db)
        
        # Assert
        assert isinstance(repository, MessageRepository)
        assert repository.db == mock_db


class TestHandleRepositoryErrors:
    """Tests para el decorador de manejo de errores."""
    
    def test_decorator_success_no_error(self):
        """Test decorador cuando función ejecuta sin error."""
        # Arrange
        @handle_repository_errors("test_operation")
        def test_func():
            return "success"
        
        # Act
        result = test_func()
        
        # Assert
        assert result == "success"

    def test_decorator_integrity_error_unique_constraint(self):
        """Test decorador con IntegrityError de constraint único."""
        # Arrange
        @handle_repository_errors("test_operation")
        def test_func():
            raise IntegrityError("statement", "params", "UNIQUE constraint failed: message.message_id")
        
        # Act & Assert
        with pytest.raises(MessageAlreadyExistsError) as exc_info:
            test_func()
        
        assert "message_id already exists" in str(exc_info.value)

    def test_decorator_integrity_error_other(self):
        """Test decorador con IntegrityError que no es de constraint único."""
        # Arrange
        mock_integrity_error = IntegrityError("statement", "params", "Other integrity error")
        
        @handle_repository_errors("test_operation")  
        def test_func():
            raise mock_integrity_error
        
        # Act & Assert
        with pytest.raises(DatabaseTransactionError) as exc_info:
            test_func()
        
        assert exc_info.value.operation == "test_operation"
        assert exc_info.value.original_error == mock_integrity_error

    def test_decorator_sqlalchemy_error(self):
        """Test decorador con SQLAlchemyError general."""
        # Arrange
        mock_sql_error = SQLAlchemyError("Database connection failed")
        
        @handle_repository_errors("test_operation")
        def test_func():
            raise mock_sql_error
        
        # Act & Assert
        with pytest.raises(DatabaseTransactionError) as exc_info:
            test_func()
        
        assert exc_info.value.operation == "test_operation"
        assert exc_info.value.original_error == mock_sql_error

    def test_decorator_unexpected_error(self):
        """Test decorador con excepción inesperada."""
        # Arrange
        unexpected_error = ValueError("Unexpected error")
        
        @handle_repository_errors("test_operation")
        def test_func():
            raise unexpected_error
        
        # Act & Assert
        with pytest.raises(DatabaseTransactionError) as exc_info:
            test_func()
        
        assert "test_operation - Error inesperado" in exc_info.value.operation
        assert exc_info.value.original_error == unexpected_error

    def test_decorator_with_function_arguments(self):
        """Test decorador con función que recibe argumentos."""
        # Arrange
        @handle_repository_errors("test_operation")
        def test_func(arg1, arg2, kwarg1=None):
            return f"{arg1}-{arg2}-{kwarg1}"
        
        # Act
        result = test_func("a", "b", kwarg1="c")
        
        # Assert
        assert result == "a-b-c"

    def test_decorator_preserves_function_metadata(self):
        """Test que el decorador preserva metadatos de la función."""
        # Arrange
        @handle_repository_errors("test_operation")
        def test_func():
            """Test function docstring."""
            pass
        
        # Act & Assert
        assert test_func.__name__ == "test_func"
        assert "Test function docstring." in test_func.__doc__


class TestRepositoryContext:
    """Tests para el context manager RepositoryContext."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.mock_db = Mock(spec=Session)
        self.context = RepositoryContext(self.mock_db)

    def test_init_creates_repository(self):
        """Test que __init__ crea repositorio correctamente."""
        # Assert
        assert self.context.db == self.mock_db
        assert isinstance(self.context.repository, MessageRepository)

    def test_enter_returns_repository(self):
        """Test que __enter__ retorna el repositorio."""
        # Act
        result = self.context.__enter__()
        
        # Assert
        assert result == self.context.repository

    def test_exit_success_commits(self):
        """Test que __exit__ hace commit cuando no hay excepción."""
        # Act
        result = self.context.__exit__(None, None, None)
        
        # Assert
        self.mock_db.commit.assert_called_once()
        self.mock_db.rollback.assert_not_called()
        assert result is False  # Para propagar cualquier excepción

    def test_exit_with_exception_rollbacks(self):
        """Test que __exit__ hace rollback cuando hay excepción."""
        # Act
        result = self.context.__exit__(Exception, Exception("error"), None)
        
        # Assert
        self.mock_db.rollback.assert_called_once()
        self.mock_db.commit.assert_not_called()
        assert result is False  # Para propagar la excepción

    def test_exit_commit_fails_rollbacks(self):
        """Test que __exit__ hace rollback si el commit falla."""
        # Arrange
        self.mock_db.commit.side_effect = SQLAlchemyError("Commit failed")
        
        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            self.context.__exit__(None, None, None)
        
        self.mock_db.commit.assert_called_once()
        self.mock_db.rollback.assert_called_once()

    def test_context_manager_usage_success(self):
        """Test uso completo del context manager exitoso."""
        # Arrange
        mock_db = Mock(spec=Session)
        
        # Act
        with RepositoryContext(mock_db) as repo:
            assert isinstance(repo, MessageRepository)
        
        # Assert
        mock_db.commit.assert_called_once()
        mock_db.rollback.assert_not_called()

    def test_context_manager_usage_with_exception(self):
        """Test uso del context manager con excepción."""
        # Arrange
        mock_db = Mock(spec=Session)
        
        # Act & Assert
        with pytest.raises(ValueError):
            with RepositoryContext(mock_db) as repo:
                assert isinstance(repo, MessageRepository)
                raise ValueError("Test error")
        
        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()


class TestWithRepositoryTransaction:
    """Tests para la función with_repository_transaction."""
    
    def test_returns_repository_context(self):
        """Test que retorna instancia de RepositoryContext."""
        # Arrange
        mock_db = Mock(spec=Session)
        
        # Act
        result = with_repository_transaction(mock_db)
        
        # Assert
        assert isinstance(result, RepositoryContext)
        assert result.db == mock_db

    def test_context_manager_usage(self):
        """Test uso como context manager."""
        # Arrange
        mock_db = Mock(spec=Session)
        
        # Act
        with with_repository_transaction(mock_db) as repo:
            assert isinstance(repo, MessageRepository)
        
        # Assert
        mock_db.commit.assert_called_once()
        mock_db.rollback.assert_not_called()

    def test_context_manager_with_error(self):
        """Test uso como context manager con error."""
        # Arrange
        mock_db = Mock(spec=Session)
        
        # Act & Assert
        with pytest.raises(RuntimeError):
            with with_repository_transaction(mock_db) as repo:
                assert isinstance(repo, MessageRepository)
                raise RuntimeError("Transaction failed")
        
        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()


class TestIntegrationScenarios:
    """Tests de escenarios de integración más complejos."""
    
    @patch('app.repositories.utils.MessageRepository')
    def test_get_repository_and_context_integration(self, mock_repository_class):
        """Test integración entre factory function y context manager."""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_repo_instance = Mock()
        mock_repository_class.return_value = mock_repo_instance
        
        # Act
        repo_direct = get_message_repository(mock_db)
        
        with with_repository_transaction(mock_db) as repo_context:
            # Assert que ambos usan la misma clase
            assert isinstance(repo_direct, type(repo_context))
        
        # Assert transacción se manejó correctamente
        mock_db.commit.assert_called_once()

    def test_decorator_and_context_manager_combination(self):
        """Test combinación del decorador con context manager."""
        # Arrange
        mock_db = Mock(spec=Session)
        
        @handle_repository_errors("combined_operation")
        def operation_with_context():
            with with_repository_transaction(mock_db) as repo:
                return "operation_success"
        
        # Act
        result = operation_with_context()
        
        # Assert
        assert result == "operation_success"
        mock_db.commit.assert_called_once()

    def test_nested_error_handling(self):
        """Test manejo de errores anidados."""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_db.commit.side_effect = IntegrityError("stmt", "params", "UNIQUE constraint failed")
        
        @handle_repository_errors("nested_operation")
        def operation_with_context():
            with with_repository_transaction(mock_db) as repo:
                return "should_not_reach_here"
        
        # Act & Assert
        with pytest.raises(MessageAlreadyExistsError):
            operation_with_context()
        
        mock_db.rollback.assert_called_once()