"""
Excepciones centralizadas para toda la aplicación.

Reexporta todas las excepciones desde sus módulos respectivos
para facilitar las importaciones en tests y otros módulos.
"""

# Importar excepciones del repositorio
from app.repositories.exceptions import (
    MessageRepositoryError,
    MessageNotFoundError, 
    MessageAlreadyExistsError,
    SessionNotFoundError
)

# Importar excepciones de servicios
from app.services.exceptions import (
    MessageServiceError,
    ContentFilterError,
    InappropriateContentError,
    RateLimitExceededError
)

# Alias para consistency con nombres usados en tests
DuplicateMessageError = MessageAlreadyExistsError

# Excepción general para errores de base de datos
class DatabaseError(Exception):
    """Excepción para errores generales de base de datos."""
    pass

# Reexportar todo para facilitar importación
__all__ = [
    # Errores de repositorio
    'MessageRepositoryError',
    'MessageNotFoundError',
    'MessageAlreadyExistsError',
    'SessionNotFoundError',
    'DuplicateMessageError',  # Alias
    
    # Errores de servicios
    'MessageServiceError',
    'ContentFilterError', 
    'InappropriateContentError',
    'RateLimitExceededError',
    
    # Errores generales
    'DatabaseError'
]