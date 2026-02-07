"""
Excepciones personalizadas para el repositorio de mensajes.

Define errores específicos que pueden ocurrir en las operaciones de base de datos.
"""

class MessageRepositoryError(Exception):
    """Excepción base para errores del repositorio de mensajes."""
    pass

class MessageNotFoundError(MessageRepositoryError):
    """Excepción cuando no se encuentra un mensaje."""
    
    def __init__(self, message_id: str):
        self.message_id = message_id
        super().__init__(f"Mensaje con ID '{message_id}' no encontrado")

class MessageAlreadyExistsError(MessageRepositoryError):
    """Excepción cuando ya existe un mensaje con el mismo ID."""
    
    def __init__(self, message_id: str):
        self.message_id = message_id
        super().__init__(f"Mensaje con ID '{message_id}' ya existe")

class SessionNotFoundError(MessageRepositoryError):
    """Excepción cuando no se encuentra una sesión."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Sesión con ID '{session_id}' no encontrada")

class DatabaseTransactionError(MessageRepositoryError):
    """Excepción para errores de transacciones de base de datos."""
    
    def __init__(self, operation: str, original_error: Exception = None):
        self.operation = operation
        self.original_error = original_error
        message = f"Error en transacción durante operación: {operation}"
        if original_error:
            message += f" - {str(original_error)}"
        super().__init__(message)