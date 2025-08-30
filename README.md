# 💰 Controle de Gastos

Sistema completo de controle financeiro pessoal com interface web e API RESTful.

## 🚀 Tecnologias

- **Backend**: FastAPI + MongoDB Atlas
- **Frontend**: HTML5 + CSS3 + JavaScript
- **Deploy**: Railway (Backend) + Vercel (Frontend)

## 📂 Estrutura do Projeto

```
├── backend/           # API FastAPI
│   ├── main.py       # Aplicação principal
│   ├── requirements.txt
│   └── Procfile      # Configuração Railway
├── frontend/         # Interface web
│   ├── index.html
│   ├── script.js
│   └── styles.css
└── docs/            # Documentação
    ├── RAILWAY_CONFIG.txt
    └── RAILWAY_MONGODB_GUIDE.md
```

## 🛠️ Configuração Local

### 1. Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py
```

### 2. Frontend
Abra `frontend/index.html` no navegador ou use um servidor local.

## 🌐 Deploy

### Backend (Railway)
1. Configure as variáveis de ambiente (ver `docs/RAILWAY_CONFIG.txt`)
2. Push para GitHub
3. Railway faz deploy automático

### Frontend (Vercel)
1. Importe o repositório no Vercel
2. Configure Build Settings:
   - Framework: Other
   - Output Directory: `frontend`

## 📊 Funcionalidades

- ✅ Controle de gastos com categorias
- ✅ Tipos de pagamento personalizáveis
- ✅ Relatórios mensais e anuais
- ✅ Interface responsiva
- ✅ API RESTful completa
- ✅ Validação de dados
- ✅ Filtros e buscas

## 🔗 Links

- **API Docs**: `/docs` (Swagger)
- **Health Check**: `/health`
- **Frontend Demo**: [Em breve]

## 📝 Licença

MIT License - veja arquivo de licença para detalhes.
