
import os
import json
import uuid
from datetime import date, datetime
import random
import base64
import re
import requests
from flask import Flask, render_template_string, request, redirect, session, Response, make_response, jsonify
from jsonbin_client import JSONBinClient

# Initialize JSONBin client
jsonbin_client = JSONBinClient()

# --- Data Storage Structure in JSONBin.io ---
# We will use a single JSON bin to store all application data.
# The structure will be a dictionary where keys are entity names (e.g., 'students', 'cats')
# and values are lists of dictionaries representing the records.
# Example:
# {
#   "student_options": [],
#   "students": [],
#   "attendances": [],
#   "cats": [],
#   "questions": [],
#   "cat_results": [],
#   "cat_sessions": []
# }

# --- Helper functions for data access ---
BIN_ID = os.environ.get("JSONBIN_BIN_ID") # This will be set after initial creation

def _get_all_data():
    if not BIN_ID:
        return {
            "student_options": [],
            "students": [],
            "attendances": [],
            "cats": [],
            "questions": [],
            "cat_results": [],
            "cat_sessions": []
        }
    try:
        return jsonbin_client.read_bin(BIN_ID)
    except requests.exceptions.RequestException as e:
        print(f"Error reading from JSONBin: {e}")
        # If bin doesn't exist or error, return empty structure
        return {
            "student_options": [],
            "students": [],
            "attendances": [],
            "cats": [],
            "questions": [],
            "cat_results": [],
            "cat_sessions": []
        }

def _save_all_data(data):
    global BIN_ID
    if not BIN_ID:
        # Initial creation of the bin
        metadata = jsonbin_client.create_bin(data, bin_name="EduTrackData", private=True)
        BIN_ID = metadata["id"]
        os.environ["JSONBIN_BIN_ID"] = BIN_ID # Store for subsequent calls
        print(f"Created new JSONBin with ID: {BIN_ID}")
    else:
        jsonbin_client.update_bin(BIN_ID, data)

def _find_by_id(data_list, item_id):
    return next((item for item in data_list if item['id'] == item_id), None)

def _filter_data(data_list, **kwargs):
    results = []
    for item in data_list:
        match = True
        for key, value in kwargs.items():
            if item.get(key) != value:
                match = False
                break
        if match:
            results.append(item)
    return results

def _delete_by_id(data_list, item_id):
    original_len = len(data_list)
    data_list[:] = [item for item in data_list if item['id'] != item_id]
    return original_len > len(data_list)

# --- Flask App Setup ---
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey") # Use environment variable for secret key

# ==================== MODELS (Represented as dictionaries) ====================
# We will simulate SQLAlchemy models with dictionaries and manage relationships manually.
# Each 'model' will have an 'id' field, which will be a UUID.

# ==================== DESIGN SYSTEM (Copied from original) ====================
BASE_STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #080c14;
  --surface: #0d1420;
  --surface2: #111827;
  --border: rgba(99,179,237,0.12);
  --border-hover: rgba(99,179,237,0.28);
  --accent: #38bdf8;
  --accent2: #818cf8;
  --accent3: #34d399;
  --text: #f0f6ff;
  --muted: #64748b;
  --muted2: #94a3b8;
  --danger: #f87171;
  --warning: #fbbf24;
  --success: #34d399;
  --radius: 14px;
  --radius-sm: 9px;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:\'Outfit\',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;line-height:1.6}
body::before{content:\'\';position:fixed;inset:0;background:radial-gradient(ellipse 80% 50% at 50% -20%,rgba(56,189,248,0.06),transparent),radial-gradient(ellipse 60% 40% at 80% 80%,rgba(129,140,248,0.05),transparent);pointer-events:none;z-index:0}

.topbar{background:rgba(13,20,32,0.85);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);padding:0 32px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;height:64px}
.topbar-brand{font-family:\'Space Mono\',monospace;font-size:17px;font-weight:700;color:var(--accent);letter-spacing:-0.5px;display:flex;align-items:center;gap:10px}
.brand-dot{width:8px;height:8px;background:var(--accent);border-radius:50%;animation:pulse 2s ease-in-out infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(56,189,248,0.4)}50%{box-shadow:0 0 0 6px rgba(56,189,248,0)}}
.topbar-nav{display:flex;align-items:center;gap:4px}
.topbar-nav a{color:var(--muted2);text-decoration:none;font-size:13.5px;font-weight:500;padding:7px 14px;border-radius:var(--radius-sm);transition:all .2s;letter-spacing:0.2px}
.topbar-nav a:hover{color:var(--text);background:rgba(255,255,255,0.06)}
.topbar-nav .active{color:var(--accent);background:rgba(56,189,248,0.08)}
.btn-logout{background:rgba(248,113,113,0.1)!important;color:var(--danger)!important;border:1px solid rgba(248,113,113,0.2)!important}
.btn-logout:hover{background:rgba(248,113,113,0.2)!important}

.container{max-width:1280px;margin:0 auto;padding:36px 28px;position:relative;z-index:1}
.page-header{margin-bottom:32px}
.page-title{font-size:28px;font-weight:700;color:var(--text);letter-spacing:-0.5px;margin-bottom:5px}
.page-sub{color:var(--muted);font-size:14px}

.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.grid-4{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}

