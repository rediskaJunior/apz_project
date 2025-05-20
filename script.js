// ======================= CONFIGURATION ============================
const API_URL = 'http://localhost:5010/api';
const REP_URL = 'http://localhost:8590';
let token = localStorage.getItem('token') || '';

const headers = {
    'Content-Type': 'application/json'
};

if (token) {
    headers['Authorization'] = `Bearer ${token}`;
}

window.onload = function() {
    updateAuthStatus();
};

// ========================== AUTHORISATION =======================
function updateAuthStatus() {
    const authStatus = document.getElementById('auth-status');
    if (token) {
        authStatus.textContent = 'Ви авторизовані';
        authStatus.className = 'status success';
    } else {
        authStatus.textContent = 'Ви не авторизовані';
        authStatus.className = 'status error';
    }
}

async function login() {
    const login = document.getElementById('login').value;
    const password = document.getElementById('password').value;
    
    if (!login || !password) {
        showResponse('Помилка: Заповніть всі поля', true);
        return;
    }
    
    try {
        // send POST request to api gateway
        const data = await postAPI('/auth/login', { login, password });
        token = data.token; // store token data (here will be JWT)
        localStorage.setItem('token', token);
        updateAuthStatus(); // update authentification status
        showResponse('Успішно авторизовано!'); // the response field for debug
    } catch (error) {
        showResponse(`Помилка авторизації: ${error.message}`, true);
    }
}

function logout() {
    token = '';
    localStorage.removeItem('token');
    updateAuthStatus();
    showResponse('Ви вийшли з системи.');
    showSection('auth');
}

async function register() {
    const login = document.getElementById('login').value;
    const password = document.getElementById('password').value;
    
    if (!login || !password) { // check if user filled out the inputs
        showResponse('Помилка: Заповніть всі поля', true);
        return;
    } 
    
    try {
        // send POST request to api gateway
        const data = await postAPI('/auth/register', { login, password });
        showResponse('Успішно зареєстровано. Тепер можете увійти.');
    } catch (error) {
        showResponse(`Помилка реєстрації: ${error.message}`, true);
    }
}


// ====================================== HTML FUNCTIONS ===========================
function showSection(section) {
    document.getElementById('auth-section').classList.add('hidden');
    document.getElementById('repairs-section').classList.add('hidden');
    document.getElementById('orders-section').classList.add('hidden');
    document.getElementById('inventory-section').classList.add('hidden');
    
    document.getElementById(`${section}-section`).classList.remove('hidden');
}

function showResponse(data, isError = false) {
    const responseElement = document.getElementById('response');
    
    if (isError) {
        responseElement.style.color = 'red';
        responseElement.textContent = data;
    } else {
        responseElement.style.color = 'black';
        if (typeof data === 'object') {
            responseElement.innerHTML = createTable(data);
        } else {
            responseElement.textContent = data;
        }
    }
}

function createTable(data) {
    if (typeof data === 'object' && !Array.isArray(data)) {
        const keys = Object.keys(data);
        
        if (keys.length === 0) {
            return 'No data available';
        }
        
        const firstItemKey = keys[0];
        const firstItem = data[firstItemKey];
        const nestedKeys = Object.keys(firstItem);
        
        const headers = ['product_key', ...nestedKeys];
        
        let tableHTML = '<table class="data-table">';
        
        tableHTML += '<thead><tr>';
        headers.forEach(header => {
            tableHTML += `<th>${formatHeader(header)}</th>`;
        });
        tableHTML += '</tr></thead>';
        
        tableHTML += '<tbody>';
        keys.forEach(key => {
            const item = data[key];
            tableHTML += '<tr>';
            
            tableHTML += `<td>${key}</td>`;
            
            nestedKeys.forEach(nestedKey => {
                tableHTML += `<td>${item[nestedKey] !== null && item[nestedKey] !== undefined ? item[nestedKey] : ''}</td>`;
            });
            
            tableHTML += '</tr>';
        });
        tableHTML += '</tbody></table>';
        
        return tableHTML;
    }
    
    if (Array.isArray(data)) {
        if (data.length === 0) {
            return 'No data available';
        }
        
        const headers = Object.keys(data[0]);
        
        let tableHTML = '<table class="data-table">';
        
        tableHTML += '<thead><tr>';
        headers.forEach(header => {
            tableHTML += `<th>${formatHeader(header)}</th>`;
        });
        tableHTML += '</tr></thead>';
        
        tableHTML += '<tbody>';
        data.forEach(item => {
            tableHTML += '<tr>';
            headers.forEach(header => {
                tableHTML += `<td>${item[header] !== null && item[header] !== undefined ? item[header] : ''}</td>`;
            });
            tableHTML += '</tr>';
        });
        tableHTML += '</tbody></table>';
        
        return tableHTML;
    }
    
    return 'No data available';
}

function formatHeader(header) {
    return header
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// ========================== ENDPOINT CALLS ============================
async function getAPI(endpoint) {
    const url = `${REP_URL}${endpoint}`;
    console.log(`Making GET request to ${url}`);
    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                ...(token && { 'Authorization': `Bearer ${token}` })
            }
        });

        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
            const text = await response.text(); // maybe HTML
            throw new Error("Очікував JSON, але отримав: " + text.slice(0, 100));
        }

        const responseData = await response.json();

        if (!response.ok) {
            throw new Error(responseData.detail || 'Unknown error occurred');
        }

        return responseData;
    } catch (error) {
        console.error('GET API Error:', error);
        throw error;
    }
}

