#!/usr/bin/env python3
"""
Script de inicialização para Railway
"""
import os
import sys
from pathlib import Path

def main():
    # Configurar path para backend
    current_dir = Path(__file__).parent
    backend_dir = current_dir / "backend"
    sys.path.insert(0, str(backend_dir))
    
    # Importar aplicação
    from main import app
    
    # Iniciar servidor
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"🚀 Iniciando servidor em {host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()
