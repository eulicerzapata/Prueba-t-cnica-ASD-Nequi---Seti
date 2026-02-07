"""
Script para abrir automáticamente la documentación de la API en el navegador.

Uso:
    python abrir_docs.py
"""

import webbrowser
import time
import sys

def main():
    """Abrir documentación de la API en el navegador por defecto."""

    print("=" * 60)
    print("🚀 Chat Message API - Abriendo Documentación")
    print("=" * 60)
    print()

    # URLs a abrir
    urls = {
        "Swagger UI (Interactiva)": "http://localhost:8000/docs",
        "ReDoc (Alternativa)": "http://localhost:8000/redoc",
        "API Root": "http://localhost:8000/"
    }

    print("📚 Abriendo las siguientes URLs en tu navegador:")
    print()

    for nombre, url in urls.items():
        print(f"  ✅ {nombre}")
        print(f"     {url}")
        print()

        try:
            webbrowser.open(url)
            time.sleep(0.5)  # Pequeña pausa entre cada apertura
        except Exception as e:
            print(f"  ⚠️  Error al abrir {nombre}: {e}")
            print()

    print("=" * 60)
    print("✨ ¡Listo! Las pestañas deberían abrirse en tu navegador.")
    print()
    print("💡 Tip: Asegúrate de que la aplicación esté corriendo:")
    print("   uvicorn app.main:app --reload")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario.")
        sys.exit(0)
