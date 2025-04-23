# repair_service/app.py
from flask import Flask, jsonify, request
import requests
import uuid
from datetime import datetime

app = Flask(__name__)

# Імітація БД ремонтів
repairs = {}

# Статуси ремонтів
REPAIR_STATUSES = {
    "PENDING": "In waiting",
    "DIAGNOSIS": "Under diagnostic",
    "WAITING_PARTS": "Waiting for parts",
    "IN_PROGRESS": "In progress",
    "COMPLETED": "Completed",
    "CANCELLED": "Cancelled"
}

# Конфігурація сервісів
INVENTORY_SERVICE_URL = "http://localhost:5001"  # URL сервісу інвентаризації


#function ot create a repair request/note
@app.route("/repairs", methods=["POST"])
def create_repair():
    #CHANGE FOR DRONES
    data = request.json
    user_id = data.get("user_id")
    phone_model = data.get("phone_model")
    description = data.get("description")
    
    
    # Створюємо запис про ремонт
    repair_id = str(uuid.uuid4())
    repair = {
        "id": repair_id,
        "user_id": user_id,
        "phone_model": phone_model,
        "description": description,
        "status": "PENDING",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "estimated_parts": [],
        "repair_history": [
            {
                "status": "PENDING",
                "timestamp": datetime.now().isoformat(),
                "note": "Заявка на ремонт створена"
            }
        ]
    }
    
    # Збереження в "БД"
    repairs[repair_id] = repair
    
    return jsonify(repair)

#get repair status
@app.route("/repairs/<repair_id>", methods=["GET"])
def get_repair(repair_id):
    if repair_id not in repairs:
        return jsonify({"error": "Ремонт не знайдено"}), 404
    
    return jsonify(repairs[repair_id])

@app.route("/repairs/<repair_id>/diagnose", methods=["POST"])
def diagnose_repair(repair_id):
    if repair_id not in repairs:
        return jsonify({"error": "Ремонт не знайдено"}), 404
    
    data = request.json
    required_parts = data.get("required_parts", [])
    diagnosis = data.get("diagnosis", "")
    
    # Оновлюємо статус ремонту
    repairs[repair_id]["status"] = "DIAGNOSIS"
    repairs[repair_id]["diagnosis"] = diagnosis
    repairs[repair_id]["estimated_parts"] = required_parts
    repairs[repair_id]["updated_at"] = datetime.now().isoformat()
    
    # Додаємо запис в історію
    repairs[repair_id]["repair_history"].append({
        "status": "DIAGNOSIS",
        "timestamp": datetime.now().isoformat(),
        "note": "Діагностика проведена"
    })
    
    # Перевіряємо наявність запчастин в інвентарі
    if required_parts:
        try:
            # Виклик Inventory Service для резервування запчастин
            response = requests.post(
                f"{INVENTORY_SERVICE_URL}/reserve",
                json={
                    "order_id": f"repair_{repair_id}",
                    "components": [{"id": p["component_id"], "quantity": p["quantity"]} for p in required_parts]
                }
            )
            
            reservation_result = response.json()
            
            if reservation_result["success"]:
                # Всі запчастини в наявності
                repairs[repair_id]["status"] = "IN_PROGRESS"
                repairs[repair_id]["repair_history"].append({
                    "status": "IN_PROGRESS",
                    "timestamp": datetime.now().isoformat(),
                    "note": "Запчастини зарезервовано, ремонт розпочато"
                })
            else:
                # Деякі запчастини відсутні, необхідно замовити
                repairs[repair_id]["status"] = "WAITING_PARTS"
                repairs[repair_id]["missing_parts"] = reservation_result["missing_items"]
                repairs[repair_id]["repair_history"].append({
                    "status": "WAITING_PARTS",
                    "timestamp": datetime.now().isoformat(),
                    "note": "Очікуємо надходження відсутніх запчастин"
                })
                
                # Тут би мав бути запит до Parts Order Service для замовлення відсутніх запчастин
        
        except Exception as e:
            # Помилка комунікації з сервісом інвентаризації
            repairs[repair_id]["status"] = "PENDING"
            repairs[repair_id]["repair_history"].append({
                "status": "PENDING",
                "timestamp": datetime.now().isoformat(),
                "note": f"Помилка перевірки запчастин: {str(e)}"
            })
    
    return jsonify(repairs[repair_id])

#change status of repair to complete
@app.route("/repairs/<repair_id>/complete", methods=["POST"])
def complete_repair(repair_id):
    if repair_id not in repairs:
        return jsonify({"error": "Ремонт не знайдено"}), 404
    
    # Оновлюємо статус ремонту
    repairs[repair_id]["status"] = "COMPLETED"
    repairs[repair_id]["updated_at"] = datetime.now().isoformat()
    repairs[repair_id]["completed_at"] = datetime.now().isoformat()
    
    # Додаємо запис в історію
    repairs[repair_id]["repair_history"].append({
        "status": "COMPLETED",
        "timestamp": datetime.now().isoformat(),
        "note": "Ремонт завершено"
    })
    
    return jsonify(repairs[repair_id])

#cancel repair
@app.route("/repairs/<repair_id>/cancel", methods=["POST"])
def cancel_repair(repair_id):
    if repair_id not in repairs:
        return jsonify({"error": "Ремонт не знайдено"}), 404
    
    # Оновлюємо статус ремонту
    repairs[repair_id]["status"] = "CANCELLED"
    repairs[repair_id]["updated_at"] = datetime.now().isoformat()
    
    # Додаємо запис в історію
    repairs[repair_id]["repair_history"].append({
        "status": "CANCELLED",
        "timestamp": datetime.now().isoformat(),
        "note": "Ремонт скасовано"
    })
    
    # Звільняємо зарезервовані запчастини
    try:
        requests.post(
            f"{INVENTORY_SERVICE_URL}/release",
            json={"order_id": f"repair_{repair_id}"}
        )
    except Exception:
        # Ігноруємо помилки комунікації з сервісом інвентаризації
        pass
    
    return jsonify(repairs[repair_id])

#get all user repairs
@app.route("/repairs", methods=["GET"])
def get_repairs():
    user_id = request.args.get("user_id")
    status = request.args.get("status")
    
    result = []
    for repair in repairs.values():
        # Фільтруємо за ID користувача, якщо вказано
        if user_id and str(repair["user_id"]) != user_id:
            continue
        
        # Фільтруємо за статусом, якщо вказано
        if status and repair["status"] != status:
            continue
        
        result.append(repair)
    
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, port=5002)