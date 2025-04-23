# inventory_service/app.py
from flask import Flask, jsonify, request

app = Flask(__name__)

# Імітація інвентарю в пам'яті
inventory = {
    "components": {
        1: {"id": 1, "name": "Екран iPhone 12", "quantity": 15, "type": "display"},
        2: {"id": 2, "name": "Батарея Samsung S21", "quantity": 20, "type": "battery"},
        3: {"id": 3, "name": "Корпус Xiaomi Mi 11", "quantity": 8, "type": "case"},
        4: {"id": 4, "name": "Камера iPhone 13", "quantity": 10, "type": "camera"}
    },
    "phones": {
        1: {"id": 1, "name": "iPhone 13", "quantity": 5, "price": 30000},
        2: {"id": 2, "name": "Samsung S21", "quantity": 3, "price": 25000},
        3: {"id": 3, "name": "Xiaomi Mi 11", "quantity": 7, "price": 20000}
    }
}

# Історія резервувань
reserved_items = {}

#function to get all components
@app.route("/components", methods=["GET"])
def get_components():
    return jsonify(list(inventory["components"].values()))

#function to get component by id
@app.route("/components/<int:component_id>", methods=["GET"])
def get_component(component_id):
    component = inventory["components"].get(component_id)
    if not component:
        return jsonify({"error": "Component not found"}), 404
    return jsonify(component)

#get all phones
@app.route("/phones", methods=["GET"])
def get_phones():
    return jsonify(list(inventory["phones"].values()))

#get a specific phone item
@app.route("/phones/<int:phone_id>", methods=["GET"])
def get_phone(phone_id):
    phone = inventory["phones"].get(phone_id)
    if not phone:
        return jsonify({"error": "Телефон не знайдено"}), 404
    return jsonify(phone)

#reserve an item that is ordered
@app.route("/reserve", methods=["POST"])
def reserve_parts():
    # Ендпоінт для резервування частин (для ремонту або замовлення)
    data = request.json
    order_id = data.get("order_id")
    components = data.get("components", [])
    phones = data.get("phones", [])
    
    missing_items = []
    reserved = {"components": [], "phones": []}

    #CHANGE TO DRONE PARTS AND ETC
    
    # Перевірка наявності компонентів
    for comp in components:
        comp_id = comp.get("id")
        quantity = comp.get("quantity", 1)
        
        if comp_id in inventory["components"]:
            if inventory["components"][comp_id]["quantity"] >= quantity:
                # Резервуємо компонент
                inventory["components"][comp_id]["quantity"] -= quantity
                reserved["components"].append({
                    "id": comp_id,
                    "quantity": quantity
                })
            else:
                missing_items.append({
                    "type": "component",
                    "id": comp_id,
                    "requested": quantity,
                    "available": inventory["components"][comp_id]["quantity"]
                })
        else:
            missing_items.append({
                "type": "component",
                "id": comp_id,
                "requested": quantity,
                "available": 0
            })
    
    # Перевірка наявності телефонів
    for phone in phones:
        phone_id = phone.get("id")
        quantity = phone.get("quantity", 1)
        
        if phone_id in inventory["phones"]:
            if inventory["phones"][phone_id]["quantity"] >= quantity:
                # Резервуємо телефон
                inventory["phones"][phone_id]["quantity"] -= quantity
                reserved["phones"].append({
                    "id": phone_id,
                    "quantity": quantity
                })
            else:
                missing_items.append({
                    "type": "phone",
                    "id": phone_id,
                    "requested": quantity,
                    "available": inventory["phones"][phone_id]["quantity"]
                })
        else:
            missing_items.append({
                "type": "phone",
                "id": phone_id,
                "requested": quantity,
                "available": 0
            })
    
    # Зберігаємо резервування
    if order_id:
        reserved_items[order_id] = reserved
    
    return jsonify({
        "success": len(missing_items) == 0,
        "reserved": reserved,
        "missing_items": missing_items,
        "order_id": order_id
    })

#function to cancel the reservation
@app.route("/release", methods=["POST"])
def release_reservation():
    # Відміна резервування (якщо замовлення скасовано)
    data = request.json
    order_id = data.get("order_id")
    
    if order_id not in reserved_items:
        return jsonify({"error": "Резервування не знайдено"}), 404
    
    # Повертаємо компоненти в інвентар
    for comp in reserved_items[order_id]["components"]:
        inventory["components"][comp["id"]]["quantity"] += comp["quantity"]
    
    # Повертаємо телефони в інвентар
    for phone in reserved_items[order_id]["phones"]:
        inventory["phones"][phone["id"]]["quantity"] += phone["quantity"]
    
    # Видаляємо резервування
    del reserved_items[order_id]
    
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True, port=5001)