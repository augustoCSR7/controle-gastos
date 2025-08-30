"""
Arquivo de entrada para Railway
Importa a aplicação FastAPI da pasta backend
"""
import sys
import os
from pathlib import Path

# Adiciona o diretório backend ao path
current_dir = Path(__file__).parent
backend_dir = current_dir / "backend"
sys.path.insert(0, str(backend_dir))

# Importa a aplicação FastAPI
try:
    from main import app
    print("✅ Aplicação FastAPI importada com sucesso!")
except ImportError as e:
    print(f"❌ Erro ao importar aplicação: {e}")
    # Fallback: tenta importar diretamente
    import importlib.util
    spec = importlib.util.spec_from_file_location("backend_main", backend_dir / "main.py")
    backend_main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(backend_main)
    app = backend_main.app
    print("✅ Aplicação importada via fallback!")

# Expor a aplicação para uvicorn
application = app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)