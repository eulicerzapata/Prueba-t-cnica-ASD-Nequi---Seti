"""
Script de inicio rápido para la Chat Message API.

Inicia el servidor y abre automáticamente la documentación.

Uso:
    python inicio_rapido.py
"""

import subprocess
import webbrowser
import time
import sys
import os

def verificar_dependencias():
    """Verificar que las dependencias estén instaladas."""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        print("✅ Todas las dependencias están instaladas")
        return True
    except ImportError as e:
        print(f"❌ Faltan dependencias: {e}")
        print("\n💡 Ejecuta: pip install -r requirements.txt")
        return False

def main():
    """Iniciar servidor y abrir documentación."""

    print("=" * 70)
    print("🚀 Chat Message API - Inicio Rápido")
    print("=" * 70)
    print()

    # Verificar dependencias
    print("🔍 Verificando dependencias...")
    if not verificar_dependencias():
        sys.exit(1)

    print()
    print("📦 Iniciando servidor FastAPI...")
    print("   Host: 127.0.0.1")
    print("   Puerto: 8000")
    print("   Modo: Hot reload activado")
    print()
    print("⚠️  Presiona CTRL+C para detener el servidor")
    print("=" * 70)
    print()

    # Esperar un poco antes de abrir el navegador
    def abrir_navegador():
        """Abrir navegador después de que el servidor inicie."""
        time.sleep(3)  # Esperar 3 segundos
        print("\n📚 Abriendo documentación en el navegador...")
        webbrowser.open("http://localhost:8000/docs")

    # Iniciar thread para abrir navegador
    import threading
    navegador_thread = threading.Thread(target=abrir_navegador, daemon=True)
    navegador_thread.start()

    try:
        # Iniciar servidor uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--reload",
            "--host", "127.0.0.1",
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n\n⚠️  Servidor detenido por el usuario.")
        print("👋 ¡Hasta pronto!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error al iniciar el servidor: {e}")
        print("\n💡 Asegúrate de estar en el directorio correcto del proyecto")
        sys.exit(1)

if __name__ == "__main__":
    # Cambiar al directorio del script si es necesario
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
