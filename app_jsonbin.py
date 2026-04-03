from flask import Flask, request, jsonify
import requests, os, uuid

app = Flask(__name__)

# JSONBin config
API_KEY = os.getenv("JSONBIN_API_KEY")
BIN_ID = os.getenv("JSONBIN_BIN_ID")

URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"

HEADERS = {
    "X-Master-Key": API_KEY,
    "Content-Type": "application/json"
}

def get_db():
    res = requests.get(URL, headers=HEADERS)
    if res.status_code == 200:
        return res.json().get("record", {})
    return {}

def save_db(data):
    requests.put(URL, headers=HEADERS, json=data)

# ================= HOME =================
@app.route("/")
def home():
    return jsonify({"message": "EduTrack API running 🚀"})

# ================= REGISTER =================
@app.route("/api/register", methods=["POST"])
def register():
    data = request.json
    db = get_db()

    users = db.get("users", [])

    users.append({
        "id": str(uuid.uuid4()),
        "username": data["username"],
        "password": data["password"]
    })

    db["users"] = users
    save_db(db)

    return jsonify({"message": "Registered successfully"})

# ================= LOGIN =================
@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    db = get_db()

    users = db.get("users", [])

    for u in users:
        if u["username"] == data["username"] and u["password"] == data["password"]:
            return jsonify({"message": "Login success", "user": u})

    return jsonify({"message": "Invalid login"}), 401

# ================= DASHBOARD =================
@app.route("/api/dashboard")
def dashboard():
    db = get_db()
    users = db.get("users", [])

    return jsonify({
        "total_users": len(users)
    })

# ================= VERCEL =================
application = app
