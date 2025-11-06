// Configuração da API
const API_URL = 'http://localhost:5000';

// Regras de validação para nomes de componentes
const COMPONENT_NAME_PATTERN = /^[a-z\s]+$/;

function sanitizeNameValue(value) {
    if (!value) return '';
    return value.toLowerCase();
}

function sanitizeNameInput(input) {
    if (!input) return;
    const sanitizedValue = sanitizeNameValue(input.value);
    if (input.value !== sanitizedValue) {
        input.value = sanitizedValue;
    }
}

function attachComponentInputListeners(container) {
    if (!container) return;
    const inputs = container.querySelectorAll('.component-name, .component-parent');
    inputs.forEach((input) => {
        input.addEventListener('input', () => sanitizeNameInput(input));
    });
}

function isValidComponentName(name) {
    return typeof name === 'string' && name.trim().length > 0 && COMPONENT_NAME_PATTERN.test(name);
}

document.addEventListener('DOMContentLoaded', () => {
    attachComponentInputListeners(document.getElementById('componentsContainer'));
    const productNameInput = document.getElementById('productName');
    if (productNameInput) {
        productNameInput.addEventListener('input', () => sanitizeNameInput(productNameInput));
    }
});

// Funções de limpeza para cada aba
function clearCreateProductTab() {
    document.getElementById('productName').value = '';
    document.getElementById('componentsContainer').innerHTML = `
        <div class="component-input-group">
            <input type="text" class="component-name" placeholder="Nome do Componente">
            <input type="text" class="component-parent" placeholder="Pai (deixe vazio para raiz)">
            <input type="number" class="component-quantity" placeholder="Quantidade" min="1" value="1">
            <input type="number" class="component-cost" step="0.01" placeholder="Custo" min="0">
            <button class="remove-btn" onclick="removeComponent(this)">✖</button>
        </div>
    `;
    attachComponentInputListeners(document.getElementById('componentsContainer'));
    const messageDiv = document.getElementById('createProductMessage');
    if (messageDiv) messageDiv.innerHTML = '';
}

function clearViewProductsTab() {
    document.getElementById('productsList').innerHTML = '';
    document.getElementById('productDetails').innerHTML = '';
}

function clearExplosionTab() {
    document.getElementById('explosionProductSelect').value = '';
    document.getElementById('explosionQuantity').value = '';
    document.getElementById('explosionResult').innerHTML = '';
}

function clearUpdateComponentTab() {
    document.getElementById('updateProductSelect').value = '';
    document.getElementById('updateComponentSelect').innerHTML = '<option value="">Primeiro selecione um produto</option>';
    document.getElementById('newCost').value = '';
    const messageDiv = document.getElementById('updateComponentMessage');
    if (messageDiv) messageDiv.innerHTML = '';
}

// Gerenciamento de Tabs
function openTab(evt, tabName) {
    const tabContents = document.getElementsByClassName('tab-content');
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.remove('active');
    }
    
    const tabButtons = document.getElementsByClassName('tab-button');
    for (let i = 0; i < tabButtons.length; i++) {
        tabButtons[i].classList.remove('active');
    }
    
    document.getElementById(tabName).classList.add('active');
    evt.currentTarget.classList.add('active');
    
    // Limpa e carrega dados quando necessário
    if (tabName === 'createProduct') {
        clearCreateProductTab();
    } else if (tabName === 'viewProducts') {
        clearViewProductsTab();
        loadProducts();
    } else if (tabName === 'explosion') {
        clearExplosionTab();
        loadProductsForExplosion();
    } else if (tabName === 'updateComponent') {
        clearUpdateComponentTab();
        loadProductsForUpdate();
    }
}

