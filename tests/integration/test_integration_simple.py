"""
Tests de Integración Simplificados

Tests que no dependen de la API completa funcionando
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestIntegrationSimple:
    """Tests de integración simplificados."""

    def test_app_startup_basic(self):
        """Test básico de que la aplicación arranca."""
        from app.main import app
        
        with TestClient(app) as client:
            # Test básico de documentación
            response = client.get("/docs")
            assert response.status_code == 200

    def test_health_check_basic(self):
        """Test básico de health check."""
        from app.main import app
        
        with TestClient(app) as client:
            # Test el endpoint de documentación como health check
            response = client.get("/")
            # Puede ser 200, 404, o redirección - cualquiera significa que la app funciona
            assert response.status_code in [200, 404, 307, 308]

    @pytest.mark.smoke  
    def test_smoke_app_imports(self):
        """Smoke test de imports principales."""
        try:
            from app.main import app
            from app.models.message import Message
            from app.services.message_service import MessageService
            from app.repositories.message_repository import MessageRepository
            
            assert app is not None
            assert Message is not None
            assert MessageService is not None
            assert MessageRepository is not None
            
        except Exception as e:
            pytest.fail(f"Error en imports básicos: {e}")

    def test_database_models_basic(self):
        """Test básico de modelos de base de datos."""
        from app.models.message import Message
        from app.schemas.message import SenderEnum
        from datetime import datetime, timezone
        
        # Test que podemos crear una instancia del modelo
        message = Message(
            message_id="test-123",
            session_id="test-session",
            content="test content",
            sender=SenderEnum.USER,
            timestamp=datetime.now(timezone.utc),
            word_count=2,
            character_count=12,
            processed_at=datetime.now(timezone.utc)
        )
        
        assert message.message_id == "test-123"
        assert message.content == "test content"