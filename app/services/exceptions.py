"""
Excepciones específicas para la capa de servicios.

Define errores de negocio que pueden ocurrir durante el procesamiento de mensajes.
"""

class MessageServiceError(Exception):
    """Excepción base para errores del servicio de mensajes."""
    pass

class ContentFilterError(MessageServiceError):
    """Excepción para errores relacionados con filtro de contenido."""
    
    def __init__(self, message: str, inappropriate_words: list = None):
        self.inappropriate_words = inappropriate_words or []
        super().__init__(message)

class InappropriateContentError(ContentFilterError):
    """Excepción cuando se detecta contenido inapropiado."""
    
    def __init__(self, inappropriate_words: list):
        self.inappropriate_words = inappropriate_words
        words_str = ", ".join(inappropriate_words)
        super().__init__(f"Contenido inapropiado detectado: {words_str}", inappropriate_words)

class RateLimitExceededError(MessageServiceError):
    """Excepción cuando se exceden los límites de tasa."""
    
    def __init__(self, limit_type: str, current_count: int, max_allowed: int):
        self.limit_type = limit_type
        self.current_count = current_count
        self.max_allowed = max_allowed
        super().__init__(
            f"Límite de {limit_type} excedido: {current_count}/{max_allowed}"
        )

class MessageValidationError(MessageServiceError):
    """Excepción para errores de validación de mensajes."""
    
    def __init__(self, validation_errors: list):
        self.validation_errors = validation_errors
        errors_str = "; ".join(validation_errors)
        super().__init__(f"Errores de validación: {errors_str}")

class UnauthorizedSenderError(MessageServiceError):
    """Excepción cuando el remitente no está autorizado."""
    
    def __init__(self, sender: str, session_id: str):
        self.sender = sender
        self.session_id = session_id
        super().__init__(f"Sender '{sender}' no autorizado para sesión '{session_id}'")

class MessageProcessingError(MessageServiceError):
    """Excepción para errores durante el procesamiento de mensajes."""
    
    def __init__(self, operation: str, original_error: Exception = None):
        self.operation = operation
        self.original_error = original_error
        message = f"Error durante {operation}"
        if original_error:
            message += f": {str(original_error)}"
        super().__init__(message)