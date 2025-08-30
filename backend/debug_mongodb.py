#!/usr/bin/env python3
"""
Script de debug para testar conectividade MongoDB Atlas no Railway
Execute este script para diagnosticar problemas de conexão
"""

import os
import asyncio
import ssl
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

async def test_mongodb_connection():
    """Testa diferentes configurações de conexão com MongoDB Atlas"""
    
    mongodb_url = os.environ.get("MONGODB_URL", "")
    
    if not mongodb_url:
        print("❌ MONGODB_URL não encontrada nas variáveis de ambiente")
        return False
    
    print(f"🔗 URL de conexão: {mongodb_url[:50]}...")
    
    # Configurações de teste
    configs = [
        {
            "name": "Configuração Padrão",
            "options": {}
        },
        {
            "name": "SSL Desabilitado",
            "options": {
                "ssl": False
            }
        },
        {
            "name": "SSL Sem Verificação",
            "options": {
                "ssl": True,
                "ssl_cert_reqs": ssl.CERT_NONE,
                "ssl_match_hostname": False,
                "connectTimeoutMS": 30000,
                "serverSelectionTimeoutMS": 30000
            }
        },
        {
            "name": "SSL Completo Railway",
            "options": {
                "ssl": True,
                "ssl_cert_reqs": ssl.CERT_NONE,
                "ssl_ca_certs": None,
                "ssl_certfile": None,
                "ssl_keyfile": None,
                "ssl_match_hostname": False,
                "connectTimeoutMS": 30000,
                "serverSelectionTimeoutMS": 30000,
                "socketTimeoutMS": 45000,
                "maxPoolSize": 10,
                "retryWrites": True,
                "w": "majority"
            }
        }
    ]
    
    for config in configs:
        print(f"\n🧪 Testando: {config['name']}")
        try:
            client = AsyncIOMotorClient(mongodb_url, **config["options"])
            
            # Teste de ping
            await client.admin.command('ping')
            print("✅ Ping bem-sucedido!")
            
            # Teste de listagem de databases
            db_list = await client.list_database_names()
            print(f"📚 Databases: {db_list}")
            
            # Teste específico do database
            database = client.get_database("controle_gastos")
            collections = await database.list_collection_names()
            print(f"📁 Collections: {collections}")
            
            client.close()
            print(f"✅ {config['name']} funcionou!")
            return True
            
        except Exception as e:
            print(f"❌ {config['name']} falhou: {type(e).__name__}: {e}")
            try:
                client.close()
            except:
                pass
    
    return False

async def test_network_connectivity():
    """Testa conectividade de rede básica"""
    import socket
    
    # Testar resolução DNS do seu cluster
    try:
        host = "cluster-controle-gastos.0zgulhb.mongodb.net"  # ✅ Seu cluster real
        ip = socket.gethostbyname(host)
        print(f"🌐 DNS Resolution OK: {host} -> {ip}")
    except Exception as e:
        print(f"❌ DNS Resolution failed: {e}")
    
    # Testar conectividade TCP
    try:
        sock = socket.create_connection(("8.8.8.8", 53), timeout=10)
        sock.close()
        print("🌐 Internet connectivity OK")
    except Exception as e:
        print(f"❌ Internet connectivity failed: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando debug de conectividade MongoDB Atlas...")
    
    asyncio.run(test_network_connectivity())
    
    success = asyncio.run(test_mongodb_connection())
    
    if success:
        print("\n🎉 Pelo menos uma configuração funcionou!")
        print("📝 Use a configuração que funcionou no seu main.py")
    else:
        print("\n❌ Nenhuma configuração funcionou")
        print("🔧 Verifique:")
        print("   1. MONGODB_URL está correta?")
        print("   2. IP está na whitelist do MongoDB Atlas?")
        print("   3. Credenciais estão corretas?")
        print("   4. Cluster está ativo?")
