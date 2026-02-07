"""
Fixtures de datos para testing.

Proporciona datos de prueba reutilizables, 
generadores de datos y objetos mock.
"""

import pytest
from datetime import datetime, timezone
from typing import List, Dict, Any
from unittest.mock import Mock

from app.models.message import Message
from app.schemas.message import MessageCreate, SenderEnum


@pytest.fixture
def message_factory():
    """Factory para crear mensajes de prueba."""
    def _create_message(
        message_id: str = None,
        session_id: str = "default-session",
        content: str = "Default test message",
        sender: SenderEnum = SenderEnum.USER,
        timestamp: datetime = None,
        word_count: int = None,
        character_count: int = None
    ) -> Message:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
            
        if word_count is None:
            word_count = len(content.split())
            
        if character_count is None:
            character_count = len(content)
            
        return Message(
            message_id=message_id or f"msg-{hash(content) % 10000}",
            session_id=session_id,
            content=content,
            sender=sender,
            timestamp=timestamp,
            word_count=word_count,
            character_count=character_count
        )
    
    return _create_message


@pytest.fixture
def message_create_factory():
    """Factory para crear objetos MessageCreate."""
    def _create_message_create(
        message_id: str = None,
        session_id: str = "test-session",
        content: str = "Test message content",
        sender: SenderEnum = SenderEnum.USER,
        timestamp: datetime = None
    ) -> MessageCreate:
        return MessageCreate(
            message_id=message_id,
            session_id=session_id,
            content=content,
            sender=sender,
            timestamp=timestamp
        )
    
    return _create_message_create


@pytest.fixture
def conversation_data():
    """Datos de una conversación completa para testing."""
    return [
        {
            "session_id": "conversation-123",
            "content": "Hola, necesito ayuda con mi cuenta",
            "sender": "user",
            "expected_word_count": 6,
            "expected_char_count": 36
        },
        {
            "session_id": "conversation-123", 
            "content": "¡Por supuesto! ¿En qué puedo ayudarte?",
            "sender": "system",
            "expected_word_count": 7,
            "expected_char_count": 38
        },
        {
            "session_id": "conversation-123",
            "content": "No puedo acceder a mi panel de usuario",
            "sender": "user", 
            "expected_word_count": 8,
            "expected_char_count": 38
        },
        {
            "session_id": "conversation-123",
            "content": "Entiendo. Vamos a revisar tu configuración paso a paso.",
            "sender": "system",
            "expected_word_count": 10,
            "expected_char_count": 61
        }
    ]


@pytest.fixture
def multiple_sessions_data():
    """Datos de múltiples sesiones para testing de paginación."""
    sessions_data = {}
    
    for session_num in range(1, 4):  # 3 sesiones
        session_id = f"session-{session_num}"
        sessions_data[session_id] = []
        
        for msg_num in range(1, 6):  # 5 mensajes por sesión
            sessions_data[session_id].append({
                "session_id": session_id,
                "content": f"Mensaje {msg_num} de la sesión {session_num}",
                "sender": "user" if msg_num % 2 == 1 else "system"
            })
    
    return sessions_data


@pytest.fixture
def edge_case_messages():
    """Mensajes con casos edge para testing robusto."""
    return [
        {
            "description": "Mensaje vacío",
            "data": {
                "session_id": "edge-case-session",
                "content": "",
                "sender": "user"
            },
            "expected_word_count": 0,
            "expected_char_count": 0
        },
        {
            "description": "Mensaje con solo espacios",
            "data": {
                "session_id": "edge-case-session",
                "content": "   \t\n  ",
                "sender": "user"
            },
            "expected_word_count": 0,
            "expected_char_count": 8
        },
        {
            "description": "Mensaje muy largo",
            "data": {
                "session_id": "edge-case-session",
                "content": "x" * 5000,  # 5000 caracteres
                "sender": "user"
            },
            "expected_word_count": 1,
            "expected_char_count": 5000
        },
        {
            "description": "Mensaje con emojis",
            "data": {
                "session_id": "edge-case-session", 
                "content": "Hola 👋 ¿cómo estás? 😊🎉",
                "sender": "user"
            },
            "expected_word_count": 4,
            "expected_char_count": 26
        },
        {
            "description": "Mensaje con caracteres especiales",
            "data": {
                "session_id": "edge-case-session",
                "content": "Test @#$%^&*()_+-=[]{}|;:,.<>?/~`",
                "sender": "system"
            }, 
            "expected_word_count": 2,
            "expected_char_count": 33
        }
    ]


