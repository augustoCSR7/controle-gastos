const API_URL = 'http://localhost:8000';
let categorias = [];
let tiposPagamento = [];
let gastos = [];
let autoRefreshInterval;

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    setDateToToday();
    startAutoRefresh();
    checkConnection();
    loadCategorias();
    loadTiposPagamento();
    loadGastos();
    
    // Event listeners
    document.getElementById('form-gasto').addEventListener('submit', handleAddGasto);
    document.getElementById('form-categoria').addEventListener('submit', handleAddCategoria);
    document.getElementById('form-pagamento').addEventListener('submit', handleAddTipoPagamento);
    
    // Modal event listeners
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            e.target.classList.remove('active');
        }
    });
});

// Navegação entre seções
function showSection(sectionName) {
    // Remover active de todas as seções
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Remover active de todos os botões
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Ativar seção e botão correspondentes
    document.getElementById(sectionName + '-section').classList.add('active');
    document.querySelector(`[onclick="showSection('${sectionName}')"]`).classList.add('active');
}

// Modais
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
    
    // Limpar formulários ao fechar
    if (modalId === 'categoria-modal') {
        document.getElementById('form-categoria').reset();
        document.getElementById('categoria-cor').value = '#3498db';
    } else if (modalId === 'pagamento-modal') {
        document.getElementById('form-pagamento').reset();
        document.getElementById('pagamento-cor').value = '#3498db';
    }
}

function setDateToToday() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('gasto-data').value = today;
}

function startAutoRefresh() {
    autoRefreshInterval = setInterval(() => {
        loadGastos();
        calculateTotal();
    }, 5000);
}

async function checkConnection() {
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    
    try {
        const response = await fetch(`${API_URL}/`);
        if (response.ok) {
            statusIndicator.classList.remove('offline');
            statusText.textContent = 'Backend conectado';
        } else {
            throw new Error('Resposta inválida');
        }
    } catch (error) {
        statusIndicator.classList.add('offline');
        statusText.textContent = 'Backend offline';
    }
}

async function loadCategorias() {
    try {
        const response = await fetch(`${API_URL}/categorias`);
        categorias = await response.json();
        updateCategoriaSelect();
    } catch (error) {
        console.error('Erro ao carregar categorias:', error);
    }
}

async function loadTiposPagamento() {
    try {
        const response = await fetch(`${API_URL}/tipos-pagamento`);
        tiposPagamento = await response.json();
        updateTipoPagamentoSelect();
    } catch (error) {
        console.error('Erro ao carregar tipos de pagamento:', error);
    }
}

function updateCategoriaSelect() {
    const select = document.getElementById('gasto-categoria');
    select.innerHTML = '<option value="">Selecione uma categoria...</option>';
    
    categorias.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat.id;
        option.textContent = cat.nome;
        select.appendChild(option);
    });
}

function updateTipoPagamentoSelect() {
    const select = document.getElementById('gasto-tipo-pagamento');
    select.innerHTML = '<option value="">Selecione o tipo...</option>';
    
    tiposPagamento.forEach(tipo => {
        const option = document.createElement('option');
        option.value = tipo.id;
        option.textContent = `${tipo.icone} ${tipo.nome}`;
        select.appendChild(option);
    });
}

async function loadGastos() {
    try {
        const response = await fetch(`${API_URL}/gastos`);
        gastos = await response.json();
        
        updateHistorico();
        calculateTotal();
    } catch (error) {
        console.error('Erro ao carregar gastos:', error);
    }
}

