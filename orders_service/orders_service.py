# orders_service/app.py
from flask import Flask, jsonify, request
import requests
import uuid
from datetime import datetime

app = Flask(__name__)

# Імітація БД замовлень
orders = {}

# Статуси замовлень
ORDER_STATUSES = {
    "PENDING": "Очікує обробки",
    "PROCESSING": "В обробці",
    "WAITING_PARTS": "Очікує запчастини",
    "SHIPPED": "Відправлено",
    "DELIVERED": "Доставлено",
    "CANCELLED": "Скасовано"
}

# Конфігурація сервісів
INVENTORY_SERVICE_URL = "http://localhost:5001"  # URL сервісу інвентаризації

@app.route("/orders", methods=["POST"])
def create_order():
    data = request.json
    user_id = data.get("user_id")
    items = data.get("items", [])  # Список телефонів/компонентів для замовлення
    shipping_address = data.get("shipping_address", {})
    
    # Створюємо запис про замовлення
    order_id = str(uuid.uuid4())
    order = {
        "id": order_id,
        "user_id": user_id,
        "items": items,
        "shipping_address": shipping_address,
        "status": "PENDING",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "total_price": calculate_total_price(items),
        "order_history": [
            {
                "status": "PENDING",
                "timestamp": datetime.now().isoformat(),
                "note": "Замовлення створено"
            }
        ]
    }
    
    # Збереження в "БД"
    orders[order_id] = order
    
    # Перевіряємо наявність товарів в інвентарі
    try:
        # Розділяємо замовлення на телефони та компоненти
        phones = [item for item in items if item.get("type") == "phone"]
        components = [item for item in items if item.get("type") == "component"]
        
        # Виклик Inventory Service для резервування товарів
        response = requests.post(
            f"{INVENTORY_SERVICE_URL}/reserve",
            json={
                "order_id": order_id,
                "phones": [{"id": p["item_id"], "quantity": p["quantity"]} for p in phones],
                "components": [{"id": c["item_id"], "quantity": c["quantity"]} for c in components]
            }
        )
        
        reservation_result = response.json()
        
        if reservation_result["success"]:
            # Всі товари в наявності
            orders[order_id]["status"] = "PROCESSING"
            orders[order_id]["order_history"].append({
                "status": "PROCESSING",
                "timestamp": datetime.now().isoformat(),
                "note": "Товари зарезервовано, замовлення в обробці"
            })
        else:
            # Деякі товари відсутні, необхідно замовити
            orders[order_id]["status"] = "WAITING_PARTS"
            orders[order_id]["missing_items"] = reservation_result["missing_items"]
            orders[order_id]["order_history"].append({
                "status": "WAITING_PARTS",
                "timestamp": datetime.now().isoformat(),
                "note": "Очікуємо надходження відсутніх товарів"
            })
    
    except Exception as e:
        # Помилка комунікації з сервісом інвентаризації
        orders[order_id]["order_history"].append({
            "status": "PENDING",
            "timestamp": datetime.now().isoformat(),
            "note": f"Помилка перевірки наявності: {str(e)}"
        })
    
    return jsonify(orders[order_id])

@app.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    if order_id not in orders:
        return jsonify({"error": "Замовлення не знайдено"}), 404
    
    return jsonify(orders[order_id])

@app.route("/orders/<order_id>/cancel", methods=["POST"])
def cancel_order(order_id):
    if order_id not in orders:
        return jsonify({"error": "Замовлення не знайдено"}), 404
    
    # Перевіряємо, чи можна скасувати замовлення
    current_status = orders[order_id]["status"]
    if current_status in ["SHIPPED", "DELIVERED"]:
        return jsonify({
            "error": "Неможливо скасувати замовлення в статусі " + ORDER_STATUSES[current_status]
        }), 400
    
    # Оновлюємо статус замовлення
    orders[order_id]["status"] = "CANCELLED"
    orders[order_id]["updated_at"] = datetime.now().isoformat()
    
    # Додаємо запис в історію
    orders[order_id]["order_history"].append({
        "status": "CANCELLED",
        "timestamp": datetime.now().isoformat(),
        "note": "Замовлення скасовано"
    })
    
    # Звільняємо зарезервовані товари
    try:
        requests.post(
            f"{INVENTORY_SERVICE_URL}/release",
            json={"order_id": order_id}
        )
    except Exception:
        # Ігноруємо помилки комунікації з сервісом інвентаризації
        pass
    
    return jsonify(orders[order_id])

@app.route("/orders/<order_id>/status", methods=["PUT"])
def update_order_status(order_id):
    if order_id not in orders:
        return jsonify({"error": "Замовлення не знайдено"}), 404
    
    data = request.json
    new_status = data.get("status")
    note = data.get("note", "")
    
    # Перевіряємо, чи існує такий статус
    if new_status not in ORDER_STATUSES:
        return jsonify({"error": "Недійсний статус замовлення"}), 400
    
    # Оновлюємо статус замовлення
    orders[order_id]["status"] = new_status
    orders[order_id]["updated_at"] = datetime.now().isoformat()
    
    # Додаємо запис в історію
    orders[order_id]["order_history"].append({
        "status": new_status,
        "timestamp": datetime.now().isoformat(),
        "note": note or f"Статус змінено на {ORDER_STATUSES[new_status]}"
    })
    
    return jsonify(orders[order_id])

@app.route("/orders", methods=["GET"])
def get_orders():
    user_id = request.args.get("user_id")
    status = request.args.get("status")
    
    result = []
    for order in orders.values():
        # Фільтруємо за ID користувача, якщо вказано
        if user_id and str(order["user_id"]) != user_id:
            continue
        
        # Фільтруємо за статусом, якщо вказано
        if status and order["status"] != status:
            continue
        
        result.append(order)
    
    return jsonify(result)

def calculate_total_price(items):
    # У реальній системі тут був би запит до бази даних або сервісу цін
    # Для спрощення, повертаємо заглушку
    return sum(item.get("price", 0) * item.get("quantity", 1) for item in items)

if __name__ == "__main__":
    app.run(debug=True, port=5003)