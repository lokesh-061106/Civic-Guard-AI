import os
import json
import asyncio
import hashlib
import hmac
import base64
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, Response, jsonify, g
from pydantic import BaseModel, Field, ValidationError
from agents import run_roadguard_pipeline, run_direct_intelligence_query

# Initialize Flask App
app = Flask(__name__, static_folder='static', template_folder='templates')

# Database Files
USERS_FILE = "users.json"
INCIDENTS_FILE = "incidents.json"
REWARDS_FILE = "rewards.json"
LEADERBOARD_FILE = "leaderboard.json"
ANALYTICS_FILE = "analytics.json"
WORKORDERS_FILE = "workorders.json"
AUDIT_LOGS_FILE = "audit_logs.json"

# Secret Key for signed tokens (JWT-like)
JWT_SECRET = os.environ.get("JWT_SECRET", "civicguard-secure-secret-key-98765")

# --- UTILITIES ---

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token(payload: dict) -> str:
    # Expire in 24 hours
    payload["exp"] = (datetime.now(timezone.utc) + timedelta(hours=24)).timestamp()
    payload_str = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_str.encode()).decode().rstrip("=")
    signature = hmac.new(JWT_SECRET.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"

def verify_token(token: str) -> dict | None:
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, signature = parts
        expected_sig = hmac.new(JWT_SECRET.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        
        # Add padding back
        padding = 4 - (len(payload_b64) % 4)
        if padding < 4:
            payload_b64 += "=" * padding
        payload_str = base64.urlsafe_b64decode(payload_b64.encode()).decode()
        payload = json.loads(payload_str)
        
        if payload.get("exp", 0) < datetime.now(timezone.utc).timestamp():
            return None # Expired
            
        return payload
    except Exception:
        return None

def read_json_file(filename: str, default_val) -> list | dict:
    if not os.path.exists(filename):
        return default_val
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except Exception:
        return default_val

def write_json_file(filename: str, data) -> bool:
    try:
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False

def add_audit_log(event_type: str, username: str, details: str):
    ip = request.remote_addr or "127.0.0.1"
    logs = read_json_file(AUDIT_LOGS_FILE, [])
    log_id = f"AUD-RG-{int(datetime.now(timezone.utc).timestamp()) % 100000:05d}-{len(logs)}"
    logs.append({
        "log_id": log_id,
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "event_type": event_type,
        "username": username,
        "ip_address": ip,
        "details": details
    })
    write_json_file(AUDIT_LOGS_FILE, logs)

# --- PYDANTIC VALIDATION MODELS ---

class RegisterInput(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=6)
    fullname: str = Field(..., min_length=2, max_length=50)

class LoginInput(BaseModel):
    username: str = Field(...)
    password: str = Field(...)

class ReportInput(BaseModel):
    description: str = Field(..., min_length=10)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    image_url: str = Field(default=None)

class StatusUpdateInput(BaseModel):
    incident_id: str = Field(...)
    status: str = Field(...)

class UserStatusInput(BaseModel):
    username: str = Field(...)
    status: str = Field(...)

# --- MIDDLEWARE FOR AUTHENTICATION ---

def get_auth_token():
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    return request.args.get("token") # Fallback for SSE query params

def requires_auth(roles=None):
    def decorator(f):
        def wrapper(*args, **kwargs):
            token = get_auth_token()
            if not token:
                return jsonify({"error": "Authorization token required"}), 401
            payload = verify_token(token)
            if not payload:
                return jsonify({"error": "Invalid or expired token"}), 401
            
            # Check User Status (Restriction or Suspension)
            users = read_json_file(USERS_FILE, [])
            user_rec = next((u for u in users if u["username"] == payload["username"]), None)
            if not user_rec:
                return jsonify({"error": "User profile not found"}), 401
            
            if user_rec.get("status") == "suspended":
                return jsonify({"error": "This account has been suspended due to AI FraudGuard violations."}), 403
            
            g.current_user = user_rec
            
            if roles and payload.get("role") not in roles:
                return jsonify({"error": "Insufficient permissions for this action"}), 403
            
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

# --- API ROUTES ---

@app.route('/')
def index():
    """Renders the main multi-view SPA frontend."""
    return render_template('index.html')

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = RegisterInput(**(request.json or {}))
    except ValidationError as err:
        return jsonify({"error": "Input validation failed", "details": err.errors()}), 400
        
    users = read_json_file(USERS_FILE, [])
    if any(u["username"] == data.username for u in users):
        return jsonify({"error": "Username already exists"}), 409
        
    new_user = {
        "username": data.username,
        "password": hash_password(data.password),
        "fullname": data.fullname,
        "role": "citizen",
        "points": 0,
        "badges": [],
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat() + "Z"
    }
    users.append(new_user)
    write_json_file(USERS_FILE, users)
    
    # Auto-add to leaderboard
    leaderboard = read_json_file(LEADERBOARD_FILE, [])
    leaderboard.append({
        "username": data.username,
        "fullname": data.fullname,
        "points": 0,
        "rank": len(leaderboard) + 1,
        "badges_count": 0,
        "reports_count": 0
    })
    write_json_file(LEADERBOARD_FILE, leaderboard)
    
    add_audit_log("USER_REGISTRATION", data.username, f"Registered new citizen account: {data.fullname}")
    
    # Generate token
    token = generate_token({"username": data.username, "role": "citizen"})
    return jsonify({
        "message": "User registered successfully",
        "token": token,
        "username": data.username,
        "fullname": data.fullname,
        "role": "citizen"
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = LoginInput(**(request.json or {}))
    except ValidationError as err:
        return jsonify({"error": "Input validation failed", "details": err.errors()}), 400
        
    users = read_json_file(USERS_FILE, [])
    user_rec = next((u for u in users if u["username"] == data.username), None)
    
    if not user_rec or user_rec["password"] != hash_password(data.password):
        return jsonify({"error": "Invalid username or password"}), 401
        
    if user_rec.get("status") == "suspended":
        return jsonify({"error": "This account is suspended due to fraud violations."}), 403
        
    token = generate_token({"username": user_rec["username"], "role": user_rec["role"]})
    
    add_audit_log("USER_LOGIN", user_rec["username"], f"Logged in successfully. Role: {user_rec['role']}")
    
    return jsonify({
        "token": token,
        "username": user_rec["username"],
        "fullname": user_rec["fullname"],
        "role": user_rec["role"],
        "points": user_rec.get("points", 0),
        "badges": user_rec.get("badges", []),
        "status": user_rec.get("status", "active")
    })

@app.route('/api/incidents', methods=['GET'])
def get_incidents():
    incidents = read_json_file(INCIDENTS_FILE, [])
    return jsonify(list(reversed(incidents)))

@app.route('/api/incidents/update', methods=['POST'])
@requires_auth(roles=["government", "admin"])
def update_incident_status():
    try:
        data = StatusUpdateInput(**(request.json or {}))
    except ValidationError as err:
        return jsonify({"error": "Input validation failed", "details": err.errors()}), 400
        
    incidents = read_json_file(INCIDENTS_FILE, [])
    target_inc = next((i for i in incidents if i["incident_id"] == data.incident_id), None)
    
    if not target_inc:
        return jsonify({"error": f"Incident {data.incident_id} not found"}), 404
        
    old_status = target_inc.get("status", "Open")
    target_inc["status"] = data.status
    write_json_file(INCIDENTS_FILE, incidents)
    
    # Sync with Work Order
    workorders = read_json_file(WORKORDERS_FILE, [])
    for wo in workorders:
        if wo["incident_id"] == data.incident_id:
            if data.status == "Resolved":
                wo["status"] = "Completed"
            elif data.status == "In Progress":
                wo["status"] = "In Progress"
            break
    write_json_file(WORKORDERS_FILE, workorders)
    
    # Sync Analytics
    analytics = read_json_file(ANALYTICS_FILE, {})
    if "summary" in analytics:
        resolved_count = len([i for i in incidents if i["status"] == "Resolved"])
        analytics["summary"]["resolved_incidents"] = resolved_count
        analytics["summary"]["pending_incidents"] = len(incidents) - resolved_count
        write_json_file(ANALYTICS_FILE, analytics)
        
    add_audit_log(
        event_type="INCIDENT_STATUS_UPDATE",
        username=g.current_user["username"],
        details=f"Updated status of {data.incident_id} from '{old_status}' to '{data.status}'"
    )
    
    return jsonify({"message": f"Incident status updated successfully to {data.status}"})

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard_endpoint():
    leaderboard = read_json_file(LEADERBOARD_FILE, [])
    return jsonify(leaderboard)

@app.route('/api/rewards', methods=['GET'])
def get_rewards_endpoint():
    rewards = read_json_file(REWARDS_FILE, [])
    return jsonify(list(reversed(rewards)))

@app.route('/api/analytics', methods=['GET'])
def get_analytics_endpoint():
    analytics = read_json_file(ANALYTICS_FILE, {})
    return jsonify(analytics)

@app.route('/api/workorders', methods=['GET'])
@requires_auth(roles=["government", "admin"])
def get_workorders_endpoint():
    workorders = read_json_file(WORKORDERS_FILE, [])
    return jsonify(list(reversed(workorders)))

@app.route('/api/users', methods=['GET'])
@requires_auth(roles=["admin"])
def get_users_endpoint():
    users = read_json_file(USERS_FILE, [])
    # Strip passwords for security
    safe_users = []
    for u in users:
        u_copy = u.copy()
        if "password" in u_copy:
            del u_copy["password"]
        safe_users.append(u_copy)
    return jsonify(safe_users)

@app.route('/api/users/update-status', methods=['POST'])
@requires_auth(roles=["admin"])
def update_user_status():
    try:
        data = UserStatusInput(**(request.json or {}))
    except ValidationError as err:
        return jsonify({"error": "Input validation failed", "details": err.errors()}), 400
        
    users = read_json_file(USERS_FILE, [])
    target_u = next((u for u in users if u["username"] == data.username), None)
    
    if not target_u:
        return jsonify({"error": f"User {data.username} not found"}), 404
        
    old_status = target_u.get("status", "active")
    target_u["status"] = data.status
    write_json_file(USERS_FILE, users)
    
    add_audit_log(
        event_type="USER_STATUS_CHANGE",
        username=g.current_user["username"],
        details=f"Admin updated user status of '{data.username}' from '{old_status}' to '{data.status}'"
    )
    
    return jsonify({"message": f"User status updated successfully to {data.status}"})

@app.route('/api/audit-logs', methods=['GET'])
@requires_auth(roles=["admin"])
def get_audit_logs_endpoint():
    logs = read_json_file(AUDIT_LOGS_FILE, [])
    return jsonify(list(reversed(logs)))

@app.route('/api/city-report', methods=['POST'])
@requires_auth(roles=["citizen", "government", "admin"])
def get_city_intelligence_report():
    data = request.json or {}
    city = data.get("city", "Chennai")
    
    # Run the direct intelligence agent routine asynchronously
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        report_markdown = loop.run_until_complete(run_direct_intelligence_query(city))
        return jsonify({"report": report_markdown})
    except Exception as e:
        return jsonify({"error": f"Intelligence Agent Failed: {str(e)}"}), 500
    finally:
        loop.close()

# --- STREAMING AGENT SSE RUNNER ---

@app.route('/api/report', methods=['GET'])
@requires_auth(roles=["citizen", "government", "admin"])
def report_incident_stream():
    """
    Spawns the ADK sequential multi-agent pipeline and streams SSE trace updates.
    Arguments must be passed as URL query parameters.
    """
    description = request.args.get("description")
    latitude = request.args.get("latitude")
    longitude = request.args.get("longitude")
    image_url = request.args.get("image_url")
    username = g.current_user["username"]
    
    # Basic Validation
    if not description or not latitude or not longitude:
        return jsonify({"error": "Missing parameters: description, latitude, longitude"}), 400
        
    try:
        lat_float = float(latitude)
        lng_float = float(longitude)
    except ValueError:
        return jsonify({"error": "Invalid coordinates format"}), 400
        
    # Rate Limiting & User Restriction Checks
    if g.current_user.get("status") == "restricted":
        # Restricted users cannot file reports (FraudGuard penalty)
        def restricted_sse_generator():
            err_payload = {
                "node": "error",
                "text": "Your account has been RESTRICTED by FraudGuard. Submissions are temporarily blocked."
            }
            yield f"data: {json.dumps(err_payload)}\n\n"
        return Response(restricted_sse_generator(), mimetype='text/event-stream')

    def sse_event_generator():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run the 7-agent ADK pipeline
            pipeline = run_roadguard_pipeline(username, description, lat_float, lng_float, image_url)
            
            while True:
                try:
                    chunk = loop.run_until_complete(pipeline.__anext__())
                    yield f"data: {json.dumps(chunk)}\n\n"
                except StopAsyncIteration:
                    break
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_data = {"node": "error", "text": f"Agent Pipeline Execution Failed: {str(e)}"}
            yield f"data: {json.dumps(error_data)}\n\n"
        finally:
            loop.close()
            
    return Response(sse_event_generator(), mimetype='text/event-stream')

# --- INITIALIZATION ---

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Run server locally on all interfaces
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
