"""
Fixtures adicionales para tests de integración.

Ingeniero QA Senior - Fixtures extendidas para testing completo
"""

import pytest
from typing import List, Dict, Any
from httpx import AsyncClient


@pytest.fixture
def sample_message_data() -> Dict[str, Any]:
    """Datos de mensaje de ejemplo para testing."""
    return {
        "session_id": "test-session-123",
        "content": "Sample message content for testing",
        "sender": "user"
    }


@pytest.fixture
def sample_messages_data() -> List[Dict[str, Any]]:
    """Múltiples mensajes de ejemplo para testing masivo."""
    return [
        {
            "session_id": "bulk-session-001",
            "content": f"Test message {i} content",
            "sender": "user" if i % 2 == 0 else "system"
        }
        for i in range(1, 6)
    ]


@pytest.fixture
async def create_test_messages(client: AsyncClient):
    """Fixture helper para crear mensajes de test vía API."""
    created_messages = []

    async def _create_messages(messages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Crear múltiples mensajes y retornar sus datos."""
        for msg_data in messages_data:
            response = await client.post("/api/messages", json=msg_data)
            assert response.status_code == 201
            created_messages.append(response.json())
        return created_messages

    yield _create_messages


@pytest.fixture
def assert_helpers():
    """Helpers de aserciones comunes para tests."""
    class AssertHelpers:
        @staticmethod
        def assert_message_structure(message_dict: Dict[str, Any],
                                   required_fields: List[str] = None):
            """Verificar que el mensaje tiene la estructura apropiada."""
            default_fields = [
                "message_id", "session_id", "content", "sender",
                "timestamp", "word_count", "character_count", "processed_at"
            ]
            fields_to_check = required_fields or default_fields

            for field in fields_to_check:
                assert field in message_dict, f"Campo faltante: {field}"

        @staticmethod
        def assert_pagination_structure(pagination_dict: Dict[str, Any]):
            """Verificar que la paginación tiene la estructura apropiada."""
            required_fields = ["limit", "offset", "has_next"]
            for field in required_fields:
                assert field in pagination_dict, f"Campo de paginación faltante: {field}"

        @staticmethod
        def assert_response_structure(response_dict: Dict[str, Any]):
            """Verificar que la respuesta de API tiene la estructura apropiada."""
            assert "messages" in response_dict
            assert "total_count" in response_dict
            assert "session_id" in response_dict
            assert "pagination" in response_dict

            assert isinstance(response_dict["messages"], list)
            assert isinstance(response_dict["total_count"], int)
            assert isinstance(response_dict["session_id"], str)
            assert isinstance(response_dict["pagination"], dict)

    return AssertHelpers()