"""
Utilidades para el repositorio de mensajes.

Funciones helper y factory para facilitar el uso del repositorio.
"""

from functools import wraps
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from .message_repository import MessageRepository
from .exceptions import (
    MessageAlreadyExistsError,
    DatabaseTransactionError
)


def get_message_repository(db: Session) -> MessageRepository:
    """
    Factory function para crear instancia del repositorio de mensajes.
    
    Args:
        db: Sesión de SQLAlchemy
        
    Returns:
        MessageRepository: Instancia del repositorio
    """
    return MessageRepository(db)


def handle_repository_errors(operation_name: str):
    """
    Decorador para manejo consistente de errores de repositorio.
    
    Args:
        operation_name: Nombre de la operación para logging de errores
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except IntegrityError as e:
                # Error de integridad (ej: clave duplicada)
                if "UNIQUE constraint failed" in str(e):
                    raise MessageAlreadyExistsError("message_id already exists")
                raise DatabaseTransactionError(operation_name, e)
            except SQLAlchemyError as e:
                # Otros errores de SQLAlchemy
                raise DatabaseTransactionError(operation_name, e)
            except Exception as e:
                # Errores inesperados
                raise DatabaseTransactionError(
                    f"{operation_name} - Error inesperado", e
                )
        return wrapper
    return decorator


class RepositoryContext:
    """
    Context manager para operaciones de repositorio con manejo automático de transacciones.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = MessageRepository(db)
    
    def __enter__(self) -> MessageRepository:
        return self.repository
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # Si no hubo excepción, hacer commit
            try:
                self.db.commit()
            except SQLAlchemyError:
                self.db.rollback()
                raise
        else:
            # Si hubo excepción, hacer rollback
            self.db.rollback()
        
        # Retornar False permite que la excepción se propague
        return False


def with_repository_transaction(db: Session):
    """
    Context manager simplificado para operaciones con transacciones.
    
    Args:
        db: Sesión de SQLAlchemy
        
    Returns:
        RepositoryContext: Context manager con repositorio
        
    Usage:
        with with_repository_transaction(db) as repo:
            message = repo.create(message_data, metadata)
            # Commit automático al salir del contexto
    """
    return RepositoryContext(db)