.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:24px;position:relative;overflow:hidden;transition:border-color .2s}
.card:hover{border-color:var(--border-hover)}
.card::before{content:\'\';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(56,189,248,0.3),transparent);opacity:0;transition:opacity .3s}
.card:hover::before{opacity:1}
.card-title{font-size:14px;font-weight:600;color:var(--muted2);text-transform:uppercase;letter-spacing:1px;margin-bottom:18px;padding-bottom:14px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:8px}
.card-icon{font-size:16px}

.stat-card{background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);padding:22px 24px;position:relative;overflow:hidden}
.stat-card::after{content:\'\';position:absolute;bottom:0;left:0;right:0;height:2px;background:linear-gradient(135deg,var(--accent),var(--accent2))}
.stat-num{font-family:\'Space Mono\',monospace;font-size:34px;font-weight:700;color:var(--accent);line-height:1}
.stat-label{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-top:6px}
.stat-icon{position:absolute;top:20px;right:20px;font-size:24px;opacity:0.15}

label{display:block;font-size:12px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:0.8px;margin-bottom:7px;margin-top:16px}
label:first-child{margin-top:0}
input[type=text],input[type=password],input[type=date],input[type=number],select,textarea{
  width:100%;background:rgba(0,0,0,0.3);border:1px solid var(--border);border-radius:var(--radius-sm);
  padding:11px 15px;color:var(--text);font-size:14px;font-family:\'Outfit\',sans-serif;
  outline:none;transition:all .2s;-webkit-appearance:none}
input:focus,select:focus,textarea:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(56,189,248,0.1)}
select option{background:var(--surface2)}
textarea{resize:vertical;min-height:80px}
input[type=checkbox]{width:18px;height:18px;accent-color:var(--accent);cursor:pointer}

.btn{display:inline-flex;align-items:center;gap:8px;padding:10px 20px;border:none;border-radius:var(--radius-sm);
  font-size:13.5px;font-weight:600;cursor:pointer;text-decoration:none;transition:all .2s;font-family:\'Outfit\',sans-serif;letter-spacing:0.3px;position:relative;overflow:hidden}
.btn::after{content:\'\';position:absolute;inset:0;background:rgba(255,255,255,0);transition:background .2s}
.btn:hover::after{background:rgba(255,255,255,0.06)}
.btn-primary{background:linear-gradient(135deg,#38bdf8,#0ea5e9);color:#0a1628}
.btn-primary:hover{box-shadow:0 4px 20px rgba(56,189,248,0.35);transform:translateY(-1px)}
.btn-danger{background:rgba(248,113,113,0.12);color:var(--danger);border:1px solid rgba(248,113,113,0.25)}
.btn-danger:hover{background:rgba(248,113,113,0.22)}
.btn-success{background:linear-gradient(135deg,#34d399,#10b981);color:#052e16}
.btn-success:hover{box-shadow:0 4px 20px rgba(52,211,153,0.3);transform:translateY(-1px)}
.btn-ghost{background:rgba(255,255,255,0.04);color:var(--muted2);border:1px solid var(--border)}
.btn-ghost:hover{background:rgba(255,255,255,0.08);color:var(--text);border-color:var(--border-hover)}
.btn-indigo{background:rgba(129,140,248,0.12);color:var(--accent2);border:1px solid rgba(129,140,248,0.25)}
.btn-indigo:hover{background:rgba(129,140,248,0.22)}
.btn-warn{background:rgba(251,191,36,0.1);color:var(--warning);border:1px solid rgba(251,191,36,0.25)}
.btn-sm{padding:6px 13px;font-size:12px;border-radius:7px}
.btn:active{transform:scale(0.97)}

.table-wrap{overflow-x:auto;border-radius:var(--radius-sm)}
table{width:100%;border-collapse:collapse}
thead{background:rgba(0,0,0,0.3)}
th{padding:11px 16px;text-align:left;font-size:11px;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:0.8px;border-bottom:1px solid var(--border);white-space:nowrap}
td{padding:13px 16px;font-size:13.5px;color:var(--muted2);border-bottom:1px solid rgba(99,179,237,0.05)}
tr:last-child td{border-bottom:none}
tbody tr{transition:background .15s}
tbody tr:hover td{background:rgba(56,189,248,0.02)}

.badge{display:inline-flex;align-items:center;padding:4px 9px;border-radius:6px;font-size:11px;font-weight:500;letter-spacing:0.3px}
.badge-indigo{background:rgba(129,140,248,0.15);color:var(--accent2)}
.badge-blue{background:rgba(56,189,248,0.15);color:var(--accent)}
.badge-danger{background:rgba(248,113,113,0.15);color:var(--danger)}
.badge-success{background:rgba(52,211,153,0.15);color:var(--success)}
.badge-present{background:rgba(52,211,153,0.15);color:var(--success)}
.badge-absent{background:rgba(248,113,113,0.15);color:var(--danger)}

.alert{padding:14px 20px;border-radius:var(--radius-sm);font-size:14px;display:flex;align-items:center;gap:10px;margin-bottom:16px}
.alert-error{background:rgba(248,113,113,0.15);color:var(--danger);border:1px solid rgba(248,113,113,0.25)}
.alert-success{background:rgba(52,211,153,0.15);color:var(--success);border:1px solid rgba(52,211,153,0.25)}
.alert-info{background:rgba(56,189,248,0.15);color:var(--accent);border:1px solid rgba(56,189,248,0.25)}

.auth-wrap{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px}
.auth-box{width:100%;max-width:400px}
.auth-logo{text-align:center;margin-bottom:28px}
.auth-logo-text{font-family:\'Space Mono\',monospace;font-size:28px;font-weight:700;color:var(--accent);letter-spacing:-0.5px;margin-bottom:5px}
.auth-logo-sub{color:var(--muted);font-size:14px}
.otp-input{font-family:\'Space Mono\',monospace!important;font-size:22px!important;text-align:center;letter-spacing:3px}

.exam-topbar{background:rgba(13,20,32,0.85);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);padding:0 32px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;height:64px}
.exam-brand{font-family:\'Space Mono\',monospace;font-size:17px;font-weight:700;color:var(--danger);letter-spacing:-0.5px;display:flex;align-items:center;gap:10px}
.exam-timer{font-family:\'Space Mono\',monospace;font-size:18px;font-weight:700;color:var(--warning);background:rgba(251,191,36,0.1);padding:6px 12px;border-radius:var(--radius-sm)}

.question-card{background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);padding:24px;margin-bottom:16px}
.q-num{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px}
.q-text{font-size:17px;font-weight:500;color:var(--text);margin-bottom:18px;line-height:1.5}
.option-btn{display:flex;align-items:center;width:100%;text-align:left;padding:12px 16px;margin-bottom:8px;background:rgba(0,0,0,0.2);border:1px solid var(--border);border-radius:var(--radius-sm);color:var(--text);font-size:15px;cursor:pointer;transition:all .2s}
.option-btn:hover{background:rgba(0,0,0,0.4);border-color:var(--accent)}
.option-btn.selected{background:var(--accent);color:#0a1628;border-color:var(--accent)}
.option-btn.selected strong{color:#0a1628}
.option-btn.correct{background:var(--success);color:#0a1628;border-color:var(--success)}
.option-btn.correct strong{color:#0a1628}
.option-btn.wrong{background:var(--danger);color:#0a1628;border-color:var(--danger)}
.option-btn.wrong strong{color:#0a1628}

.face-status{font-size:12px;color:var(--muted2);margin-top:8px;text-align:center}

.tag{display:inline-flex;align-items:center;gap:6px;background:rgba(129,140,248,0.15);color:var(--accent2);padding:5px 10px;border-radius:6px;font-size:12px}
.tag button{background:none;border:none;color:var(--accent2);font-size:14px;cursor:pointer}

.flex-right{display:flex;justify-content:flex-end}
.text-center{text-align:center}
</style>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">"""

Q_BLOCK_STYLE = """
<style>
.question-block{background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);padding:24px;margin-bottom:16px}
.question-block .q-num{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px}
.question-block .q-text{font-size:17px;font-weight:500;color:var(--text);margin-bottom:18px;line-height:1.5}
</style>"""

def page(body_content, role=None, active=None, extra_style=""):
    topbar_nav = ""
    if role == "admin":
        topbar_nav = f"""
        <div class="topbar-nav">
          <a href="/dashboard" class="{'active' if active == 'Dashboard' else ''}">&#128200; Dashboard</a>
          <a href="/mark_attendance" class="{'active' if active == 'Attendance' else ''}">&#128197; Attendance</a>
          <a href="/admin_cats" class="{'active' if active == 'Assessments' else ''}">&#128196; Assessments</a>
          <a href="/reports" class="{'active' if active == 'Reports' else ''}">&#128202; Reports</a>
          <a href="/logout" class="btn-logout">&#10162; Logout</a>
        </div>"""
    elif role == "student":
        topbar_nav = f"""
        <div class="topbar-nav">
          <a href="/student_home" class="{'active' if active == 'Home' else ''}">&#127968; Home</a>
          <a href="/ai" class="{'active' if active == 'AI' else ''}">&#129504; AI Tutor</a>
          <a href="/logout" class="btn-logout">&#10162; Logout</a>
        </div>"""

    return render_template_string(f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EduTrack</title>
    {BASE_STYLE}
    {extra_style}
</head>
<body>
    <div class="topbar">
        <div class="topbar-brand"><span class="brand-dot"></span> EduTrack</div>
        {topbar_nav}
    </div>
    {body_content}
</body>
</html>
""")

# ==================== AUTHENTICATION ====================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        data = _get_all_data()

        if role == "admin":
            # For simplicity, hardcode admin credentials or store in env vars
            ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
            ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "adminpass")
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                session["role"] = "admin"
                session["username"] = username
                return redirect("/dashboard")
            else:
                error = "Invalid admin credentials."
        elif role == "student":
            student = next((s for s in data["students"] if s["reg_no"] == username and s["first_name"].lower() == password.lower()), None)
            if student:
                session["role"] = "student"
                session["student_id"] = student['id']
                session["username"] = student['first_name'] + " " + student['last_name']
                return redirect("/student_home")
            else:
                error = "Invalid student credentials or registration number."
        else:
            error = "Invalid role selected."

        return page(f"""
        <div class="auth-wrap"><div class="auth-box">
          <div class="auth-logo"><div class="auth-logo-text">&#128200; EduTrack</div><div class="auth-logo-sub">Login to your account</div></div>
          <div class="card">
            <div class="card-title">Login</div>
            <div class="alert alert-error">&#9888;&nbsp; {error}</div>
            <form method="post">
              <label>Username / Reg No</label>
              <input type="text" name="username" placeholder="Enter your username or registration number" required>
              <label>Password / First Name</label>
              <input type="password" name="password" placeholder="Enter your password or first name" required>
              <label>Role</label>
              <select name="role">
                <option value="admin">Admin</option>
                <option value="student">Student</option>
              </select>
              <div style="margin-top:22px"><button class="btn btn-primary" style="width:100%;justify-content:center;padding:13px">&#10162; Login</button></div>
            </form>
          </div>
        </div></div>"""
        )

    return page("""
    <div class="auth-wrap"><div class="auth-box">
      <div class="auth-logo"><div class="auth-logo-text">&#128200; EduTrack</div><div class="auth-logo-sub">Login to your account</div></div>
      <div class="card">
        <div class="card-title">Login</div>
        <form method="post">
          <label>Username / Reg No</label>
          <input type="text" name="username" placeholder="Enter your username or registration number" required>
          <label>Password / First Name</label>
          <input type="password" name="password" placeholder="Enter your password or first name" required>
          <label>Role</label>
          <select name="role">
            <option value="admin">Admin</option>
            <option value="student">Student</option>
          </select>
          <div style="margin-top:22px"><button class="btn btn-primary" style="width:100%;justify-content:center;padding:13px">&#10162; Login</button></div>
        </form>
      </div>
    </div></div>"""
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/")
def index():
    return redirect("/login")

# ==================== STUDENT ROUTES ====================
@app.route("/student_home")
def student_home():
    if session.get("role") != "student":
        return redirect("/login")
    
    data = _get_all_data()
    student_id = session.get("student_id")
    student = _find_by_id(data['students'], student_id)
    if not student:
        return redirect("/login")

    student_option = _find_by_id(data["student_options"], student["option_id"])
    student['option_name'] = student_option['name'] if student_option else 'N/A'

    today = date.today()
    # Check if attendance is already marked for today
    attendance_today = next((att for att in data['attendances'] if att['student_id'] == student_id and date.fromisoformat(att['date']) == today), None)
    attendance_marked = attendance_today is not None

    # Get all CATs
    cats = data['cats']
    # Get results for the student
    student_results = _filter_data(data['cat_results'], student_id=student_id)
    completed_cat_ids = {res['cat_id'] for res in student_results}

    available_cats = []
    for cat in cats:
        cat_copy = cat.copy()
        cat_copy['status'] = 'Completed' if cat['id'] in completed_cat_ids else 'Pending'
        available_cats.append(cat_copy)

    body = f"""
    <div class="container">
      <div class="page-header"><div class="page-title">Welcome, {student['first_name']}</div><div class="page-sub">Your student dashboard</div></div>

      <div class="grid-2" style="margin-bottom:28px">
        <div class="stat-card">
          <div class="stat-num">{student['reg_no']}</div>
          <div class="stat-label">Registration No.</div>
          <div class="stat-icon">&#128220;</div>
        </div>
        <div class="stat-card" style="--accent:#818cf8">
          <div class="stat-num" style="color:var(--accent2)">{student['option_name']}</div>
          <div class="stat-label">Programme</div>
          <div class="stat-icon">&#127891;</div>
        </div>
      </div>

      <div class="card" style="margin-bottom:20px">
        <div class="card-title"><span class="card-icon">&#128197;</span> Daily Attendance</div>
        {'<div class="alert alert-success">&#10003;&nbsp; Attendance for today has been marked.</div>' if attendance_marked else ''}
        {'<div class="alert alert-info">&#9432;&nbsp; Attendance can only be marked after 4 PM.</div>' if datetime.now().hour < 16 and not attendance_marked else ''}
        {'<form method="post" action="/student_mark_attendance"><button class="btn btn-primary" {"disabled" if datetime.now().hour < 16 else ""}>&#10003; Mark Attendance for Today</button></form>' if not attendance_marked and datetime.now().hour >= 16 else ''}
      </div>

      <div class="card">
        <div class="card-title"><span class="card-icon">&#128196;</span> Available Assessments</div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Assessment Title</th><th>Duration</th><th>Status</th><th>Action</th></tr></thead>
            <tbody>
              {''.join(f"""<tr>
                <td style="color:var(--text);font-weight:500">{cat['title']}</td>
                <td>{cat['duration_minutes']} mins</td>
                <td><span class="badge {'badge-success' if cat['status'] == 'Completed' else 'badge-blue'}">{cat['status']}</span></td>
                <td>
                  {'<a href="/cat_result/' + str(next((res['id'] for res in student_results if res['cat_id'] == cat['id']), '')) + '" class="btn btn-ghost btn-sm">View Result</a>' if cat['status'] == 'Completed' else ''}
                  {'<a href="/cat_otp/' + str(cat['id']) + '" class="btn btn-primary btn-sm">Start Assessment</a>' if cat['status'] == 'Pending' else ''}
                </td>
              </tr>""" for cat in available_cats) or '<tr><td colspan="4" style="text-align:center;padding:28px;color:var(--muted)">No assessments available.</td></tr>'}
            </tbody>
          </table>
        </div>
      </div>
    </div>"""
    return page(body, role="student", active="Home")

@app.route("/student_mark_attendance", methods=["POST"])
def student_mark_attendance():
    if session.get("role") != "student":
        return redirect("/login")
    
    data = _get_all_data()
    student_id = session.get("student_id")
    student = _find_by_id(data['students'], student_id)
    if not student:
        return redirect("/login")
    
    now = datetime.now()
    today = date.today().isoformat()
    if now.hour < 16:
        return redirect("/student_home")
    
    existing = next((att for att in data['attendances'] if att['student_id'] == student_id and att['date'] == today), None)
    if not existing:
        data['attendances'].append({
            'id': str(uuid.uuid4()),
            'student_id': student_id,
            'date': today,
            'status': 'Present'
        })
        _save_all_data(data)
    return redirect("/student_home")

# ==================== OTP GATE ====================
@app.route("/cat_otp/<cat_id>", methods=["GET","POST"])
def cat_otp(cat_id):
    if session.get("role") != "student":
        return redirect("/login")
    
    data = _get_all_data()
    student_id = session.get("student_id")
    student = _find_by_id(data['students'], student_id)
    cat = _find_by_id(data['cats'], cat_id)
    if not student or not cat:
        return redirect("/login")

    already = next((res for res in data['cat_results'] if res['student_id'] == student_id and res['cat_id'] == cat_id), None)
    if already:
        return redirect(f"/cat_result/{already['id']}")

    if not cat['otp_enabled']:
        return redirect(f"/take_cat/{cat_id}")

    error = ""
    if request.method == "POST":
        entered = request.form.get("otp","").strip()
        if entered == cat['otp_code']:
            data['cat_sessions'].append({
                'id': str(uuid.uuid4()),
                'student_id': student_id,
                'cat_id': cat_id,
                'verified': True,
                'created_at': datetime.utcnow().isoformat()
            })
            _save_all_data(data)
            session[f"otp_verified_{cat_id}"] = True
            return redirect(f"/take_cat/{cat_id}")
        error = "Incorrect OTP. Please check with your instructor."

    body = f"""
    <div class="auth-wrap"><div class="auth-box" style="max-width:460px">
      <div class="auth-logo">
        <div class="auth-logo-text">&#128274; OTP Required</div>
        <div class="auth-logo-sub">{cat['title']}</div>
      </div>
      <div class="card">
        <div class="card-title">Enter Access Code</div>
        <div class="alert alert-info">&#9432;&nbsp; This assessment requires an OTP from your instructor to begin.</div>
        {\'<div class="alert alert-error">\'+error+\'</div>\' if error else \'\'}
        <form method="post">
          <label>One-Time Password</label>
          <input name="otp" class="otp-input" placeholder="000000" maxlength="10" autocomplete="off" autofocus required>
          <div style="margin-top:22px"><button class="btn btn-primary" style="width:100%;justify-content:center;padding:13px">&#10003; Verify &amp; Start</button></div>
        </form>
      </div>
      <div style="text-align:center;margin-top:16px"><a href="/student_home" class="btn btn-ghost btn-sm">&#8592; Back to Home</a></div>
    </div></div>"""
    return page(body, role="student")

# ==================== TAKE CAT ====================
@app.route("/take_cat/<cat_id>")
def take_cat(cat_id):
    if session.get("role") != "student":
        return redirect("/login")
    
    data = _get_all_data()
    student_id = session.get("student_id")
    student = _find_by_id(data['students'], student_id)
    cat = _find_by_id(data['cats'], cat_id)
    if not student or not cat:
        return redirect("/login")

    already = next((res for res in data['cat_results'] if res['student_id'] == student_id and res['cat_id'] == cat_id), None)
    if already:
        return redirect(f"/cat_result/{already['id']}")

    if cat['otp_enabled'] and not session.get(f"otp_verified_{cat_id}"):
        # Check if there's a verified session in the data store
        verified_session = next((s for s in data['cat_sessions'] if s['student_id'] == student_id and s['cat_id'] == cat_id and s['verified']), None)
        if not verified_session:
            return redirect(f"/cat_otp/{cat_id}")
        else:
            session[f"otp_verified_{cat_id}"] = True # Restore session if found in data

    questions = _filter_data(data['questions'], cat_id=cat_id)
    if cat['randomize_questions']:
        random.shuffle(questions)

    q_order = [q['id'] for q in questions]
    session[f"cat_order_{cat_id}"] = q_order
    total_secs = cat['duration_minutes'] * 60

    questions_html = ""
    for i, q in enumerate(questions):
        questions_html += f"""
        <div class="question-card" id="q{i}">
          <div class="q-num">Question {i+1} / {len(questions)}</div>
          <div class="q-text">{q['question_text']}</div>
          <button type="button" class="option-btn" onclick="selectOption(this,\'{q['id']}\',\'A\')" data-qid="{q['id']}" data-val="A"><strong>A.</strong>&nbsp; {q['option_a']}</button>
          <button type="button" class="option-btn" onclick="selectOption(this,\'{q['id']}\',\'B\')" data-qid="{q['id']}" data-val="B"><strong>B.</strong>&nbsp; {q['option_b']}</button>
          <button type="button" class="option-btn" onclick="selectOption(this,\'{q['id']}\',\'C\')" data-qid="{q['id']}" data-val="C"><strong>C.</strong>&nbsp; {q['option_c']}</button>
          <button type="button" class="option-btn" onclick="selectOption(this,\'{q['id']}\',\'D\')" data-qid="{q['id']}" data-val="D"><strong>D.</strong>&nbsp; {q['option_d']}</button>
          <input type="hidden" name="q_{q['id']}" id="ans_{q['id']}">
        </div>"""

    body = f"""
    <!-- EXAM LOCKDOWN: no topbar, no nav -->
    <div id="examTopbar" class="exam-topbar">
      <div class="exam-brand">&#128683; EXAM IN PROGRESS — {cat['title']}</div>
      <div style="display:flex;align-items:center;gap:16px">
        <div style="font-size:12px;color:var(--muted2)"><span id="answered">0</span>/{len(questions)} answered</div>
        <div class="exam-timer" id="timer">{cat['duration_minutes']}:00</div>
      </div>
    </div>

    <!-- FACE DETECTION OVERLAY -->
    <div id="faceOverlay" style="position:fixed;bottom:20px;right:20px;z-index:300;background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);padding:12px;width:220px;display:none">
      <video id="faceVideo" autoplay muted style="width:196px;height:148px;border-radius:var(--radius-sm);object-fit:cover;border:1px solid var(--border)"></video>
      <canvas id="faceCanvas" style="display:none"></canvas>
      <div id="faceStatus" class="face-status">&#128249; Initializing camera...</div>
    </div>

    <!-- WARNING MODAL -->
    <div id="warnModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.85);z-index:500;align-items:center;justify-content:center">
      <div style="background:var(--surface2);border:2px solid var(--danger);border-radius:var(--radius);padding:36px;max-width:460px;text-align:center">
        <div style="font-size:48px;margin-bottom:16px">&#9888;</div>
        <div style="font-size:22px;font-weight:600;color:var(--danger);margin-bottom:12px">Warning: Unusual Activity Detected!</div>
        <p style="color:var(--muted2);margin-bottom:24px">Please refrain from switching tabs or opening new windows during the assessment. Such activities will be flagged.</p>
        <button class="btn btn-danger" onclick="document.getElementById('warnModal').style.display='none'">&#10003; Understood</button>
      </div>
    </div>

    <div class="container" style="max-width:800px;padding-top:90px">
      <form id="catForm" method="post" action="/submit_cat/{cat_id}">
        <input type="hidden" name="cat_start_time" value="{datetime.utcnow().isoformat()}">
        <input type="hidden" name="question_order" value="{json.dumps(q_order)}">
        <div id="questions">
          {questions_html}
        </div>
        <div style="margin-top:30px;text-align:center">
          <button type="submit" class="btn btn-primary btn-success" style="padding:14px 30px;font-size:16px">&#10003; Submit Assessment</button>
        </div>
      </form>
    </div>

    <script>
    let answeredCount = 0;
    const totalQuestions = {len(questions)};
    const timerDisplay = document.getElementById('timer');
    let timeLeft = {total_secs};
    let tabSwitches = 0;
    let faceDetected = false;
    let faceCaptureInterval;
    let lastFaceImage = null;

    function updateAnsweredCount() {
        answeredCount = document.querySelectorAll('.option-btn.selected').length;
        document.getElementById('answered').textContent = answeredCount;
    }

    function selectOption(button, qid, val) {
        const parent = button.closest('.question-card');
        parent.querySelectorAll('.option-btn').forEach(btn => btn.classList.remove('selected'));
        button.classList.add('selected');
        document.getElementById(`ans_${qid}`).value = val;
        updateAnsweredCount();
    }

    function startTimer() {
        const interval = setInterval(() => {
            timeLeft--;
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            timerDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            if (timeLeft <= 0) {
                clearInterval(interval);
                document.getElementById('catForm').submit();
            }
        }, 1000);
    }

    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            tabSwitches++;
            document.getElementById('warnModal').style.display = 'flex';
        }
    });

    // Face detection (simplified for client-side, actual detection would be server-side or more robust client-side ML)
    const video = document.getElementById('faceVideo');
    const canvas = document.getElementById('faceCanvas');
    const context = canvas.getContext('2d');
    const faceStatus = document.getElementById('faceStatus');
    const faceOverlay = document.getElementById('faceOverlay');

    async function setupCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;
            faceOverlay.style.display = 'block';
            faceStatus.textContent = '&#128247; Camera active. Detecting face...';
            video.onloadedmetadata = () => {
                video.play();
                faceCaptureInterval = setInterval(captureFace, 5000); // Capture face every 5 seconds
            };
        } catch (err) {
            console.error("Error accessing camera: ", err);
            faceStatus.textContent = '&#10060; Camera access denied or error.';
            faceOverlay.style.display = 'none';
        }
    }

    function captureFace() {
        if (video.readyState === video.HAVE_ENOUGH_DATA) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            lastFaceImage = canvas.toDataURL('image/jpeg', 0.7);
            faceDetected = true; // Assume face detected if image captured
            faceStatus.textContent = '&#128247; Face detected.';
        }
    }

    // Start timer and camera when page loads
    window.onload = () => {
        startTimer();
        setupCamera();
    };

    // Append cheating flags to form before submission
    document.getElementById('catForm').addEventListener('submit', function(event) {
        const tabSwitchesInput = document.createElement('input');
        tabSwitchesInput.type = 'hidden';
        tabSwitchesInput.name = 'tab_switches';
        tabSwitchesInput.value = tabSwitches;
        this.appendChild(tabSwitchesInput);

        const faceImageInput = document.createElement('input');
        faceImageInput.type = 'hidden';
        faceImageInput.name = 'face_image';
        faceImageInput.value = lastFaceImage || '';
        this.appendChild(faceImageInput);

        clearInterval(faceCaptureInterval);
    });

    </script>"""
    return page(body, role="student")

@app.route("/submit_cat/<cat_id>", methods=["POST"])
def submit_cat(cat_id):
    if session.get("role") != "student":
        return redirect("/login")
    
    data = _get_all_data()
    student_id = session.get("student_id")
    student = _find_by_id(data['students'], student_id)
    cat = _find_by_id(data['cats'], cat_id)
    if not student or not cat:
        return redirect("/login")

    # Prevent resubmission
    already = next((res for res in data['cat_results'] if res['student_id'] == student_id and res['cat_id'] == cat_id), None)
    if already:
        return redirect(f"/cat_result/{already['id']}")

    submitted_answers = {}
    score = 0
    total_questions = len(_filter_data(data['questions'], cat_id=cat_id))
    question_order = json.loads(request.form.get('question_order', '[]'))

    for q_id in question_order:
        answer = request.form.get(f'q_{q_id}')
        question = _find_by_id(data['questions'], q_id)
        if question:
            submitted_answers[q_id] = answer
            if answer == question['correct_answer']:
                score += 1
    
    # Cheating flags
    tab_switches = int(request.form.get('tab_switches', 0))
    face_image = request.form.get('face_image', None)
    cheating_flag = tab_switches > 0 # Simple flag for now

    new_result = {
        'id': str(uuid.uuid4()),
        'student_id': student_id,
        'cat_id': cat_id,
        'score': score,
        'total': total_questions,
        'submitted_at': datetime.utcnow().isoformat(),
        'answers_json': json.dumps(submitted_answers),
        'question_order': json.dumps(question_order),
        'cheating_flag': cheating_flag,
        'tab_switches': tab_switches,
        'ip_address': request.remote_addr, # This might not work as expected in serverless
        'device_info': request.headers.get('User-Agent'),
        'face_image': face_image
    }
    data['cat_results'].append(new_result)
    _save_all_data(data)

    # Clear OTP session data
    session.pop(f"otp_verified_{cat_id}", None)
    session.pop(f"cat_order_{cat_id}", None)

    return redirect(f"/cat_result/{new_result['id']}")

@app.route("/cat_result/<result_id>")
def cat_result(result_id):
    if session.get("role") != "student":
        return redirect("/login")
    
    data = _get_all_data()
    student_id = session.get("student_id")
    result = _find_by_id(data['cat_results'], result_id)
    if not result or result['student_id'] != student_id:
        return redirect("/student_home") # Or show 404/unauthorized

    cat = _find_by_id(data['cats'], result['cat_id'])
    if not cat:
        return redirect("/student_home")

    questions = _filter_data(data['questions'], cat_id=cat['id'])
    question_map = {q['id']: q for q in questions}
    submitted_answers = json.loads(result['answers_json'])
    question_order = json.loads(result['question_order'])

    questions_html = ""
    for q_id in question_order:
        q = question_map.get(q_id)
        if not q: continue
        student_ans = submitted_answers.get(q_id)
        correct_ans = q['correct_answer']

        options_html = ""
        for opt_key in ['A', 'B', 'C', 'D']:
            option_text = q[f'option_{opt_key.lower()}']
            btn_class = "option-btn"
            if opt_key == correct_ans:
                btn_class += " correct"
            elif opt_key == student_ans and opt_key != correct_ans:
                btn_class += " wrong"
            elif opt_key == student_ans and opt_key == correct_ans:
                btn_class += " selected" # Mark as selected and correct
            
            options_html += f"""
            <button type="button" class="{btn_class}" disabled><strong>{opt_key}.</strong>&nbsp; {option_text}</button>"""

        questions_html += f"""
        <div class="question-card">
          <div class="q-num">Question</div>
          <div class="q-text">{q['question_text']}</div>
          {options_html}
          <div style="margin-top:10px;font-size:13px;color:var(--muted2)">
            Your Answer: <span style="font-weight:600;color:{'var(--success)' if student_ans == correct_ans else 'var(--danger)'}">{student_ans or 'N/A'}</span>
            {' (Correct Answer: ' + correct_ans + ')' if student_ans != correct_ans else ''}
          </div>
        </div>"""

    body = f"""
    <div class="container" style="max-width:800px">
      <div class="page-header"><div class="page-title">Assessment Result</div><div class="page-sub">{cat['title']}</div></div>

      <div class="grid-2" style="margin-bottom:28px">
        <div class="stat-card">
          <div class="stat-num">{result['score']}/{result['total']}</div>
          <div class="stat-label">Your Score</div>
          <div class="stat-icon">&#127891;</div>
        </div>
        <div class="stat-card" style="--accent:#34d399">
          <div class="stat-num" style="color:var(--success)">{round(result['score']/result['total']*100) if result['total'] else 0}%</div>
          <div class="stat-label">Percentage</div>
          <div class="stat-icon">&#127881;</div>
        </div>
      </div>

      {'<div class="alert alert-danger">&#9888;&nbsp; This assessment was flagged for unusual activity (e.g., tab switches: ' + str(result['tab_switches']) + ').</div>' if result['cheating_flag'] else ''}
      {'<div class="card" style="margin-bottom:20px"><div class="card-title">Face Snapshot</div><img src="' + result['face_image'] + '" style="max-width:100%;border-radius:var(--radius-sm);"></div>' if result['face_image'] else ''}

      <div class="card">
        <div class="card-title"><span class="card-icon">&#128220;</span> Your Answers</div>
        {questions_html}
      </div>
      <div style="text-align:center;margin-top:20px"><a href="/student_home" class="btn btn-ghost">&#8592; Back to Home</a></div>
    </div>"""
    return page(body, role="student")

# ==================== AI TUTOR ====================
# Placeholder for AI Tutor functionality
# The original code used an external API for AI, which would need to be re-integrated
# or replaced with a Vercel-compatible solution (e.g., calling an external LLM API)

@app.route("/ai", methods=["GET", "POST"])
def ai_tutor():
    if session.get("role") != "student":
        return redirect("/login")

    ai_history = session.get("ai_history", [])
    answer = ""
    sources = []
    query = ""

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        if query:
            # This part needs to be replaced with an actual LLM call
            # For now, it's a placeholder response
            answer = f"AI Tutor is currently under maintenance. Your query was: '{query}'"
            sources = []
            ai_history.append({"query": query, "answer": answer, "sources": sources})
            session["ai_history"] = ai_history

    history_html = "".join(f"""
    <div class="ai-message ai-user"><strong>You:</strong> {h['query']}</div>
    <div class="ai-message ai-bot"><strong>AI Tutor:</strong> {h['answer']}
        {'<div class="ai-sources"><strong>Sources:</strong> ' + ''.join(f'<a href="{s['url']}" target="_blank">{s['name']}</a>' for s in h['sources']) + '</div>' if h['sources'] else ''}
    </div>""" for h in ai_history)

    body = f"""
    <div class="container" style="max-width:800px">
      <div class="page-header"><div class="page-title">AI Tutor</div><div class="page-sub">Ask anything about your courses</div></div>

      <div class="card" style="margin-bottom:20px">
        <div class="card-title"><span class="card-icon">&#129504;</span> Chat with AI</div>
        <div class="ai-chat-window" style="max-height:400px;overflow-y:auto;border:1px solid var(--border);border-radius:var(--radius-sm);padding:15px;margin-bottom:15px;background:var(--surface2)">
          {history_html or '<p style="color:var(--muted);text-align:center;padding:20px;">No conversation yet. Ask me anything!</p>'}
        </div>
        <form method="post" action="/ai" style="display:flex;gap:10px">
          <input type="text" name="query" placeholder="Ask a question..." style="flex:1" required>
          <button class="btn btn-primary">Ask</button>
        </form>
        <form method="post" action="/clear_ai" style="margin-top:10px;text-align:right;">
            <button class="btn btn-ghost btn-sm">Clear Chat</button>
        </form>
      </div>
    </div>"""
    return page(body, role="student", active="AI")

@app.route("/clear_ai", methods=["POST"])
def clear_ai():
    session.pop("ai_history", None)
    return redirect("/ai")

# ==================== ADMIN DASHBOARD ====================
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if session.get("role") != "admin":
        return redirect("/login")
    
    data = _get_all_data()
    text_q = request.form.get("q","").strip()
    option_id_filter = request.form.get("option_id","")
    options = data['student_options']

    filtered_students = data['students']
    if text_q:
        filtered_students = [s for s in filtered_students if text_q.lower() in s['reg_no'].lower() or \
                                                            text_q.lower() in s['first_name'].lower() or \
                                                            text_q.lower() in s['last_name'].lower()]
    if option_id_filter:
        filtered_students = [s for s in filtered_students if str(s['option_id']) == option_id_filter]

    # Attach option name to students for display
    option_map = {opt['id']: opt['name'] for opt in options}
    for s in filtered_students:
        s['option_name'] = option_map.get(s['option_id'], 'N/A')

    total_students = len(data['students'])
    total_cats = len(data['cats'])
    today = date.today().isoformat()
    present_today = len([att for att in data['attendances'] if att['date'] == today and att['status'] == 'Present'])
    total_results = len(data['cat_results'])
    cheat_count = len([res for res in data['cat_results'] if res['cheating_flag']])

    rows = "".join(f"""<tr>
      <td><span style="font-family:\'Space Mono\',monospace;font-size:12px;color:var(--accent)">{s['reg_no']}</span></td>
      <td style="color:var(--text);font-weight:500">{s['first_name']} {s['last_name']}</td>
      <td><span class="badge badge-indigo">{s['option_name']}</span></td>
      <td><form method="post" action="/delete_student/{s['id']}" style="display:inline"><button class="btn btn-danger btn-sm">Delete</button></form></td>
    </tr>""" for s in filtered_students)

    body = f"""
    <div class="container">
      <div class="page-header"><div class="page-title">Admin Dashboard</div><div class="page-sub">Overview of students, attendance, and assessments</div></div>

      <div class="grid-4" style="margin-bottom:28px">
        <div class="stat-card"><div class="stat-num">{total_students}</div><div class="stat-label">Total Students</div><div class="stat-icon">&#128101;</div></div>
        <div class="stat-card" style="--accent:#34d399"><div class="stat-num" style="color:var(--success)">{present_today}</div><div class="stat-label">Present Today</div><div class="stat-icon">&#128197;</div></div>
        <div class="stat-card" style="--accent:#818cf8"><div class="stat-num" style="color:var(--accent2)">{total_cats}</div><div class="stat-label">Assessments</div><div class="stat-icon">&#128196;</div></div>
        <div class="stat-card" style="--accent:#f87171"><div class="stat-num" style="color:var(--danger)">{cheat_count}</div><div class="stat-label">Flagged Results</div><div class="stat-icon">&#9888;</div></div>
      </div>

      <div class="card" style="margin-bottom:20px">
        <div class="card-title"><span class="card-icon">&#127807;</span> Programme Options</div>
        <form method="post" action="/add_option" style="display:flex;gap:10px;align-items:flex-end;margin-bottom:16px">
          <div style="flex:1"><label style="margin-top:0">New Option / Programme</label><input name="option_name" placeholder="e.g. Software Engineering" required></div>
          <button class="btn btn-primary" style="height:43px">Add Option</button>
        </form>
        <div style="display:flex;flex-wrap:wrap;gap:8px">
          {''.join(f'<div class="tag">{o['name']}<form method="post" action="/delete_option/{o['id']}" style="display:inline"><button title="Delete">&#10005;</button></form></div>' for o in options)}
        </div>
      </div>

      <div class="card">
        <div class="card-title"><span class="card-icon">&#128101;</span> Students</div>
        <form method="post" style="display:flex;gap:10px;align-items:flex-end;margin-bottom:20px">
          <div style="flex:2"><label style="margin-top:0">Search</label><input name="q" placeholder="Reg No, first or last name..." value="{text_q}"></div>
          <div style="flex:1"><label style="margin-top:0">Filter by Option</label>
            <select name="option_id">
              <option value="">All Options</option>
              {''.join(f'<option value="{o['id']}" {"selected" if option_id_filter==str(o['id']) else ""}>{o['name']}</option>' for o in options)}
            </select>
          </div>
          <button class="btn btn-ghost" style="height:43px">Filter</button>
        </form>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Reg No</th><th>Name</th><th>Option</th><th>Action</th></tr></thead>
            <tbody>{rows or '<tr><td colspan="4" style="text-align:center;padding:28px;color:var(--muted)">No students found.</td></tr>'}</tbody>
          </table>
        </div>
      </div>
    </div>"""
    return page(body, role="admin", active="Dashboard")

@app.route("/add_option", methods=["POST"])
def add_option():
    if session.get("role") != "admin": return redirect("/login")
    name = request.form["option_name"].strip()
    
    data = _get_all_data()
    if name and not next((o for o in data['student_options'] if o['name'] == name), None):
        data['student_options'].append({
            'id': str(uuid.uuid4()),
            'name': name
        })
        _save_all_data(data)
    return redirect("/dashboard")

@app.route("/delete_option/<option_id>", methods=["POST"])
def delete_option(option_id):
    if session.get("role") != "admin": return redirect("/login")
    
    data = _get_all_data()
    option = _find_by_id(data['student_options'], option_id)
    if not option:
        return redirect("/dashboard")

    # Check if there are students enrolled in this option
    if any(s['option_id'] == option_id for s in data['students']):
        return page(\'<div class="container"><div class="alert alert-error">Cannot delete option with enrolled students.</div><a href="/dashboard" class="btn btn-ghost">&#8592; Back</a></div>\', role="admin")
    
    _delete_by_id(data['student_options'], option_id)
    _save_all_data(data)
    return redirect("/dashboard")

@app.route("/delete_student/<student_id>", methods=["POST"])
def delete_student(student_id):
    if session.get("role") != "admin": return redirect("/login")
    
    data = _get_all_data()
    if _delete_by_id(data['students'], student_id):
        # Also delete related attendances and CAT results
        data['attendances'] = [att for att in data['attendances'] if att['student_id'] != student_id]
        data['cat_results'] = [res for res in data['cat_results'] if res['student_id'] != student_id]
        data['cat_sessions'] = [sess for sess in data['cat_sessions'] if sess['student_id'] != student_id]
        _save_all_data(data)
    return redirect("/dashboard")

# ==================== MARK ATTENDANCE ====================
@app.route("/mark_attendance", methods=["GET","POST"])
def mark_attendance():
    if session.get("role") != "admin": return redirect("/login")
    
    data = _get_all_data()
    all_students = data['students']
    options = data['student_options']
    option_id_filter = request.args.get("option_id","")
    selected_date_str = request.args.get("att_date", date.today().isoformat())
    try:
        selected_date = date.fromisoformat(selected_date_str)
    except ValueError:
        selected_date = date.today()

    students_to_display = all_students
    if option_id_filter:
        students_to_display = [s for s in all_students if str(s['option_id']) == option_id_filter]

    # Attach option name to students for display
    option_map = {opt['id']: opt['name'] for opt in options}
    for s in students_to_display:
        s['option_name'] = option_map.get(s['option_id'], 'N/A')

    if request.method == "POST":
        sel_date_str = request.form.get("att_date", date.today().isoformat())
        try:
            sel_date = date.fromisoformat(sel_date_str)
        except ValueError:
            sel_date = date.today()
        
        for student in all_students:
            status = "Present" if request.form.get(f"att_{student['id']}") else "Absent"
            existing_att = next((att for att in data['attendances'] if att['student_id'] == student['id'] and date.fromisoformat(att['date']) == sel_date), None)
            if existing_att:
                existing_att['status'] = status
            else:
                data['attendances'].append({
                    'id': str(uuid.uuid4()),
                    'student_id': student['id'],
                    'date': sel_date.isoformat(),
                    'status': status
                })
        _save_all_data(data)
        return page(f\' <div class="container"><div class="alert alert-success">&#10003;&nbsp; Attendance saved for {sel_date.strftime("%d %B %Y")}.</div><a href="/mark_attendance" class="btn btn-ghost">&#8592; Back</a></div>\', role="admin", active="Attendance")

    rows = ""
    for s in students_to_display:
        existing = next((att for att in data['attendances'] if att['student_id'] == s['id'] and date.fromisoformat(att['date']) == selected_date), None)
        checked = "checked" if existing and existing['status'] == "Present" else ""
        rows += f"""<tr>
          <td><span style="font-family:\'Space Mono\',monospace;font-size:12px;color:var(--accent)">{s['reg_no']}</span></td>
          <td style="color:var(--text);font-weight:500">{s['first_name']} {s['last_name']}</td>
          <td><span class="badge badge-indigo">{s['option_name']}</span></td>
          <td style="text-align:center"><input type="checkbox" name="att_{s['id']}" {checked}></td>
        </tr>"""

    body = f"""
    <div class="container">
      <div class="page-header"><div class="page-title">Mark Attendance</div><div class="page-sub">Select a date and mark students present</div></div>
      <div class="card" style="margin-bottom:20px">
        <form method="get" style="display:flex;gap:12px;align-items:flex-end;flex-wrap:wrap">
          <div><label style="margin-top:0">Date</label><input type="date" name="att_date" value="{selected_date_str}" style="width:auto"></div>
          <div><label style="margin-top:0">Filter by Option</label>
            <select name="option_id" style="width:auto">
              <option value="">All Options</option>
              {''.join(f'<option value="{o['id']}" {"selected" if option_id_filter==str(o['id']) else ""}>{o['name']}</option>' for o in options)}
            </select>
          </div>
          <button class="btn btn-ghost" style="height:43px">Apply Filter</button>
        </form>
      </div>
      <div class="card">
        <div class="card-title"><span class="card-icon">&#128197;</span> {selected_date.strftime('%A, %d %B %Y')}</div>
        <form method="post">
          <input type="hidden" name="att_date" value="{selected_date_str}">
          <div class="table-wrap">
            <table>
              <thead><tr><th>Reg No</th><th>Name</th><th>Option</th><th style="text-align:center">Present</th></tr></thead>
              <tbody>{rows or '<tr><td colspan="4" style="text-align:center;padding:28px;color:var(--muted)">No students found.</td></tr>'}</tbody>
            </table>
          </div>
          <div style="margin-top:20px;display:flex;gap:12px;align-items:center">
            <button class="btn btn-primary">&#10003; Save Attendance</button>
            <button type="button" class="btn btn-ghost btn-sm" onclick="document.querySelectorAll('input[type=checkbox]').forEach(c=>c.checked=true)">Select All</button>
            <button type="button" class="btn btn-ghost btn-sm" onclick="document.querySelectorAll('input[type=checkbox]').forEach(c=>c.checked=false)">Clear All</button>
          </div>
        </form>
      </div>
    </div>"""
    return page(body, role="admin", active="Attendance")

# ==================== ADMIN CATS ====================
@app.route("/admin_cats")
def admin_cats():
    if session.get("role") != "admin": return redirect("/login")
    
    data = _get_all_data()
    cats = data['cats']
    questions = data['questions']

    # Attach question count to each CAT
    cat_question_counts = {cat['id']: len([q for q in questions if q['cat_id'] == cat['id']]) for cat in cats}
    for cat in cats:
        cat['question_count'] = cat_question_counts.get(cat['id'], 0)

    rows = "".join(f"""<tr>
      <td style="color:var(--text);font-weight:500">{c['title']}</td>
      <td>{c['question_count']}</td>
      <td>{c['duration_minutes']} mins</td>
      <td>{'Yes' if c['otp_enabled'] else 'No'}</td>
      <td>{c['otp_code'] if c['otp_enabled'] else 'N/A'}</td>
      <td>{datetime.fromisoformat(c['created_at']).strftime('%d %b %Y')}</td>
      <td>
        <a href="/edit_cat/{c['id']}" class="btn btn-indigo btn-sm">Edit</a>
        <form method="post" action="/delete_cat/{c['id']}" style="display:inline;margin-left:5px;"><button class="btn btn-danger btn-sm">Delete</button></form>
      </td>
    </tr>""" for c in cats)

    body = f"""
    <div class="container">
      <div class="page-header"><div class="page-title">Assessments</div><div class="page-sub">Manage your CATs and questions</div></div>

      <div class="card" style="margin-bottom:20px">
        <div class="card-title"><span class="card-icon">&#128196;</span> All Assessments</div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Title</th><th>Questions</th><th>Duration</th><th>OTP Enabled</th><th>OTP Code</th><th>Created</th><th>Actions</th></tr></thead>
            <tbody>{rows or '<tr><td colspan="7" style="text-align:center;padding:28px;color:var(--muted)">No assessments created yet.</td></tr>'}</tbody>
          </table>
        </div>
        <div style="margin-top:20px;text-align:right">
          <a href="/create_cat" class="btn btn-primary">&#10133; Create New Assessment</a>
        </div>
      </div>
    </div>"""
    return page(body, role="admin", active="Assessments")

@app.route("/create_cat", methods=["GET", "POST"])
def create_cat():
    if session.get("role") != "admin": return redirect("/login")
    
    data = _get_all_data()

    if request.method == "POST":
        title = request.form["title"].strip()
        duration = int(request.form["duration"])
        otp_enabled = 'otp_enabled' in request.form
        otp_code = request.form.get("otp_code", "").strip() if otp_enabled else None
        randomize_questions = 'randomize_questions' in request.form

        new_cat_id = str(uuid.uuid4())
        new_cat = {
            'id': new_cat_id,
            'title': title,
            'created_at': datetime.utcnow().isoformat(),
            'otp_enabled': otp_enabled,
            'otp_code': otp_code,
            'randomize_questions': randomize_questions,
            'duration_minutes': duration
        }
        data['cats'].append(new_cat)

        questions_to_add = []
        i = 0
        while True:
            q_text = request.form.get(f"q{i}_text")
            if not q_text: break
            questions_to_add.append({
                'id': str(uuid.uuid4()),
                'cat_id': new_cat_id,
                'question_text': q_text.strip(),
                'option_a': request.form[f"q{i}_a"].strip(),
                'option_b': request.form[f"q{i}_b"].strip(),
                'option_c': request.form[f"q{i}_c"].strip(),
                'option_d': request.form[f"q{i}_d"].strip(),
                'correct_answer': request.form[f"q{i}_correct"].strip()
            })
            i += 1
        data['questions'].extend(questions_to_add)
        _save_all_data(data)
        return redirect("/admin_cats")

    body = f"""
    <div class="container" style="max-width:800px">
      <div class="page-header"><div class="page-title">Create New Assessment</div><div class="page-sub">Define your CAT and add questions</div></div>

      <form method="post">
        <div class="card" style="margin-bottom:20px">
          <div class="card-title"><span class="card-icon">&#128220;</span> Assessment Details</div>
          <label>Title</label>
          <input type="text" name="title" placeholder="e.g. Mid-Term Exam - Software Engineering" required>
          <label>Duration (minutes)</label>
          <input type="number" name="duration" value="60" min="1" required>
          <label style="display:flex;align-items:center;gap:10px;margin-top:20px">
            <input type="checkbox" name="otp_enabled" id="otp_enabled" onchange="document.getElementById('otp_code_field').style.display = this.checked ? 'block' : 'none'">
            Enable OTP for this assessment
          </label>
          <div id="otp_code_field" style="display:none;margin-top:10px">
            <label>OTP Code</label>
            <input type="text" name="otp_code" placeholder="e.g. 123456" maxlength="10">
          </div>
          <label style="display:flex;align-items:center;gap:10px;margin-top:20px">
            <input type="checkbox" name="randomize_questions" checked>
            Randomize question order for students
          </label>
        </div>

        <div class="card" style="margin-bottom:20px">
          <div class="card-title"><span class="card-icon">&#128221;</span> Questions</div>
          <div id="questions">
            <!-- Question blocks will be added here by JavaScript -->
          </div>
          <div style="margin-top:20px">
            <button type="button" class="btn btn-ghost" onclick="addQuestion()">&#10133; Add Question</button>
          </div>
        </div>

        <div style="text-align:center;margin-top:30px">
          <button type="submit" class="btn btn-primary" style="padding:14px 30px;font-size:16px">&#10003; Create Assessment</button>
        </div>
      </form>
    </div>

    <script>
    let questionCount = 0;
    function addQuestion() {
      const d = document.createElement('div');
      d.className = 'question-block';
      d.innerHTML = `
        <div class="q-num">Question #${questionCount + 1}</div>
        <label style="margin-top:0">Question Text</label>
        <textarea name="q${questionCount}_text" required></textarea>
        <div class="grid-2" style="gap:12px;margin-top:2px">
          <div><label>Option A</label><input name="q${questionCount}_a" required></div>
          <div><label>Option B</label><input name="q${questionCount}_b" required></div>
          <div><label>Option C</label><input name="q${questionCount}_c" required></div>
          <div><label>Option D</label><input name="q${questionCount}_d" required></div>
        </div>
        <label>Correct Answer</label>
        <select name="q${questionCount}_correct" required>
          <option value="A">A</option><option value="B">B</option><option value="C">C</option><option value="D">D</option>
        </select>
      `;
      document.getElementById('questions').appendChild(d);
      questionCount++;
    }
    // Add one question by default
    addQuestion();
    </script>"""
    return page(body, role="admin", active="Assessments", extra_style=Q_BLOCK_STYLE)

@app.route("/edit_cat/<cat_id>", methods=["GET", "POST"])
def edit_cat(cat_id):
    if session.get("role") != "admin": return redirect("/login")
    
    data = _get_all_data()
    cat = _find_by_id(data['cats'], cat_id)
    if not cat:
        return redirect("/admin_cats")
    
    cat_questions = _filter_data(data['questions'], cat_id=cat_id)

    if request.method == "POST":
        cat['title'] = request.form["title"].strip()
        cat['duration_minutes'] = int(request.form["duration"])
        cat['otp_enabled'] = 'otp_enabled' in request.form
        cat['otp_code'] = request.form.get("otp_code", "").strip() if cat['otp_enabled'] else None
        cat['randomize_questions'] = 'randomize_questions' in request.form

        # Update existing questions and add new ones
        updated_question_ids = []
        questions_to_add = []
        i = 0
        while True:
            q_id = request.form.get(f"q{i}_id")
            q_text = request.form.get(f"q{i}_text")
            if not q_text: break

            if q_id: # Existing question
                question = _find_by_id(data['questions'], q_id)
                if question:
                    question['question_text'] = q_text.strip()
                    question['option_a'] = request.form[f"q{i}_a"].strip()
                    question['option_b'] = request.form[f"q{i}_b"].strip()
                    question['option_c'] = request.form[f"q{i}_c"].strip()
                    question['option_d'] = request.form[f"q{i}_d"].strip()
                    question['correct_answer'] = request.form[f"q{i}_correct"].strip()
                    updated_question_ids.append(q_id)
            else: # New question
                questions_to_add.append({
                    'id': str(uuid.uuid4()),
                    'cat_id': cat_id,
                    'question_text': q_text.strip(),
                    'option_a': request.form[f"q{i}_a"].strip(),
                    'option_b': request.form[f"q{i}_b"].strip(),
                    'option_c': request.form[f"q{i}_c"].strip(),
                    'option_d': request.form[f"q{i}_d"].strip(),
                    'correct_answer': request.form[f"q{i}_correct"].strip()
                })
            i += 1
        
        # Remove deleted questions
        data['questions'] = [q for q in data['questions'] if q['cat_id'] != cat_id or q['id'] in updated_question_ids]
        data['questions'].extend(questions_to_add)
        _save_all_data(data)
        return redirect("/admin_cats")

    questions_html = ""
    for i, q in enumerate(cat_questions):
        questions_html += f"""
        <div class="question-block">
          <div class="q-num">Question #{i + 1}</div>
          <input type="hidden" name="q{i}_id" value="{q['id']}">
          <label style="margin-top:0">Question Text</label>
          <textarea name="q{i}_text" required>{q['question_text']}</textarea>
          <div class="grid-2" style="gap:12px;margin-top:2px">
            <div><label>Option A</label><input name="q{i}_a" value="{q['option_a']}" required></div>
            <div><label>Option B</label><input name="q{i}_b" value="{q['option_b']}" required></div>
            <div><label>Option C</label><input name="q{i}_c" value="{q['option_c']}" required></div>
            <div><label>Option D</label><input name="q{i}_d" value="{q['option_d']}" required></div>
          </div>
          <label>Correct Answer</label>
          <select name="q{i}_correct" required>
            <option value="A" {'selected' if q['correct_answer'] == 'A' else ''}>A</option>
            <option value="B" {'selected' if q['correct_answer'] == 'B' else ''}>B</option>
            <option value="C" {'selected' if q['correct_answer'] == 'C' else ''}>C</option>
            <option value="D" {'selected' if q['correct_answer'] == 'D' else ''}>D</option>
          </select>
          <div style="margin-top:15px;text-align:right;">
            <button type="button" class="btn btn-danger btn-sm" onclick="this.closest('.question-block').remove();">Remove Question</button>
          </div>
        </div>"""

    body = f"""
    <div class="container" style="max-width:800px">
      <div class="page-header"><div class="page-title">Edit Assessment</div><div class="page-sub">{cat['title']}</div></div>

      <form method="post">
        <div class="card" style="margin-bottom:20px">
          <div class="card-title"><span class="card-icon">&#128220;</span> Assessment Details</div>
          <label>Title</label>
          <input type="text" name="title" value="{cat['title']}" required>
          <label>Duration (minutes)</label>
          <input type="number" name="duration" value="{cat['duration_minutes']}" min="1" required>
          <label style="display:flex;align-items:center;gap:10px;margin-top:20px">
            <input type="checkbox" name="otp_enabled" id="otp_enabled" {'checked' if cat['otp_enabled'] else ''} onchange="document.getElementById('otp_code_field').style.display = this.checked ? 'block' : 'none'">
            Enable OTP for this assessment
          </label>
          <div id="otp_code_field" style="display:{'block' if cat['otp_enabled'] else 'none'};margin-top:10px">
            <label>OTP Code</label>
            <input type="text" name="otp_code" value="{cat['otp_code'] or ''}" placeholder="e.g. 123456" maxlength="10">
          </div>
          <label style="display:flex;align-items:center;gap:10px;margin-top:20px">
            <input type="checkbox" name="randomize_questions" {'checked' if cat['randomize_questions'] else ''}>
            Randomize question order for students
          </label>
        </div>

        <div class="card" style="margin-bottom:20px">
          <div class="card-title"><span class="card-icon">&#128221;</span> Questions</div>
          <div id="questions">
            {questions_html}
          </div>
          <div style="margin-top:20px">
            <button type="button" class="btn btn-ghost" onclick="addQuestion()">&#10133; Add Question</button>
          </div>
        </div>

        <div style="text-align:center;margin-top:30px">
          <button type="submit" class="btn btn-primary" style="padding:14px 30px;font-size:16px">&#10003; Update Assessment</button>
        </div>
      </form>
    </div>

    <script>
    let questionCount = {len(cat_questions)};
    function addQuestion() {
      const d = document.createElement('div');
      d.className = 'question-block';
      d.innerHTML = `
        <div class="q-num">Question #${questionCount + 1}</div>
        <label style="margin-top:0">Question Text</label>
        <textarea name="q${questionCount}_text" required></textarea>
        <div class="grid-2" style="gap:12px;margin-top:2px">
          <div><label>Option A</label><input name="q${questionCount}_a" required></div>
          <div><label>Option B</label><input name="q${questionCount}_b" required></div>
          <div><label>Option C</label><input name="q${questionCount}_c" required></div>
          <div><label>Option D</label><input name="q${questionCount}_d" required></div>
        </div>
        <label>Correct Answer</label>
        <select name="q${questionCount}_correct" required>
          <option value="A">A</option><option value="B">B</option><option value="C">C</option><option value="D">D</option>
        </select>
        <div style="margin-top:15px;text-align:right;">
            <button type="button" class="btn btn-danger btn-sm" onclick="this.closest('.question-block').remove();">Remove Question</button>
        </div>
      `;
      document.getElementById('questions').appendChild(d);
      questionCount++;
    }
    </script>"""
    return page(body, role="admin", active="Assessments", extra_style=Q_BLOCK_STYLE)

@app.route("/delete_cat/<cat_id>", methods=["POST"])
def delete_cat(cat_id):
    if session.get("role") != "admin": return redirect("/login")
    
    data = _get_all_data()
    if _delete_by_id(data['cats'], cat_id):
        # Delete associated questions, results, and sessions
        data['questions'] = [q for q in data['questions'] if q['cat_id'] != cat_id]
        data['cat_results'] = [res for res in data['cat_results'] if res['cat_id'] != cat_id]
        data['cat_sessions'] = [sess for sess in data['cat_sessions'] if sess['cat_id'] != cat_id]
        _save_all_data(data)
    return redirect("/admin_cats")

# ==================== REPORTS ====================
@app.route("/reports")
def reports():
    if session.get("role") != "admin": return redirect("/login")
    
    data = _get_all_data()
    cats = data['cats']
    cat_results = data['cat_results']
    students = data['students']
    student_options = data['student_options']

    student_map = {s['id']: s for s in students}
    option_map = {o['id']: o['name'] for o in student_options}

    cats_summary = ""
    for cat in cats:
        results_for_cat = _filter_data(cat_results, cat_id=cat['id'])
        if not results_for_cat: continue

        total_scores = 0
        total_possible = 0
        for r in results_for_cat:
            total_scores += r['score']
            total_possible += r['total']
        
        avg = round(total_scores / total_possible * 100) if total_possible else 0

        rows = "".join(
            f\'<tr><td><span style="font-family:\'Space Mono\',monospace;font-size:12px;color:var(--accent)">{student_map[r['student_id']]['reg_no']}</span></td>\'
            f\'<td><span style="color:var(--text);font-weight:500">{student_map[r['student_id']]['first_name']} {student_map[r['student_id']]['last_name']}</span></td>\'
            f\'<td><span class="badge badge-indigo">{option_map.get(student_map[r['student_id']]['option_id'], 'N/A')}</span></td>\'
            f\'<td><span style="font-family:\'Space Mono\',monospace">{r['score']}/{r['total']}</span></td>\'
            f\'<td><span class="badge {"badge-success" if round(r['score']/r['total']*100)>=50 else "badge-danger"}">{round(r['score']/r['total']*100) if r['total'] else 0}%</span></td>\'
            f\'<td>{"<span class=badge badge-danger>&#9888; Flagged</span>" if r['cheating_flag'] else ""}</td>\'
            f\'<td><span style="color:var(--muted);font-size:12.5px">{datetime.fromisoformat(r['submitted_at']).strftime("%d %b %Y %H:%M")}</span></td></tr>\'
            for r in results_for_cat
        )
        cats_summary += f"""
        <div style="margin-bottom:28px">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
            <div style="font-size:15px;font-weight:600;color:var(--text)">{cat['title']}</div>
            <div style="display:flex;gap:8px">
              <span class="badge badge-blue">Avg: {avg}%</span>

            </div>
          </div>
          <div class="table-wrap"><table>
            <thead><tr><th>Reg No</th><th>Name</th><th>Option</th><th>Score</th><th>%</th><th>Flag</th><th>Submitted</th></tr></thead>
            <tbody>{rows}</tbody>
          </table></div>
        </div>"""

    body = f"""
    <div class="container">
      <div class="page-header"><div class="page-title">Reports</div><div class="page-sub">Export attendance and assessment data</div></div>
      <div class="grid-2" style="margin-bottom:24px">
        <div class="card">
          <div class="card-title"><span class="card-icon">&#128197;</span> Attendance Report</div>
          <form method="get" action="/export_attendance_csv">
            <label style="margin-top:0">From Date</label><input type="date" name="from_date">
            <label>To Date</label><input type="date" name="to_date">
            <label>Programme</label>
            <select name="option_id">
              <option value="">All Programmes</option>
              {''.join(f'<option value="{o['id']}">{o['name']}</option>' for o in student_options)}
            </select>
            <div style="margin-top:18px"><button class="btn btn-success">&#8681; Download Attendance CSV</button></div>
          </form>
        </div>
        <div class="card">
          <div class="card-title"><span class="card-icon">&#128196;</span> Marks Report</div>
          <form method="get" action="/export_marks_csv">
            <label style="margin-top:0">Assessment (CAT)</label>
            <select name="cat_id">
              <option value="">All CATs</option>
              {''.join(f'<option value="{c['id']}">{c['title']}</option>' for c in cats)}
            </select>
            <label>Programme</label>
            <select name="option_id">
              <option value="">All Programmes</option>
              {''.join(f'<option value="{o['id']}">{o['name']}</option>' for o in student_options)}
            </select>
            <div style="margin-top:18px"><button class="btn btn-success">&#8681; Download Marks CSV</button></div>
          </form>
        </div>
      </div>
      <div class="card">
        <div class="card-title"><span class="card-icon">&#128200;</span> Marks Summary</div>
        {cats_summary or '<p style="color:var(--muted);font-size:13.5px">No assessment results yet.</p>'}
      </div>
    </div>"""
    return page(body, role="admin", active="Reports")

# ==================== CSV EXPORTS ====================
@app.route("/export_attendance_csv")
def export_attendance_csv():
    if session.get("role") != "admin": return redirect("/login")
    
    data = _get_all_data()
    all_students = data['students']
    all_attendances = data['attendances']
    student_options = data['student_options']

    from_date_str = request.args.get("from_date")
    to_date_str = request.args.get("to_date")
    option_id_filter = request.args.get("option_id")

    try:
        from_date = date.fromisoformat(from_date_str) if from_date_str else None
        to_date = date.fromisoformat(to_date_str) if to_date_str else None
    except ValueError:
        from_date = to_date = None

    students_to_export = all_students
    if option_id_filter:
        students_to_export = [s for s in all_students if str(s['option_id']) == option_id_filter]

    # Filter attendances by date range
    filtered_attendances = []
    for att in all_attendances:
        att_date = date.fromisoformat(att['date'])
        if (from_date is None or att_date >= from_date) and \
           (to_date is None or att_date <= to_date):
            filtered_attendances.append(att)
    
    all_dates = sorted(list(set(date.fromisoformat(a['date']) for a in filtered_attendances)))

    option_map = {o['id']: o['name'] for o in student_options}
    student_attendance_map = {s['id']: {date.fromisoformat(att['date']): att['status'] for att in _filter_data(filtered_attendances, student_id=s['id'])} for s in students_to_export}

    rows = [["Reg No","First Name","Last Name","Option"] + [str(d) for d in all_dates] + ["Total Present","Total Absent"]]
    for s in students_to_export:
        row = [s['reg_no'], s['first_name'], s['last_name'], option_map.get(s['option_id'], 'N/A')]
        present_count = 0
        for d in all_dates:
            status = student_attendance_map.get(s['id'], {}).get(d, "Absent")
            row.append(status)
            if status == "Present":
                present_count += 1
        row += [str(present_count), str(len(all_dates) - present_count)]
        rows.append(row)
    
    csv_rows = [",".join(map(str, r)) for r in rows]
    return Response("\n".join(csv_rows), mimetype="text/csv", headers={"Content-Disposition":"attachment;filename=attendance_report.csv"})

@app.route("/export_marks_csv")
def export_marks_csv():
    if session.get("role") != "admin": return redirect("/login")
    
    data = _get_all_data()
    all_cats = data['cats']
    all_students = data['students']
    all_cat_results = data['cat_results']
    student_options = data['student_options']
    all_questions = data['questions']

    cat_id_filter = request.args.get("cat_id")
    option_id_filter = request.args.get("option_id")

    cats_to_export = [c for c in all_cats if cat_id_filter is None or str(c['id']) == cat_id_filter]
    students_to_export = [s for s in all_students if option_id_filter is None or str(s['option_id']) == option_id_filter]

    option_map = {o['id']: o['name'] for o in student_options}
    question_counts_map = {cat['id']: len([q for q in all_questions if q['cat_id'] == cat['id']]) for cat in all_cats}

    headers = ["Reg No","First Name","Last Name","Option"]
    for c in cats_to_export:
        headers += [f"{c['title']} (Score)", f"{c['title']} (Total)", f"{c['title']} (%)", f"{c['title']} (Flag)"]
    rows = [headers]

    for s in students_to_export:
        row = [s['reg_no'], s['first_name'], s['last_name'], option_map.get(s['option_id'], 'N/A')]
        for c in cats_to_export:
            result = next((res for res in all_cat_results if res['student_id'] == s['id'] and res['cat_id'] == c['id']), None)
            if result:
                pct = round(result['score']/result['total']*100) if result['total'] else 0
                flag = "FLAGGED" if result['cheating_flag'] else "OK"
                row += [str(result['score']), str(result['total']), f"{pct}%", flag]
            else:
                row += ["N/A", str(question_counts_map.get(c['id'], 0)), "N/A", "N/A"]
        rows.append(row)
    
    csv_rows = [",".join(map(str, r)) for r in rows]
    return Response("\n".join(csv_rows), mimetype="text/csv", headers={"Content-Disposition":"attachment;filename=marks_report.csv"})

# ==================== VERCEL ENTRY POINT ====================
# Vercel expects a 'app' or 'wsgi_app' variable at the top level
# to serve the Flask application.

# if __name__ == "__main__":
#     app.run(debug=True, use_reloader=False)

