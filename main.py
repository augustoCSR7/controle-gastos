"""
Arquivo de entrada para Railway
Importa a aplicação FastAPI da pasta backend
"""
import sys
import os

# Adiciona o diretório backend ao path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Importa a aplicação
from main import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)