// Adicionar componente
function addComponent() {
    const container = document.getElementById('componentsContainer');
    const newGroup = document.createElement('div');
    newGroup.className = 'component-input-group';
    newGroup.innerHTML = `
        <input type="text" class="component-name" placeholder="Nome do Componente">
        <input type="text" class="component-parent" placeholder="Pai (deixe vazio para raiz)">
        <input type="number" class="component-quantity" placeholder="Quantidade" min="1" value="1">
        <input type="number" class="component-cost" step="0.01" placeholder="Custo" min="0">
        <button class="remove-btn" onclick="removeComponent(this)">✖</button>
    `;
    container.appendChild(newGroup);
    attachComponentInputListeners(newGroup);
}

// Remover componente
function removeComponent(button) {
    button.parentElement.remove();
}

// Criar produto
async function createProduct() {
    const productNameInput = document.getElementById('productName');
    sanitizeNameInput(productNameInput);
    const productName = sanitizeNameValue(productNameInput.value).trim();
    productNameInput.value = productName;
    const messageDiv = document.getElementById('createProductMessage');

    if (!productName) {
        showMessage(messageDiv, 'Por favor, insira o nome do produto.', 'error');
        return;
    }

    if (!isValidComponentName(productName)) {
        showMessage(messageDiv, 'O nome do produto deve conter apenas letras minúsculas e espaços.', 'error');
        return;
    }

    // Coleta componentes
    const componentGroups = document.querySelectorAll('#componentsContainer .component-input-group');
    const components = [];

    for (let group of componentGroups) {
        const nameInput = group.querySelector('.component-name');
        const parentInput = group.querySelector('.component-parent');

        sanitizeNameInput(nameInput);
        sanitizeNameInput(parentInput);

        const name = sanitizeNameValue(nameInput.value).trim();
        const parentRaw = parentInput.value ? sanitizeNameValue(parentInput.value).trim() : '';
        nameInput.value = name;
        parentInput.value = parentRaw;
        const parent = parentRaw || null;
        const quantity = parseInt(group.querySelector('.component-quantity').value);
        const cost = parseFloat(group.querySelector('.component-cost').value);

        if (!name || isNaN(quantity) || isNaN(cost)) {
            showMessage(messageDiv, 'Preencha todos os campos dos componentes corretamente.', 'error');
            return;
        }

        if (!isValidComponentName(name)) {
            showMessage(messageDiv, 'Os nomes dos componentes devem conter apenas letras minúsculas e espaços.', 'error');
            return;
        }

        if (parent && !isValidComponentName(parent)) {
            showMessage(messageDiv, 'Os nomes dos componentes devem conter apenas letras minúsculas e espaços.', 'error');
            return;
        }

        components.push({ name, parent, quantity, cost });
    }
    
    if (components.length === 0) {
        showMessage(messageDiv, 'Adicione pelo menos um componente.', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/products`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: productName, components })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage(messageDiv, `✅ ${data.message}`, 'success');
            document.getElementById('productName').value = '';
            document.getElementById('componentsContainer').innerHTML = `
                <div class="component-input-group">
                    <input type="text" class="component-name" placeholder="Nome do Componente">
                    <input type="text" class="component-parent" placeholder="Pai (deixe vazio para raiz)">
                    <input type="number" class="component-quantity" placeholder="Quantidade" min="1" value="1">
                    <input type="number" class="component-cost" step="0.01" placeholder="Custo" min="0">
                    <button class="remove-btn" onclick="removeComponent(this)">✖</button>
                </div>
            `;
        } else {
            showMessage(messageDiv, `❌ ${data.error}`, 'error');
        }
    } catch (error) {
        showMessage(messageDiv, `❌ Erro ao conectar com o servidor: ${error.message}`, 'error');
    }
}

// Carregar produtos
async function loadProducts() {
    const listDiv = document.getElementById('productsList');
    listDiv.innerHTML = '<p>Carregando...</p>';
    
    try {
        const response = await fetch(`${API_URL}/products`);
        const products = await response.json();
        
        if (products.length === 0) {
            listDiv.innerHTML = '<p>Nenhum produto cadastrado.</p>';
            return;
        }
        
        listDiv.innerHTML = '';
        products.forEach(product => {
            const card = document.createElement('div');
            card.className = 'product-card';
            card.innerHTML = `
                <h3>${product.name}</h3>
                <p>ID: ${product.id}</p>
                <p>Custo Total: R$ ${product.total_cost.toFixed(2)}</p>
            `;
            card.onclick = () => loadProductDetails(product.id);
            listDiv.appendChild(card);
        });
    } catch (error) {
        listDiv.innerHTML = `<p class="error">Erro ao carregar produtos: ${error.message}</p>`;
    }
}

// Carregar detalhes do produto
async function loadProductDetails(productId) {
    const detailsDiv = document.getElementById('productDetails');
    detailsDiv.innerHTML = '<p>Carregando detalhes...</p>';
    
    try {
        // Busca detalhes
        const response = await fetch(`${API_URL}/products/${productId}`);
        const product = await response.json();
        
        // Busca árvore
        const treeResponse = await fetch(`${API_URL}/products/${productId}/tree`);
        const treeData = await treeResponse.json();
        
        let html = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2>${product.name}</h2>
                <button class="btn-danger" onclick="deleteProduct(${product.id}, '${product.name}')">🗑️ Excluir Produto</button>
            </div>
            <p><strong>ID:</strong> ${product.id}</p>
            <p><strong>Custo Total:</strong> R$ ${product.total_cost.toFixed(2)}</p>
            
            <h3>Árvore Hierárquica</h3>
            <div class="tree-view">${treeData.tree}</div>
            
            <h3>Componentes</h3>
            <table class="components-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Nome</th>
                        <th>Pai</th>
                        <th>Quantidade</th>
                        <th>Custo Unitário</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        product.components.forEach(comp => {
            const isRoot = !comp.parent_name;
            html += `
                <tr>
                    <td>${comp.id}</td>
                    <td>${comp.name}</td>
                    <td>${comp.parent_name || '-'}</td>
                    <td>
                        <input type="number" 
                               id="qty-${comp.id}" 
                               value="${comp.quantity}" 
                               min="1" 
                               style="width: 70px; padding: 5px;"
                               onchange="updateQuantity(${comp.id}, ${productId})">
                    </td>
                    <td>R$ ${comp.cost.toFixed(2)}</td>
                    <td>
                        ${isRoot ? '<span style="color: #999;">Raiz</span>' : 
                          `<button class="btn-delete-small" onclick="deleteComponent(${comp.id}, '${comp.name}', ${productId})">🗑️</button>`}
                    </td>
                </tr>
            `;
        });
        
        html += `
                </tbody>
            </table>
        `;
        
        detailsDiv.innerHTML = html;
    } catch (error) {
        detailsDiv.innerHTML = `<p class="error">Erro ao carregar detalhes: ${error.message}</p>`;
    }
}

// Atualizar quantidade do componente
async function updateQuantity(componentId, productId) {
    const input = document.getElementById(`qty-${componentId}`);
    const newQuantity = parseInt(input.value);
    
    if (isNaN(newQuantity) || newQuantity < 1) {
        alert('Quantidade inválida. Deve ser maior ou igual a 1.');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/components/${componentId}/quantity`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quantity: newQuantity })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Recarrega os detalhes do produto para mostrar o novo custo total
            loadProductDetails(productId);
            showTemporaryMessage(`✅ Quantidade atualizada! Novo custo total: R$ ${data.product_new_total_cost.toFixed(2)}`);
        } else {
            alert(`Erro: ${data.error}`);
            loadProductDetails(productId);
        }
    } catch (error) {
        alert(`Erro ao atualizar quantidade: ${error.message}`);
    }
}

