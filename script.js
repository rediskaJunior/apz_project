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

// Функція для виконання запитів до API
async function fetchAPI(endpoint, method = 'GET', data = null) {
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const options = {
        method,
        headers
    };
    
    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_URL}${endpoint}`, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Помилка запиту');
        }
        
        return result;
    } catch (error) {
        console.error('Помилка API:', error);
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
        const data = await fetchAPI('/auth/login', 'POST', { login, password });
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
        const data = await fetchAPI('/auth/register', 'POST', { login, password });
        showResponse('Успішно зареєстровано. Тепер можете увійти.');
    } catch (error) {
        showResponse(`Помилка реєстрації: ${error.message}`, true);
    }
}

// Отримання ремонтів
async function getRepairs() {
    try {
        const data = await fetchAPI('/repairs');
        showResponse(data);
    } catch (error) {
        showResponse(`Помилка отримання ремонтів: ${error.message}`, true);
    }
}

// Створення ремонту
async function createRepair() {
    const phoneModel = document.getElementById('phone-model').value;
    const issue = document.getElementById('issue').value;
    
    if (!phoneModel || !issue) {
        showResponse('Помилка: Заповніть всі поля', true);
        return;
    }
    
    try {
        const data = await fetchAPI('/repairs', 'POST', { phoneModel, issue });
        showResponse(data);
    } catch (error) {
        showResponse(`Помилка створення ремонту: ${error.message}`, true);
    }
}

// Отримання замовлень
async function getOrders() {
    try {
        const data = await fetchAPI('/orders');
        showResponse(data);
    } catch (error) {
        showResponse(`Помилка отримання замовлень: ${error.message}`, true);
    }
}

// Створення замовлення
async function createOrder() {
    const component = document.getElementById('component').value;
    const quantity = document.getElementById('quantity').value;
    
    if (!component || !quantity) {
        showResponse('Помилка: Заповніть всі поля', true);
        return;
    }
    
    try {
        const data = await fetchAPI('/orders', 'POST', { component, quantity });
        showResponse(data);
    } catch (error) {
        showResponse(`Помилка створення замовлення: ${error.message}`, true);
    }
}

// Отримання компонентів
async function getComponents() {
    try {
        const data = await fetchAPI('/inventory/components');
        showResponse(data);
    } catch (error) {
        showResponse(`Помилка отримання компонентів: ${error.message}`, true);
    }
}

// Отримання телефонів
async function getPhones() {
    try {
        const data = await fetchAPI('/inventory/phones');
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