@pytest.fixture
def inappropriate_content_samples():
    """Muestras de contenido inapropiado para testing del filtro."""
    return [
        "Este mensaje contiene spam repetitivo",
        "Contenido malicioso y fraudulento aquí",
        "Palabras ofensivas y lenguaje inapropiado",
        "Mensaje promocional no solicitado de spam"
    ]


@pytest.fixture
def valid_timestamps():
    """Timestamps válidos en diferentes formatos para testing."""
    base_time = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
    
    return [
        {
            "description": "ISO con Z",
            "timestamp": base_time.isoformat().replace("+00:00", "Z"),
            "expected_datetime": base_time
        },
        {
            "description": "ISO con +00:00",  
            "timestamp": base_time.isoformat(),
            "expected_datetime": base_time
        },
        {
            "description": "ISO con microsegundos",
            "timestamp": base_time.replace(microsecond=123456).isoformat().replace("+00:00", "Z"),
            "expected_datetime": base_time.replace(microsecond=123456)
        }
    ]


@pytest.fixture
def database_test_scenarios():
    """Escenarios para testing de operaciones de base de datos."""
    return [
        {
            "name": "bulk_insert", 
            "description": "Inserción masiva de mensajes",
            "message_count": 50,
            "sessions_count": 5
        },
        {
            "name": "concurrent_access",
            "description": "Acceso concurrente a la misma sesión",
            "message_count": 20,
            "sessions_count": 1
        },
        {
            "name": "mixed_senders",
            "description": "Mensajes mezclados de user y system",
            "message_count": 30,
            "sessions_count": 3
        }
    ]


@pytest.fixture
def api_response_templates():
    """Templates de respuestas de API para validación."""
    return {
        "success_create": {
            "status": "success",
            "data": {
                "message_id": str,
                "session_id": str,
                "content": str,
                "sender": str,
                "timestamp": str
            }
        },
        "success_list": {
            "status": "success", 
            "data": {
                "messages": list,
                "total": int,
                "page": int,
                "page_size": int
            }
        },
        "error_validation": {
            "status": "error",
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str
            }
        },
        "error_duplicate": {
            "status": "error",
            "error": {
                "code": "DUPLICATE_MESSAGE",
                "message": str
            }
        },
        "error_inappropriate": {
            "status": "error",
            "error": {
                "code": "INAPPROPRIATE_CONTENT",
                "message": str
            }
        }
    }


@pytest.fixture
def performance_test_data():
    """Datos para testing de rendimiento."""
    def generate_messages(count: int, session_prefix: str = "perf"):
        messages = []
        for i in range(count):
            session_id = f"{session_prefix}-session-{i // 10}"  # 10 mensajes por sesión
            messages.append({
                "session_id": session_id,
                "content": f"Performance test message number {i+1} with some content to test",
                "sender": "user" if i % 2 == 0 else "system"
            })
        return messages
    
    return {
        "small_load": generate_messages(100),
        "medium_load": generate_messages(500), 
        "large_load": generate_messages(1000)
    }


class MockDataHelper:
    """Clase helper para generar datos mock."""
    
    @staticmethod
    def create_mock_message_list(count: int, session_id: str = "mock-session") -> List[Message]:
        """Crear lista de mensajes mock."""
        messages = []
        for i in range(count):
            messages.append(Message(
                message_id=f"mock-msg-{i}",
                session_id=session_id,
                content=f"Mock message content {i}",
                sender=SenderEnum.USER if i % 2 == 0 else SenderEnum.SYSTEM,
                timestamp=datetime.now(timezone.utc),
                word_count=3,
                character_count=20
            ))
        return messages
    
    @staticmethod
    def create_repository_mock(**kwargs) -> Mock:
        """Crear mock de repository configurado."""
        mock_repo = Mock()
        
        # Configuraciones por defecto
        mock_repo.create.return_value = kwargs.get(
            'create_return',
            Message(
                message_id="default-mock-id",
                session_id="default-session",
                content="Default mock content",
                sender=SenderEnum.USER,
                timestamp=datetime.now(timezone.utc),
                word_count=3,
                character_count=20
            )
        )
        
        mock_repo.get_by_id.return_value = kwargs.get('get_by_id_return', None)
        mock_repo.get_by_session.return_value = kwargs.get('get_by_session_return', ([], 0))
        mock_repo.exists.return_value = kwargs.get('exists_return', False)
        
        return mock_repo


@pytest.fixture
def mock_data_helper():
    """Fixture que proporciona MockDataHelper."""
    return MockDataHelper()