// Excluir componente
async function deleteComponent(componentId, componentName, productId) {
    if (!confirm(`Tem certeza que deseja excluir o componente "${componentName}"?\n\nATENÇÃO: Todos os subcomponentes também serão excluídos!`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/components/${componentId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            loadProductDetails(productId);
            showTemporaryMessage(`✅ ${data.message}`);
        } else {
            alert(`Erro: ${data.error}`);
        }
    } catch (error) {
        alert(`Erro ao excluir componente: ${error.message}`);
    }
}

// Excluir produto
async function deleteProduct(productId, productName) {
    if (!confirm(`Tem certeza que deseja excluir o produto "${productName}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/products/${productId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            clearViewProductsTab();
            loadProducts();
            showTemporaryMessage(`✅ ${data.message}`);
        } else {
            alert(`Erro: ${data.error}`);
        }
    } catch (error) {
        alert(`Erro ao excluir produto: ${error.message}`);
    }
}

// Mostrar mensagem temporária
function showTemporaryMessage(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'floating-message success';
    messageDiv.textContent = message;
    document.body.appendChild(messageDiv);
    
    setTimeout(() => {
        messageDiv.style.opacity = '0';
        setTimeout(() => messageDiv.remove(), 300);
    }, 3000);
}

// Carregar produtos para explosão
async function loadProductsForExplosion() {
    const select = document.getElementById('explosionProductSelect');
    select.innerHTML = '<option value="">Carregando...</option>';
    
    try {
        const response = await fetch(`${API_URL}/products`);
        const products = await response.json();
        
        select.innerHTML = '<option value="">Selecione um produto</option>';
        products.forEach(product => {
            const option = document.createElement('option');
            option.value = product.id;
            option.textContent = `${product.name} (R$ ${product.total_cost.toFixed(2)})`;
            select.appendChild(option);
        });
    } catch (error) {
        select.innerHTML = '<option value="">Erro ao carregar</option>';
    }
}

// Calcular explosão
async function calculateExplosion() {
    const productId = document.getElementById('explosionProductSelect').value;
    const quantity = parseInt(document.getElementById('explosionQuantity').value);
    const resultDiv = document.getElementById('explosionResult');
    
    if (!productId || isNaN(quantity) || quantity <= 0) {
        showMessage(resultDiv, 'Selecione um produto e informe uma quantidade válida.', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/products/${productId}/explosion/${quantity}`);
        const data = await response.json();
        
        if (response.ok) {
            let html = `
                <h3>💥 Explosão: ${data.product_name}</h3>
                <p><strong>Quantidade a Produzir:</strong> ${data.production_quantity} unidades</p>
                <h4>Componentes Necessários:</h4>
                <table class="components-table">
                    <thead>
                        <tr>
                            <th>Componente</th>
                            <th>Quantidade</th>
                            <th>Custo Unitário</th>
                            <th>Custo Total</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            data.components_needed.forEach(comp => {
                html += `
                    <tr>
                        <td>${comp.name}</td>
                        <td>${comp.required_quantity}</td>
                        <td>R$ ${comp.unit_cost.toFixed(2)}</td>
                        <td>R$ ${comp.total_cost.toFixed(2)}</td>
                    </tr>
                `;
            });
            
            html += `
                    </tbody>
                </table>
                <h3 style="margin-top: 20px; color: #667eea;">
                    Custo Total de Aquisição: R$ ${data.total_acquisition_cost.toFixed(2)}
                </h3>
            `;
            
            resultDiv.innerHTML = html;
            resultDiv.className = 'result-box success';
        } else {
            showMessage(resultDiv, `❌ ${data.error}`, 'error');
        }
    } catch (error) {
        showMessage(resultDiv, `❌ Erro: ${error.message}`, 'error');
    }
}

// Carregar produtos para o dropdown de atualização
async function loadProductsForUpdate() {
    try {
        const response = await fetch(`${API_URL}/products`);
        const products = await response.json();
        
        const select = document.getElementById('updateProductSelect');
        select.innerHTML = '<option value="">Selecione um produto</option>';
        
        if (Array.isArray(products) && products.length > 0) {
            products.forEach(product => {
                const option = document.createElement('option');
                option.value = product.id;
                option.textContent = `${product.name} (ID: ${product.id})`;
                select.appendChild(option);
            });
        } else {
            select.innerHTML = '<option value="">Nenhum produto cadastrado</option>';
        }
    } catch (error) {
        console.error('Erro ao carregar produtos:', error);
        const select = document.getElementById('updateProductSelect');
        select.innerHTML = '<option value="">Erro ao carregar produtos</option>';
    }
}

// Carregar componentes do produto selecionado
async function loadComponentsForUpdate() {
    const productId = document.getElementById('updateProductSelect').value;
    const componentSelect = document.getElementById('updateComponentSelect');
    
    if (!productId) {
        componentSelect.innerHTML = '<option value="">Primeiro selecione um produto</option>';
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/products/${productId}`);
        const data = await response.json();
        
        componentSelect.innerHTML = '<option value="">Selecione um componente</option>';
        
        if (data.components && data.components.length > 0) {
            data.components.forEach(comp => {
                const option = document.createElement('option');
                option.value = comp.id;
                const parentInfo = comp.parent_name ? ` (Pai: ${comp.parent_name})` : ' (Raiz)';
                option.textContent = `${comp.name}${parentInfo} - R$ ${comp.cost.toFixed(2)}`;
                componentSelect.appendChild(option);
            });
        } else {
            componentSelect.innerHTML = '<option value="">Nenhum componente encontrado</option>';
        }
    } catch (error) {
        console.error('Erro ao carregar componentes:', error);
        componentSelect.innerHTML = '<option value="">Erro ao carregar componentes</option>';
    }
}

// Atualizar componente (implosão)
async function updateComponent() {
    const componentId = parseInt(document.getElementById('updateComponentSelect').value);
    const newCost = parseFloat(document.getElementById('newCost').value);
    const resultDiv = document.getElementById('updateResult');
    
    if (!componentId || isNaN(componentId)) {
        showMessage(resultDiv, 'Selecione um componente.', 'error');
        return;
    }
    
    if (isNaN(newCost) || newCost < 0) {
        showMessage(resultDiv, 'Informe um custo válido.', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/components/${componentId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cost: newCost })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            let html = `
                <h3>✅ ${data.message}</h3>
                <p><strong>Componente:</strong> ${data.component_name}</p>
                <p><strong>Custo Anterior:</strong> R$ ${data.old_cost.toFixed(2)}</p>
                <p><strong>Novo Custo:</strong> R$ ${data.new_cost.toFixed(2)}</p>
            `;
            
            if (data.implosion_performed && data.affected_products.length > 0) {
                html += `
                    <h4 style="margin-top: 20px;">🔄 Implosão Realizada - Produtos Afetados:</h4>
                    <table class="components-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Produto</th>
                                <th>Novo Custo Total</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                data.affected_products.forEach(prod => {
                    html += `
                        <tr>
                            <td>${prod.id}</td>
                            <td>${prod.name}</td>
                            <td>R$ ${prod.new_total_cost.toFixed(2)}</td>
                        </tr>
                    `;
                });
                
                html += `
                        </tbody>
                    </table>
                `;
            } else {
                html += '<p><em>Nenhum produto foi afetado por esta atualização.</em></p>';
            }
            
            resultDiv.innerHTML = html;
            resultDiv.className = 'result-box success';
        } else {
            showMessage(resultDiv, `❌ ${data.error}`, 'error');
        }
    } catch (error) {
        showMessage(resultDiv, `❌ Erro: ${error.message}`, 'error');
    }
}

// Função auxiliar para mostrar mensagens
function showMessage(element, message, type) {
    element.textContent = message;
    element.className = `message ${type}`;
    setTimeout(() => {
        element.textContent = '';
        element.className = 'message';
    }, 5000);
}

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    console.log('Sistema de Gerenciamento de Produtos carregado!');
});