function updateHistorico() {
    const container = document.getElementById('historico-content');
    
    if (gastos.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <h3>📝 Nenhum gasto encontrado</h3>
                <p>Comece adicionando seu primeiro gasto!</p>
            </div>
        `;
        return;
    }
    
    // Ordenar por data (mais recente primeiro)
    const gastosSorted = gastos.sort((a, b) => new Date(b.data_gasto) - new Date(a.data_gasto));
    
    container.innerHTML = gastosSorted.map(gasto => {
        const categoria = gasto.categoria;
        const tipoPagamento = gasto.tipo_pagamento;
        const dataFormatada = new Date(gasto.data_gasto).toLocaleDateString('pt-BR');
        
        return `
            <div class="gasto-item">
                <div class="gasto-info">
                    <div class="gasto-descricao">${gasto.descricao}</div>
                    <div class="gasto-detalhes">
                        <span>📅 ${dataFormatada}</span>
                        ${categoria ? `<span class="categoria-badge" style="background: ${categoria.cor}">${categoria.nome}</span>` : ''}
                        ${tipoPagamento ? `<span class="pagamento-badge" style="background: ${tipoPagamento.cor}">${tipoPagamento.icone} ${tipoPagamento.nome}</span>` : ''}
                    </div>
                </div>
                <div class="gasto-valor">R$ ${parseFloat(gasto.valor).toFixed(2).replace('.', ',')}</div>
                <button class="btn btn-danger" onclick="deleteGasto('${gasto.id}')">🗑️</button>
            </div>
        `;
    }).join('');
}

function calculateTotal() {
    const total = gastos.reduce((sum, gasto) => sum + parseFloat(gasto.valor), 0);
    document.getElementById('total-gastos').textContent = 
        `R$ ${total.toFixed(2).replace('.', ',')}`;
}

async function handleAddGasto(event) {
    event.preventDefault();
    
    const descricao = document.getElementById('gasto-descricao').value;
    const valor = parseFloat(document.getElementById('gasto-valor').value);
    const categoria_id = document.getElementById('gasto-categoria').value;
    const tipo_pagamento_id = document.getElementById('gasto-tipo-pagamento').value;
    const data_gasto = document.getElementById('gasto-data').value;
    
    try {
        const response = await fetch(`${API_URL}/gastos`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ descricao, valor, categoria_id, tipo_pagamento_id, data_gasto })
        });
        
        if (response.ok) {
            // Limpar formulário
            document.getElementById('form-gasto').reset();
            setDateToToday();
            
            // Recarregar dados
            loadGastos();
            
            // Mostrar mensagem de sucesso
            showNotification('Gasto adicionado com sucesso!', 'success');
        } else {
            const error = await response.json();
            showNotification(`Erro: ${error.detail}`, 'error');
        }
    } catch (error) {
        showNotification(`Erro na conexão: ${error.message}`, 'error');
    }
}

async function deleteGasto(gastoId) {
    if (!confirm('Tem certeza que deseja excluir este gasto?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/gastos/${gastoId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadGastos();
            showNotification('Gasto removido com sucesso!', 'success');
        } else {
            const error = await response.json();
            showNotification(`Erro: ${error.detail}`, 'error');
        }
    } catch (error) {
        showNotification(`Erro na conexão: ${error.message}`, 'error');
    }
}

async function handleAddCategoria(event) {
    event.preventDefault();
    
    const nome = document.getElementById('categoria-nome').value;
    const cor = document.getElementById('categoria-cor').value;
    
    try {
        const response = await fetch(`${API_URL}/categorias`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome, cor })
        });
        
        if (response.ok) {
            closeModal('categoria-modal');
            loadCategorias();
            showNotification('Categoria criada com sucesso!', 'success');
        } else {
            const error = await response.json();
            showNotification(`Erro: ${error.detail}`, 'error');
        }
    } catch (error) {
        showNotification(`Erro na conexão: ${error.message}`, 'error');
    }
}

async function handleAddTipoPagamento(event) {
    event.preventDefault();
    
    const nome = document.getElementById('pagamento-nome').value;
    const icone = document.getElementById('pagamento-icone').value;
    const cor = document.getElementById('pagamento-cor').value;
    
    try {
        const response = await fetch(`${API_URL}/tipos-pagamento`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome, icone, cor })
        });
        
        if (response.ok) {
            closeModal('pagamento-modal');
            loadTiposPagamento();
            showNotification('Tipo de pagamento criado com sucesso!', 'success');
        } else {
            const error = await response.json();
            showNotification(`Erro: ${error.detail}`, 'error');
        }
    } catch (error) {
        showNotification(`Erro na conexão: ${error.message}`, 'error');
    }
}

// Notificações simples
function showNotification(message, type = 'info') {
    // Criar elemento de notificação
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Estilos inline para a notificação
    Object.assign(notification.style, {
        position: 'fixed',
        top: '4rem',
        right: '1rem',
        padding: '1rem 1.5rem',
        borderRadius: '8px',
        color: 'white',
        fontWeight: '600',
        zIndex: '1001',
        transform: 'translateX(100%)',
        transition: 'transform 0.3s ease',
        backgroundColor: type === 'success' ? '#059669' : 
                        type === 'error' ? '#dc2626' : '#2563eb'
    });
    
    document.body.appendChild(notification);
    
    // Animar entrada
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remover após 3 segundos
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}
