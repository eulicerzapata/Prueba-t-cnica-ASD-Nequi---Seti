"""
Configuración profesional de tests para FastAPI Chat API.

Implementación de Ingeniero QA Senior:
- Base de datos SQLite en memoria para aislamiento completo
- Overrides de dependency injection apropiados
- Fixtures completas para todos los escenarios de testing
- Patrones de setup/teardown limpios
- Capacidades de monitoreo de rendimiento
"""

import pytest
import pytest_asyncio
import asyncio
import os
import sys
from pathlib import Path
from typing import Generator, AsyncGenerator, Dict, Any
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient
from datetime import datetime, timezone

# =============================================================================
# CONFIGURACIÓN DEL ENTORNO - Debe hacerse ANTES de importar la app
# =============================================================================
os.environ.update({
    "DATABASE_URL": "sqlite:///:memory:",
    "API_DEBUG": "false",
    "TESTING": "true",
    "ENABLE_CONTENT_FILTER": "true",
    "PROFANITY_WORDS": "spam,malo,prohibido"
})

# Agregar el directorio raíz del proyecto al path de Python
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Importar después de la configuración del entorno
from app.database.connection import get_database_session, Base
from app.main import app
from app.schemas.message import MessageCreate, SenderEnum
from app.models.message import Message
from app.utils.content_filter import ContentFilter

# =============================================================================
# FIXTURES DE BASE DE DATOS - Configuración profesional de SQLite en memoria
# =============================================================================

@pytest.fixture(scope="session")
def test_engine():
    """
    Motor SQLite en memoria con scope de sesión y configuración apropiada.
    Usa StaticPool para asegurar persistencia de una sola conexión.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
        echo=False  # Cambiar a True para debug de SQL
    )

    # Habilitar constraints de foreign key para SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)
    yield engine

    # Limpieza
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_engine) -> Generator[Session, None, None]:
    """
    Sesión de base de datos con scope de función y rollback automático.
    Asegura el aislamiento de tests haciendo rollback de transacciones.
    """
    connection = test_engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=connection
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def override_get_db(test_db_session):
    """
    Override de dependencia de base de datos de FastAPI para testing.
    Asegura que todas las operaciones de BD usen la sesión de test.
    """
    def _override_get_database_session():
        try:
            yield test_db_session
        finally:
            pass  # La limpieza de la sesión la maneja el fixture test_db_session

    app.dependency_overrides[get_database_session] = _override_get_database_session
    yield  # No retorna nada, solo indica que el override está activo
    app.dependency_overrides.clear()

# =============================================================================
# FIXTURES DE CLIENTES API
# =============================================================================

@pytest.fixture
def client(override_get_db) -> Generator[TestClient, None, None]:
    """
    Cliente de test síncrono de FastAPI con override de base de datos.
    Usar para testing HTTP estándar.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """
    Cliente HTTP asíncrono para testing de endpoints async.
    Usar para testing de operaciones async y peticiones concurrentes.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac

# =============================================================================
# FIXTURES MOCK - Para testing unitario
# =============================================================================

@pytest.fixture
def mock_content_filter():
    """Mock de ContentFilter para testing unitario de servicios."""
    mock_filter = Mock(spec=ContentFilter)
    mock_filter.is_appropriate.return_value = True
    mock_filter.get_inappropriate_words.return_value = []
    mock_filter.add_words.return_value = None
    mock_filter.get_word_count.return_value = 0
    mock_filter.contains_inappropriate_content.return_value = False
    return mock_filter


@pytest.fixture
def mock_message_repository():
    """Mock de MessageRepository para testing de capa de servicio."""
    mock_repo = Mock()
    mock_repo.create.return_value = Mock()
    mock_repo.get_by_id.return_value = None
    mock_repo.get_by_session.return_value = ([], 0)
    mock_repo.exists.return_value = False
    return mock_repo


@pytest.fixture
def mock_repository(mock_message_repository):
    """Alias para mock_message_repository para retrocompatibilidad."""
    return mock_message_repository

# =============================================================================
# FIXTURES DE DATOS DE PRUEBA - Datos reutilizables para tests
# =============================================================================

@pytest.fixture
def sample_message_data() -> Dict[str, Any]:
    """Datos estándar de mensaje para testing."""
    return {
        "session_id": "test-session-123",
        "content": "This is a test message",
        "sender": "user"
    }


@pytest.fixture
def sample_system_message_data() -> Dict[str, Any]:
    """Datos de mensaje del sistema para testing."""
    return {
        "session_id": "system-session-456",
        "content": "System generated message",
        "sender": "system"
    }


@pytest.fixture
def sample_inappropriate_message_data() -> Dict[str, Any]:
    """Mensaje con contenido inapropiado para tests de filtrado."""
    return {
        "session_id": "filter-test-789",
        "content": "This message contains spam content",
        "sender": "user"
    }


@pytest.fixture
def multiple_messages_data() -> list[Dict[str, Any]]:
    """Múltiples mensajes para testing de paginación y sesión."""
    return [
        {
            "session_id": "pagination-test",
            "content": f"Message {i} content for testing pagination",
            "sender": "user" if i % 2 == 0 else "system"
        }
        for i in range(1, 11)  # 10 mensajes en total
    ]

# =============================================================================
# FUNCIONES HELPER - Utilidades para tests
# =============================================================================

@pytest.fixture
def create_test_message(test_db_session):
    """Función helper para crear mensajes en la base de datos para testing."""
    def _create_message(
        message_id: str = "test-msg-123",
        session_id: str = "test-session",
        content: str = "Test message content",
        sender: str = "user"
    ) -> Message:
        message = Message(
            message_id=message_id,
            session_id=session_id,
            content=content,
            sender=sender,
            timestamp=datetime.now(timezone.utc),
            word_count=len(content.split()),
            character_count=len(content),
            processed_at=datetime.now(timezone.utc)
        )
        test_db_session.add(message)
        test_db_session.commit()
        test_db_session.refresh(message)
        return message

    return _create_message


@pytest.fixture
def assert_response_structure():
    """Helper para validar la estructura de respuestas de API."""
    def _assert_structure(response_json: dict, expected_fields: list):
        for field in expected_fields:
            assert field in response_json, f"Missing field: {field}"
        return True

    return _assert_structure

# =============================================================================
# CONFIGURACIÓN DE PYTEST
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup de sesión auto-ejecutado para entorno de test consistente."""
    # Limpiar cualquier estado existente
    if hasattr(app, 'dependency_overrides'):
        app.dependency_overrides.clear()

    yield

    # Limpieza después de todos los tests
    app.dependency_overrides.clear()


# Configurar pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

def pytest_configure(config):
    """Configurar pytest con markers y settings personalizados."""
    config.addinivalue_line(
        "markers", "integration: marca tests como tests de integración"
    )
    config.addinivalue_line(
        "markers", "unit: marca tests como tests unitarios"
    )
    config.addinivalue_line(
        "markers", "e2e: marca tests como tests end-to-end"
    )

# =============================================================================
# FIXTURES DE RENDIMIENTO Y DEBUGGING
# =============================================================================

@pytest.fixture
def performance_monitor():
    """Monitorear rendimiento de tests y consultas de base de datos."""
    import time
    start_time = time.time()
    yield
    end_time = time.time()
    duration = end_time - start_time
    if duration > 1.0:  # Registrar tests lentos
        print(f"⚠️  Test lento detectado: {duration:.2f}s")