async function postAPI(endpoint, data) {
    const url = `${REP_URL}${endpoint}`;
    console.log(`Making POST request to ${url} with data:`, data);
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(token && { 'Authorization': `Bearer ${token}` })
            },
            body: JSON.stringify(data)
        });

        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
            const text = await response.text(); // maybe HTML
            throw new Error("Очікував JSON, але отримав: " + text.slice(0, 100));
        }

        const responseData = await response.json();

        if (!response.ok) {
            throw new Error(responseData.detail || 'Unknown error occurred');
        }

        return responseData;
    } catch (error) {
        console.error('POST API Error:', error);
        throw error;
    }
}

// ================== REPAIRS ==============================
async function getRepairs() {
    console.log('getRepairs function called');
    try {
        const data = await getAPI('/repairs');
        showResponse(data);
    } catch (error) {
        showResponse(`Помилка отримання ремонтів: ${error.message}`, true);
    }
}

function addRepairPart() {
    console.log('addRepairPart function called');
    const container = document.getElementById('repair-parts-container');
    const partDiv = document.createElement('div');
    partDiv.className = 'repair-part';
    partDiv.innerHTML = `
        <input class="part-id" placeholder="ID деталі">
        <input class="part-qty" type="number" placeholder="Кількість" min="1" value="1">
        <button type="button" class="remove-part" onclick="removeRepairPart(this)">✕</button>
    `;
    container.appendChild(partDiv);
}

// async function getRepairs() {
//     console.log('getRepairs function called');
//     try {
//         const data = await getAPI('/repairs');
//         showResponse(data);
//     } catch (error) {
//         showResponse(`Помилка отримання ремонтів: ${error.message}`, true);
//     }
// }

function removeRepairPart(button) {
    console.log('removeRepairPart function called');
    const partDiv = button.parentElement;
    partDiv.remove();
}

async function createRepair() {
    console.log('createRepair function called');
    
    const phoneModel = document.getElementById('phone-model').value.trim();
    const issue = document.getElementById('issue').value.trim();

    const partElements = document.querySelectorAll('.repair-part');
    const orders = {};

    partElements.forEach((partEl, index) => {
        const partId = partEl.querySelector('.part-id').value.trim();
        const quantityInput = partEl.querySelector('.part-qty').value.trim();
        const quantity = parseInt(quantityInput, 10);

        console.log(`Part ${index + 1}: ID=${partId}, Quantity=${quantity}`);

        if (partId && quantity && quantity > 0) {
            orders[partId] = quantity;
        }
    });

    console.log('Collected orders:', orders);

    if (!phoneModel || !issue) {
        showResponse('Помилка: Заповніть модель телефону та проблему', true);
        return;
    }

    if (Object.keys(orders).length === 0) {
        showResponse('Помилка: Додайте хоча б одну деталь з кількістю', true);
        return;
    }

    try {
        console.log('Sending repair request with orders:', { orders });
        
        const data = await postAPI('/add_repair', { orders });
        console.log('Repair request successful:', data);
        showResponse(data);
        
        document.getElementById('phone-model').value = '';
        document.getElementById('issue').value = '';
        
        const container = document.getElementById('repair-parts-container');
        container.innerHTML = '';
        addRepairPart();
    } catch (error) {
        console.error('Error in createRepair:', error);
        showResponse(`Помилка створення ремонту: ${error.message}`, true);
    }
}

// =============================== ORDERS ===========================
async function getOrders() {
    try {
        const data = await getAPI('/orders');
        showResponse(data);
    } catch (error) {
        showResponse(`Помилка отримання замовлень: ${error.message}`, true);
    }
}

async function createOrder() {
   const requestData = {
        orders: {
            "part-123": 2,
            "part-456": 1
        }
    };

    try {
        const data = await postAPI('/add_order', requestData);
        showResponse(data);
    } catch (error) {
        showResponse(`Помилка створення замовлення: ${error.message}`, true);
    }
}

// =============================== INVENTORY ===========================
async function getInventory() {
    try {
        const data = await getAPI('/inventory');
        showResponse(data);
    } catch (error) {
        showResponse(`Помилка отримання компонентів: ${error.message}`, true);
    }
}

// ===================== LOADER =====================
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');
    
    // Make sure at least one part field exists
    if (document.getElementById('repair-parts-container') && 
        document.getElementById('repair-parts-container').children.length === 0) {
        addRepairPart();
    }
    
    // Add direct event listeners to buttons to ensure they work
    const createRepairBtn = document.querySelector('button[onclick="createRepair()"]');
    if (createRepairBtn) {
        createRepairBtn.addEventListener('click', function() {
            console.log('Create repair button clicked via event listener');
            createRepair();
        });
    }
    
    const getRepairsBtn = document.querySelector('button[onclick="getRepairs()"]');
    if (getRepairsBtn) {
        getRepairsBtn.addEventListener('click', function() {
            console.log('Get repairs button clicked via event listener');
            getRepairs();
        });
    }
    
    const addPartBtn = document.querySelector('button[onclick="addRepairPart()"]');
    if (addPartBtn) {
        addPartBtn.addEventListener('click', function() {
            console.log('Add part button clicked via event listener');
            addRepairPart();
        });
    }
    
    // Add remove buttons to existing repair parts if they don't have them
    document.querySelectorAll('.repair-part').forEach(part => {
        if (!part.querySelector('.remove-part')) {
            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'remove-part';
            removeBtn.textContent = '✕';
            removeBtn.onclick = function() { removeRepairPart(this); };
            part.appendChild(removeBtn);
        }
    });
});