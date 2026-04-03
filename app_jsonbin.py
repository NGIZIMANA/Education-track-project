from flask import Flask, request, jsonify, redirect, session
import requests, os, uuid

app = Flask(__name__)
app.secret_key = "secret123"

# ================= JSONBIN CONFIG =================
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
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    db = get_db()

    students = db.get("students", [])

    student = {
        "id": str(uuid.uuid4()),
        "username": data["username"],
        "password": data["password"]
    }

    students.append(student)
    db["students"] = students
    save_db(db)

    return jsonify({"message": "Registered successfully"})

# ================= LOGIN =================
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    db = get_db()

    students = db.get("students", [])

    for s in students:
        if s["username"] == data["username"] and s["password"] == data["password"]:
            return jsonify({"message": "Login success", "user": s})

    return jsonify({"message": "Invalid login"}), 401

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    db = get_db()
    students = db.get("students", [])
    return jsonify({
        "total_students": len(students)
    })

# ================= VERCEL =================
application = app
