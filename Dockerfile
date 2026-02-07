# ============================================================================
# Dockerfile Multi-Stage para Chat Message API
# ============================================================================

# Etapa 1: Builder - Construir dependencias
FROM python:3.10-slim as builder

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar paquetes Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python en un directorio virtual
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# ============================================================================
# Etapa 2: Runtime - Imagen final optimizada
# ============================================================================
FROM python:3.10-slim

# Metadata
LABEL maintainer="Chat API Team"
LABEL description="API RESTful para procesamiento de mensajes de chat"
LABEL version="1.0.0"

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Deshabilitar pip version check
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Directorio de la aplicación
    APP_HOME=/app

# Crear usuario no-root para seguridad
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Establecer directorio de trabajo
WORKDIR $APP_HOME

# Copiar dependencias instaladas desde la etapa builder
COPY --from=builder /root/.local /home/appuser/.local

# Copiar código de la aplicación
COPY --chown=appuser:appuser . .

# Crear directorios necesarios con permisos para appuser
RUN mkdir -p /app/data /app/logs && \
    chown -R appuser:appuser /app/data /app/logs

# Asegurar que los scripts de Python estén en el PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Cambiar al usuario no-root
USER appuser

# Exponer el puerto de la aplicación
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Comando por defecto para ejecutar la aplicación
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
