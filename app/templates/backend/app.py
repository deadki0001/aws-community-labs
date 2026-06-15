from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Temporary in-memory storage
users = {}

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    if username in users:
        return jsonify({"message": "Username already exists"}), 400

    hashed_password = generate_password_hash(password)
    users[username] = hashed_password

    return jsonify({"message": "User registered successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    hashed_password = users.get(username)
    if not hashed_password or not check_password_hash(hashed_password, password):
        return jsonify({"message": "Invalid username or password"}), 401

    return jsonify({"message": f"Welcome back, {username}!"}), 200

if __name__ == '__main__':
    app.run(debug=True)

