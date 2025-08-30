from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import os
from typing import List, Optional
from datetime import date, datetime
import uvicorn
from dotenv import load_dotenv
from bson import ObjectId

# Carregar variáveis de ambiente
load_dotenv()

app = FastAPI(title="💰 Controle de Gastos", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🍃 Configuração MongoDB Atlas com SSL otimizado
MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.environ.get("MONGODB_DATABASE", "controle_gastos")

# Configurações SSL específicas para Railway + MongoDB Atlas
ssl_config = {
    'ssl': True,
    'ssl_cert_reqs': 'CERT_NONE',  # Pular verificação do certificado
    'ssl_ca_certs': None,
    'ssl_certfile': None,
    'ssl_keyfile': None,
    'ssl_crlfile': None,
    'ssl_pem_passphrase': None,
    'ssl_match_hostname': False,
    'connectTimeoutMS': 30000,  # 30 segundos timeout
    'serverSelectionTimeoutMS': 30000,
    'socketTimeoutMS': 45000,
    'maxPoolSize': 10,
    'retryWrites': True,
    'w': 'majority'
}

# Cliente MongoDB com configurações SSL otimizadas
try:
    if "mongodb+srv://" in MONGODB_URL or "ssl=true" in MONGODB_URL:
        print("🔐 Conectando ao MongoDB Atlas com SSL...")
        client = AsyncIOMotorClient(MONGODB_URL, **ssl_config)
    else:
        print("🏠 Conectando ao MongoDB local...")
        client = AsyncIOMotorClient(MONGODB_URL)
    
    database = client[DATABASE_NAME]
    print(f"📁 Database: {DATABASE_NAME}")
except Exception as e:
    print(f"⚠️ Erro na criação do cliente MongoDB: {e}")
    client = None
    database = None

# Collections com verificação de segurança
if database:
    categorias_collection = database.categorias
    gastos_collection = database.gastos
    tipos_pagamento_collection = database.tipos_pagamento
else:
    print("❌ Database não inicializado - funcionando no modo offline")
    categorias_collection = None
    gastos_collection = None
    tipos_pagamento_collection = None

# Função helper para verificar conectividade
async def check_db_connection():
    """Verifica se a conexão com o database está ativa"""
    if not client or not database:
        raise HTTPException(
            status_code=503, 
            detail="Serviço de database indisponível. Tente novamente em alguns instantes."
        )
    
    try:
        # Teste rápido de conectividade
        await client.admin.command('ping')
        return True
    except Exception as e:
        print(f"⚠️ Falha na verificação de conectividade: {e}")
        raise HTTPException(
            status_code=503, 
            detail=f"Database temporariamente indisponível: {str(e)}"
        )

# Modelos Pydantic
class CategoriaBase(BaseModel):
    nome: str
    cor: str = "#3498db"

class CategoriaCreate(CategoriaBase):
    pass

class Categoria(CategoriaBase):
    id: str
    criado_em: Optional[datetime] = None

class TipoPagamentoBase(BaseModel):
    nome: str
    icone: str = "💳"
    cor: str = "#3498db"

class TipoPagamentoCreate(TipoPagamentoBase):
    pass

class TipoPagamento(TipoPagamentoBase):
    id: str
    criado_em: Optional[datetime] = None

class GastoBase(BaseModel):
    descricao: str
    valor: float
    data_gasto: str

class GastoCreate(BaseModel):
    descricao: str
    valor: float
    categoria_id: str
    tipo_pagamento_id: str
    data_gasto: date

class Gasto(BaseModel):
    id: str
    descricao: str
    valor: float
    data_gasto: str
    categoria: Optional[dict] = None
    tipo_pagamento: Optional[dict] = None
    criado_em: Optional[datetime] = None

# 🚀 Eventos de inicialização com teste de conectividade aprimorado
@app.on_event("startup")
async def startup_db_client():
    global client, database, categorias_collection, gastos_collection, tipos_pagamento_collection
    
    if not client:
        print("❌ Cliente MongoDB não foi inicializado")
        return
    
    try:
        print("🔄 Testando conectividade com MongoDB Atlas...")
        
        # Teste de ping com timeout
        await client.admin.command('ping')
        print("✅ Ping MongoDB bem-sucedido!")
        
        # Teste de listagem de databases
        db_list = await client.list_database_names()
        print(f"📚 Databases disponíveis: {db_list}")
        
        # Teste de acesso ao database específico
        stats = await database.command("dbstats")
        print(f"📊 Database stats: {stats.get('dataSize', 0)} bytes")
        
        # Criar índices para performance
        if categorias_collection:
            await categorias_collection.create_index("nome", unique=True)
            print("✅ Índice de categorias criado")
        
        if tipos_pagamento_collection:
            await tipos_pagamento_collection.create_index("nome", unique=True)
            print("✅ Índice de tipos de pagamento criado")
        
        if gastos_collection:
            await gastos_collection.create_index("data_gasto")
            await gastos_collection.create_index("categoria.nome")
            await gastos_collection.create_index("tipo_pagamento.nome")
            print("✅ Índices de gastos criados")
        
        print("🎉 MongoDB Atlas conectado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro detalhado ao conectar MongoDB: {type(e).__name__}: {e}")
        print("🔧 Tentativas de resolução:")
        print("   1. Verificar se IP está na whitelist do MongoDB Atlas")
        print("   2. Verificar se credenciais estão corretas")
        print("   3. Verificar se cluster está ativo")
        print("   4. Verificar conectividade de rede")
        
        # Não falhar a aplicação, apenas logar o erro
        print("⚠️ Aplicação iniciará em modo degradado")

@app.on_event("shutdown")
async def shutdown_db_client():
    if client:
        client.close()
        print("📝 Conexão MongoDB fechada")

# 🏷️ ROTAS PARA CATEGORIAS
@app.get("/categorias", response_model=List[Categoria])
async def listar_categorias():
    try:
        categorias = []
        cursor = categorias_collection.find().sort("nome", 1)
        
        async for categoria in cursor:
            categoria["id"] = str(categoria["_id"])
            del categoria["_id"]
            categorias.append(categoria)
        
        return categorias
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar categorias: {e}")

@app.post("/categorias", response_model=Categoria)
async def criar_categoria(categoria: CategoriaCreate):
    try:
        # Verificar se categoria já existe
        existing = await categorias_collection.find_one({"nome": categoria.nome})
        if existing:
            raise HTTPException(status_code=400, detail="Categoria já existe")
        
        # Criar nova categoria
        categoria_data = {
            "nome": categoria.nome,
            "cor": categoria.cor,
            "criado_em": datetime.now()
        }
        
        result = await categorias_collection.insert_one(categoria_data)
        categoria_data["id"] = str(result.inserted_id)
        
        return categoria_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar categoria: {e}")

@app.delete("/categorias/{categoria_id}")
async def deletar_categoria(categoria_id: str):
    try:
        # Verificar se há gastos usando esta categoria
        gastos_count = await gastos_collection.count_documents({"categoria.id": categoria_id})
        if gastos_count > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Não é possível deletar categoria com {gastos_count} gasto(s) associado(s)"
            )
        
        result = await categorias_collection.delete_one({"_id": ObjectId(categoria_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
        
        return {"deleted": result.deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar categoria: {e}")

# 💳 ROTAS PARA TIPOS DE PAGAMENTO
@app.get("/tipos-pagamento", response_model=List[TipoPagamento])
async def listar_tipos_pagamento():
    try:
        tipos = []
        cursor = tipos_pagamento_collection.find().sort("nome", 1)
        
        async for tipo in cursor:
            tipo["id"] = str(tipo["_id"])
            del tipo["_id"]
            tipos.append(tipo)
        
        return tipos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar tipos de pagamento: {e}")

@app.post("/tipos-pagamento", response_model=TipoPagamento)
async def criar_tipo_pagamento(tipo: TipoPagamentoCreate):
    try:
        # Verificar se tipo já existe
        existing = await tipos_pagamento_collection.find_one({"nome": tipo.nome})
        if existing:
            raise HTTPException(status_code=400, detail="Tipo de pagamento já existe")
        
        # Criar novo tipo
        tipo_data = {
            "nome": tipo.nome,
            "icone": tipo.icone,
            "cor": tipo.cor,
            "criado_em": datetime.now()
        }
        
        result = await tipos_pagamento_collection.insert_one(tipo_data)
        tipo_data["id"] = str(result.inserted_id)
        
        return tipo_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar tipo de pagamento: {e}")

@app.delete("/tipos-pagamento/{tipo_id}")
async def deletar_tipo_pagamento(tipo_id: str):
    try:
        # Verificar se há gastos usando este tipo
        gastos_count = await gastos_collection.count_documents({"tipo_pagamento.id": tipo_id})
        if gastos_count > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Não é possível deletar tipo com {gastos_count} gasto(s) associado(s)"
            )
        
        result = await tipos_pagamento_collection.delete_one({"_id": ObjectId(tipo_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Tipo de pagamento não encontrado")
        
        return {"deleted": result.deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar tipo de pagamento: {e}")

# 💰 ROTAS PARA GASTOS
@app.get("/gastos", response_model=List[Gasto])
async def listar_gastos(mes: Optional[int] = None, ano: Optional[int] = None):
    try:
        # Construir filtro de data (se especificado)
        filter_query = {}
        if mes and ano:
            # Filtrar por string de data (formato YYYY-MM)
            start_date = f"{ano}-{mes:02d}-01"
            if mes == 12:
                end_date = f"{ano + 1}-01-01"
            else:
                end_date = f"{ano}-{mes + 1:02d}-01"
            
            filter_query["data_gasto"] = {
                "$gte": start_date,
                "$lt": end_date
            }
        
        gastos = []
        cursor = gastos_collection.find(filter_query).sort("data_gasto", -1)
        
        async for gasto in cursor:
            gasto["id"] = str(gasto["_id"])
            del gasto["_id"]
            gastos.append(gasto)
        
        return gastos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar gastos: {e}")

@app.post("/gastos", response_model=Gasto)
async def criar_gasto(gasto: GastoCreate):
    try:
        # Buscar dados da categoria (embutir no documento)
        categoria = await categorias_collection.find_one({"_id": ObjectId(gasto.categoria_id)})
        if not categoria:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
        
        # Buscar dados do tipo de pagamento
        tipo_pagamento = await tipos_pagamento_collection.find_one({"_id": ObjectId(gasto.tipo_pagamento_id)})
        if not tipo_pagamento:
            raise HTTPException(status_code=404, detail="Tipo de pagamento não encontrado")
        
        # 🎯 NoSQL: dados da categoria e tipo de pagamento embutidos no gasto
        gasto_data = {
            "descricao": gasto.descricao,
            "valor": gasto.valor,
            "data_gasto": gasto.data_gasto.isoformat(),  # Converter para string ISO
            "categoria": {
                "id": str(categoria["_id"]),
                "nome": categoria["nome"],
                "cor": categoria["cor"]
            },
            "tipo_pagamento": {
                "id": str(tipo_pagamento["_id"]),
                "nome": tipo_pagamento["nome"],
                "icone": tipo_pagamento["icone"],
                "cor": tipo_pagamento["cor"]
            },
            "criado_em": datetime.now()
        }
        
        result = await gastos_collection.insert_one(gasto_data)
        gasto_data["id"] = str(result.inserted_id)
        
        return gasto_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar gasto: {e}")

@app.put("/gastos/{gasto_id}", response_model=Gasto)
async def atualizar_gasto(gasto_id: str, gasto_update: GastoCreate):
    try:
        # Buscar dados da categoria
        categoria = await categorias_collection.find_one({"_id": ObjectId(gasto_update.categoria_id)})
        if not categoria:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
        
        # Buscar dados do tipo de pagamento
        tipo_pagamento = await tipos_pagamento_collection.find_one({"_id": ObjectId(gasto_update.tipo_pagamento_id)})
        if not tipo_pagamento:
            raise HTTPException(status_code=404, detail="Tipo de pagamento não encontrado")
        
        # Atualizar gasto
        update_data = {
            "descricao": gasto_update.descricao,
            "valor": gasto_update.valor,
            "data_gasto": gasto_update.data_gasto.isoformat(),  # Converter para string ISO
            "categoria": {
                "id": str(categoria["_id"]),
                "nome": categoria["nome"],
                "cor": categoria["cor"]
            },
            "tipo_pagamento": {
                "id": str(tipo_pagamento["_id"]),
                "nome": tipo_pagamento["nome"],
                "icone": tipo_pagamento["icone"],
                "cor": tipo_pagamento["cor"]
            },
            "atualizado_em": datetime.now()
        }
        
        result = await gastos_collection.update_one(
            {"_id": ObjectId(gasto_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Gasto não encontrado")
        
        # Retornar gasto atualizado
        gasto_atualizado = await gastos_collection.find_one({"_id": ObjectId(gasto_id)})
        gasto_atualizado["id"] = str(gasto_atualizado["_id"])
        del gasto_atualizado["_id"]
        
        return gasto_atualizado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar gasto: {e}")

@app.delete("/gastos/{gasto_id}")
async def deletar_gasto(gasto_id: str):
    try:
        result = await gastos_collection.delete_one({"_id": ObjectId(gasto_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Gasto não encontrado")
        
        return {"deleted": result.deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar gasto: {e}")

# 📊 RELATÓRIOS (usando agregações MongoDB)
@app.get("/relatorio/mensal/{ano}/{mes}")
async def relatorio_mensal(ano: int, mes: int):
    try:
        # Filtro de data usando strings
        start_date = f"{ano}-{mes:02d}-01"
        if mes == 12:
            end_date = f"{ano + 1}-01-01"
        else:
            end_date = f"{ano}-{mes + 1:02d}-01"
        
        date_filter = {
            "data_gasto": {
                "$gte": start_date,
                "$lt": end_date
            }
        }
        
        # 🎯 Agregação MongoDB: Total do mês
        pipeline_total = [
            {"$match": date_filter},
            {"$group": {"_id": None, "total": {"$sum": "$valor"}}}
        ]
        result_total = await gastos_collection.aggregate(pipeline_total).to_list(None)
        total = result_total[0]["total"] if result_total else 0.0
        
        # 🎯 Agregação: Gastos por categoria
        pipeline_categoria = [
            {"$match": date_filter},
            {
                "$group": {
                    "_id": "$categoria.nome",
                    "total": {"$sum": "$valor"},
                    "quantidade": {"$sum": 1},
                    "cor": {"$first": "$categoria.cor"}
                }
            },
            {"$sort": {"total": -1}}
        ]
        por_categoria = await gastos_collection.aggregate(pipeline_categoria).to_list(None)
        
        # Formatar resultado
        for item in por_categoria:
            item["nome"] = item["_id"]
            del item["_id"]
        
        # Gastos detalhados
        gastos = []
        cursor = gastos_collection.find(date_filter).sort("data_gasto", -1)
        async for gasto in cursor:
            gasto["id"] = str(gasto["_id"])
            del gasto["_id"]
            gastos.append(gasto)
        
        return {
            "mes": mes,
            "ano": ano,
            "total": total,
            "por_categoria": por_categoria,
            "gastos": gastos
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no relatório mensal: {e}")

@app.get("/relatorio/anual/{ano}")
async def relatorio_anual(ano: int):
    try:
        # 🎯 Agregação MongoDB: Dados anuais usando strings de data
        pipeline = [
            {
                "$match": {
                    "data_gasto": {
                        "$gte": f"{ano}-01-01",
                        "$lt": f"{ano + 1}-01-01"
                    }
                }
            },
            {
                "$addFields": {
                    "mes": {"$toInt": {"$substr": ["$data_gasto", 5, 2]}}
                }
            },
            {
                "$group": {
                    "_id": "$mes",
                    "total": {"$sum": "$valor"},
                    "quantidade": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        result = await gastos_collection.aggregate(pipeline).to_list(None)
        
        # Formatar resultado
        meses = []
        for item in result:
            meses.append({
                "mes": item["_id"],
                "total": item["total"],
                "quantidade": item["quantidade"]
            })
        
        return {
            "ano": ano,
            "meses": meses
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no relatório anual: {e}")

@app.get("/")
async def root():
    # Verificar status da conexão
    db_status = "🟢 Conectado"
    try:
        if client and database:
            await client.admin.command('ping')
        else:
            db_status = "🔴 Desconectado"
    except Exception as e:
        db_status = f"🟡 Instável: {str(e)[:50]}..."
    
    return {
        "message": "💰 API de Controle de Gastos",
        "version": "2.0.0",
        "database": f"MongoDB Atlas - {db_status}",
        "framework": "FastAPI + Motor",
        "ssl_config": "Otimizado para Railway",
        "docs": "/docs",
        "redoc": "/redoc",
        "health_check": "/health"
    }

@app.get("/health")
async def health_check():
    """Endpoint para verificação de saúde da aplicação"""
    try:
        if not client or not database:
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "timestamp": datetime.now().isoformat()
            }
        
        await client.admin.command('ping')
        
        # Contar documentos para verificar acesso
        categorias_count = await categorias_collection.count_documents({})
        
        return {
            "status": "healthy",
            "database": "connected",
            "categorias": categorias_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "database": f"error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Desabilitar reload em produção
        log_level="info"
    )
