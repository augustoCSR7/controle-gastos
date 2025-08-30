# Alternativa: usar MongoDB local no Railway
# Se MongoDB Atlas não funcionar, use este script

from motor.motor_asyncio import AsyncIOMotorClient
import os

# URL para MongoDB local no Railway (se necessário)
LOCAL_MONGODB_URL = "mongodb://localhost:27017"

async def setup_local_mongodb():
    """Configura MongoDB local se Atlas não funcionar"""
    try:
        client = AsyncIOMotorClient(LOCAL_MONGODB_URL)
        await client.admin.command('ping')
        print("✅ MongoDB local conectado!")
        return client
    except Exception as e:
        print(f"❌ MongoDB local também falhou: {e}")
        return None

# Para usar no main.py:
# client = await setup_local_mongodb() or create_mock_client()
