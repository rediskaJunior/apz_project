from flask import Flask, jsonify, request

app = Flask(__name__)

users = {
    "user1@example.com": {"password": "password1", "id": 1, "name": "Користувач 1"},
    "user2@example.com": {"password": "password2", "id": 2, "name": "Користувач 2"},
}

#login already registered user
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("login")
    password = data.get("password")

    if email in users and users[email]["password"] == password:
        return jsonify({
            "token": f"fake_token_{users[email]['id']}",
            "user_id": users[email]['id'],
            "name": users[email]['name']
        })
    
    return jsonify({"Error" : "Incorrect login or password"}), 401

#check if token is ok
@app.route("/validate", methods=["POST"])
def validate_token():
    # Ендпоінт для валідації токена, який використовуватимуть інші сервіси
    token = request.json.get("token", "")
    
    # Спрощена перевірка токена (в реальності - перевірка JWT)
    if token and token.startswith("fake_token_"):
        user_id = int(token.split("_")[-1])
        return jsonify({"valid": True, "user_id": user_id})
    
    return jsonify({"valid": False}), 401

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    email = data.get("login")

    if email in users:
        return jsonify({"error": "The user already exists"}), 400
    

    #here we should change to saving users in a database
    user_id = len (users) + 1
    users[email] = {
        "password": data.get("password"),
        "id": user_id,
        "name": data.get("name")
    }

    return jsonify({
        "id": user_id,
        "email": email,
        "name": data.get("name")
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)