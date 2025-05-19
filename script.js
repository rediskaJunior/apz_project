// Конфігурація API
const API_URL = 'http://localhost:5010/api';
let token = localStorage.getItem('token') || '';

// Ініціалізація при завантаженні сторінки
window.onload = function() {
    updateAuthStatus();
};

// Оновлення статусу авторизації
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

// Показ відповідного розділу
function showSection(section) {
    // Приховуємо всі розділи
    document.getElementById('auth-section').classList.add('hidden');
    document.getElementById('repairs-section').classList.add('hidden');
    document.getElementById('orders-section').classList.add('hidden');
    document.getElementById('inventory-section').classList.add('hidden');
    
    // Показуємо вибраний розділ
    document.getElementById(`${section}-section`).classList.remove('hidden');
}

const headers = {
    'Content-Type': 'application/json'
};

if (token) {
    headers['Authorization'] = `Bearer ${token}`;
}

// GET request function
async function getAPI(endpoint) {
    try {
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'GET',
            headers
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'GET request error');
        }

        return result;
    } catch (error) {
        console.error('GET API Error:', error);
        throw error;
    }
}

// POST request function
async function postAPI(endpoint, data) {
    try {
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers,
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'POST request error');
        }

        return result;
    } catch (error) {
        console.error('POST API Error:', error);
        throw error;
    }
}


// Авторизація - login
async function login() {
    //get user input
    const login = document.getElementById('login').value;
    const password = document.getElementById('password').value;
    
    if (!login || !password) { // check if user filled out the inputs
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

// Реєстрація
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

// Отримання ремонтів
async function getRepairs() {
    try {
        const data = await getAPI('/repairs');
        showResponse(data);
    } catch (error) {
        showResponse(`Помилка отримання ремонтів: ${error.message}`, true);
    }
}
function addRepairPart() {
    const container = document.getElementById('repair-parts-container');
    const partDiv = document.createElement('div');
    partDiv.className = 'repair-part';
    partDiv.innerHTML = `
        <input class="part-id" placeholder="ID деталі">
        <input class="part-qty" type="number" placeholder="Кількість" min="1" value="1">
    `;
    container.appendChild(partDiv);
}


// Створення ремонту
async function createRepair() {
    const phoneModel = document.getElementById('phone-model').value.trim();
    const issue = document.getElementById('issue').value.trim();

    const partElements = document.querySelectorAll('.repair-part');
    const orders = {};

    partElements.forEach(partEl => {
        const partId = partEl.querySelector('.part-id').value.trim();
        const quantity = parseInt(partEl.querySelector('.part-qty').value.trim(), 10);

        if (partId && quantity && quantity > 0) {
            orders[partId] = quantity;
        }
    });

    if (!phoneModel || !issue) {
        showResponse('Помилка: Заповніть модель телефону та проблему', true);
        return;
    }

    if (Object.keys(orders).length === 0) {
        showResponse('Помилка: Додайте хоча б одну деталь з кількістю', true);
        return;
    }

    try {
        const data = await postAPI('/add_repair', { orders });
        showResponse(data);
    } catch (error) {
        showResponse(`Помилка створення ремонту: ${error.message}`, true);
    }
}

// Отримання замовлень
async function getOrders() {
    try {
        const data = await getAPI('/orders');
        showResponse(data);
    } catch (error) {
        showResponse(`Помилка отримання замовлень: ${error.message}`, true);
    }
}

// Створення замовлення
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

// Отримання компонентів
async function getComponents() {
    try {
        const data = await getAPI('/inventory/components');
        showResponse(data);
    } catch (error) {
        showResponse(`Помилка отримання компонентів: ${error.message}`, true);
    }
}

// Отримання телефонів
async function getPhones() {
    try {
        const data = await getAPI('/inventory/phones');
        showResponse(data);
    } catch (error) {
        showResponse(`Помилка отримання телефонів: ${error.message}`, true);
    }
}

// Виведення відповіді
function showResponse(data, isError = false) {
    const responseElement = document.getElementById('response');
    
    if (isError) {
        responseElement.style.color = 'red';
        responseElement.textContent = data;
    } else {
        responseElement.style.color = 'black';
        if (typeof data === 'object') {
            responseElement.textContent = JSON.stringify(data, null, 2);
        } else {
            responseElement.textContent = data;
        }
    }
}

// Функція для виходу з системи
function logout() {
    token = '';
    localStorage.removeItem('token');
    updateAuthStatus();
    showResponse('Ви вийшли з системи.');
    showSection('auth');
}