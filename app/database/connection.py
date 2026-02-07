"""
Configuración de base de datos SQLAlchemy

Maneja la conexión a SQLite y la configuración del ORM.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# URL de la base de datos desde variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chat_messages.db")

# Crear motor de base de datos
# Para SQLite, agregamos configuraciones específicas
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=os.getenv("API_DEBUG", "false").lower() == "true"  # Log SQL queries en modo debug
)

# Crear clase de sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()

def get_database_session():
    """
    Generador de sesiones de base de datos para dependency injection.
    
    Yields:
        Session: Sesión de SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Crear todas las tablas en la base de datos."""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Eliminar todas las tablas de la base de datos."""
    Base.metadata.drop_all(bind=engine)