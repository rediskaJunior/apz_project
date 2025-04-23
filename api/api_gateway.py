# api_gateway/app.py
from flask import Flask, jsonify, request
import requests
from functools import wraps
from flask_cors import CORS  # Додаємо підтримку CORS

app = Flask(__name__)
CORS(app)  # Дозволяємо CORS для всіх маршрутів

# Конфігурація сервісів
SERVICE_URLS = {
    "auth": "http://localhost:5000",
    "inventory": "http://localhost:5001",
    "repair": "http://localhost:5002",
    "orders": "http://localhost:5003"
}

# Заголовок з токеном
TOKEN_HEADER = "Authorization"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Отримуємо токен з заголовків
        if TOKEN_HEADER in request.headers:
            token = request.headers[TOKEN_HEADER].split(" ")[-1]
        
        if not token:
            return jsonify({"error": "Необхідний токен авторизації"}), 401
        
        # Валідуємо токен через Auth Service
        try:
            response = requests.post(
                f"{SERVICE_URLS['auth']}/validate",
                json={"token": token}
            )
            
            if not response.json().get("valid", False):
                return jsonify({"error": "Недійсний токен авторизації"}), 401
            
            # Додаємо ID користувача до запиту
            request.user_id = response.json().get("user_id")
            
        except Exception as e:
            return jsonify({"error": f"Помилка перевірки токена: {str(e)}"}), 500
        
        return f(*args, **kwargs)
    
    return decorated

# Маршрути аутентифікації (без перевірки токена)
@app.route("/api/auth/login", methods=["POST"])
def login():
    # Отримуємо дані логіну з запиту
    data = request.json or {}
    print(data)
    return proxy_request(SERVICE_URLS["auth"], "/login", data=data)

@app.route("/api/auth/register", methods=["POST"])
def register():
    # Отримуємо дані реєстрації з запиту
    data = request.json or {}
    print(data)
    return proxy_request(SERVICE_URLS["auth"], "/register", data=data)

# Маршрути для роботи з ремонтами
@app.route("/api/repairs", methods=["GET"])
@token_required
def get_repairs():
    # Додаємо user_id як параметр запиту
    params = dict(request.args)
    params["user_id"] = request.user_id
    
    return proxy_request(SERVICE_URLS["repair"], "/repairs", params=params)

@app.route("/api/repairs", methods=["POST"])
@token_required
def create_repair():
    # Додаємо user_id до тіла запиту
    data = request.json or {}
    data["user_id"] = request.user_id
    
    return proxy_request(SERVICE_URLS["repair"], "/repairs", data=data)

@app.route("/api/repairs/<repair_id>", methods=["GET"])
@token_required
def get_repair(repair_id):
    return proxy_request(SERVICE_URLS["repair"], f"/repairs/{repair_id}")

@app.route("/api/repairs/<repair_id>/diagnose", methods=["POST"])
@token_required
def diagnose_repair(repair_id):
    data = request.json or {}
    return proxy_request(SERVICE_URLS["repair"], f"/repairs/{repair_id}/diagnose", data=data)

@app.route("/api/repairs/<repair_id>/complete", methods=["POST"])
@token_required
def complete_repair(repair_id):
    data = request.json or {}
    return proxy_request(SERVICE_URLS["repair"], f"/repairs/{repair_id}/complete", data=data)

@app.route("/api/repairs/<repair_id>/cancel", methods=["POST"])
@token_required
def cancel_repair(repair_id):
    data = request.json or {}
    return proxy_request(SERVICE_URLS["repair"], f"/repairs/{repair_id}/cancel", data=data)

# Маршрути для роботи з замовленнями
@app.route("/api/orders", methods=["GET"])
@token_required
def get_orders():
    # Додаємо user_id як параметр запиту
    params = dict(request.args)
    params["user_id"] = request.user_id
    
    return proxy_request(SERVICE_URLS["orders"], "/orders", params=params)

@app.route("/api/orders", methods=["POST"])
@token_required
def create_order():
    # Додаємо user_id до тіла запиту
    data = request.json or {}
    data["user_id"] = request.user_id
    
    return proxy_request(SERVICE_URLS["orders"], "/orders", data=data)

@app.route("/api/orders/<order_id>", methods=["GET"])
@token_required
def get_order(order_id):
    return proxy_request(SERVICE_URLS["orders"], f"/orders/{order_id}")

@app.route("/api/orders/<order_id>/cancel", methods=["POST"])
@token_required
def cancel_order(order_id):
    data = request.json or {}
    return proxy_request(SERVICE_URLS["orders"], f"/orders/{order_id}/cancel", data=data)

# Маршрути для роботи з інвентарем
@app.route("/api/inventory/components", methods=["GET"])
@token_required
def get_components():
    return proxy_request(SERVICE_URLS["inventory"], "/components")

@app.route("/api/inventory/phones", methods=["GET"])
@token_required
def get_phones():
    return proxy_request(SERVICE_URLS["inventory"], "/phones")

# Функція для перенаправлення запитів до відповідних сервісів
def proxy_request(service_url, endpoint, params=None, data=None):
    url = f"{service_url}{endpoint}"
    
    try:
        # Перенаправляємо всі заголовки, окрім хоста
        headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
        
        # Виконуємо запит з тим же методом, що і оригінальний запит
        response = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            params=params,
            json=data
        )
        print(response.json(), response.status_code)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": f"Помилка при перенаправленні запиту: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, debug=True)