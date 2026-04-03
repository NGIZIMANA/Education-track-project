from flask import Flask, request, jsonify
from jsonbin_client import JSONBinClient
import os

app = Flask(__name__)

# =======================
# JSONBIN CONFIG (FIXED)
# =======================
API_KEY = os.environ.get("JSONBIN_API_KEY")
BIN_ID = os.environ.get("JSONBIN_BIN_ID")

jsonbin_client = JSONBinClient(API_KEY, BIN_ID)


# =======================
# HOME
# =======================
@app.route("/")
def home():
    return jsonify({"message": "EduTrack API running 🚀"})


# =======================
# REGISTER
# =======================
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    db = jsonbin_client.read_bin(BIN_ID)

    users = db.get("users", [])
    users.append(data)

    db["users"] = users
    jsonbin_client.update_bin(BIN_ID, db)

    return jsonify({"message": "User registered"})


# =======================
# LOGIN
# =======================
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    db = jsonbin_client.read_bin(BIN_ID)

    users = db.get("users", [])

    for user in users:
        if user["username"] == data["username"] and user["password"] == data["password"]:
            return jsonify({"message": "Login successful", "user": user})

    return jsonify({"message": "Invalid credentials"}), 401


# =======================
# WALLET
# =======================
@app.route("/wallet/<username>")
def wallet(username):
    db = jsonbin_client.read_bin(BIN_ID)
    wallets = db.get("wallets", {})

    return jsonify({"balance": wallets.get(username, 0)})


@app.route("/wallet/add", methods=["POST"])
def add_wallet():
    data = request.json
    db = jsonbin_client.read_bin(BIN_ID)

    wallets = db.get("wallets", {})
    wallets[data["username"]] = wallets.get(data["username"], 0) + data["amount"]

    db["wallets"] = wallets
    jsonbin_client.update_bin(BIN_ID, db)

    return jsonify({"message": "Wallet updated"})


# =======================
# ANALYTICS
# =======================
@app.route("/analytics")
def analytics():
    db = jsonbin_client.read_bin(BIN_ID)

    users = db.get("users", [])
    wallets = db.get("wallets", {})

    total_balance = sum(wallets.values())

    return jsonify({
        "total_users": len(users),
        "total_balance": total_balance
    })


# =======================
# VERCEL COMPATIBILITY
# =======================
application = app
