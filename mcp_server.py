import json
import os
import math
from datetime import datetime, timezone, timedelta
from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server
mcp = FastMCP("CivicGuard Registry Server")

# File paths
USERS_FILE = "users.json"
INCIDENTS_FILE = "incidents.json"
REWARDS_FILE = "rewards.json"
LEADERBOARD_FILE = "leaderboard.json"
ANALYTICS_FILE = "analytics.json"
WORKORDERS_FILE = "workorders.json"
AUDIT_LOGS_FILE = "audit_logs.json"

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates geodetic distance in meters using Haversine formula."""
    R = 6371000.0  # Radius of Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

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

def add_audit_log(event_type: str, username: str, details: str, ip: str = "127.0.0.1"):
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

def sync_leaderboard():
    """Recalculates the leaderboard from users.json."""
    users = read_json_file(USERS_FILE, [])
    # Sort citizens by points descending
    citizens = [u for u in users if u["role"] == "citizen" and u["status"] != "suspended"]
    citizens.sort(key=lambda x: x["points"], reverse=True)
    
    leaderboard = []
    for i, c in enumerate(citizens):
        leaderboard.append({
            "username": c["username"],
            "fullname": c["fullname"],
            "points": c["points"],
            "rank": i + 1,
            "badges_count": len(c.get("badges", [])),
            "reports_count": len([inc for inc in read_json_file(INCIDENTS_FILE, []) if inc.get("username") == c["username"]])
        })
    write_json_file(LEADERBOARD_FILE, leaderboard)

# MCP TOOLS IMPLEMENTATION

@mcp.tool()
def get_location_context(lat: float, lng: float) -> dict:
    """
    Fetch simulated traffic volume and school-zone/hospital proximity context for a latitude and longitude.
    """
    hash_val = abs(hash((lat, lng)))
    
    traffic_options = ["Low", "Medium", "High"]
    traffic_density = traffic_options[hash_val % len(traffic_options)]
    
    school_zone = (hash_val % 3 == 0)
    school_zone_distance = 120.5 if school_zone else 850.0
    
    hospital_zone = (hash_val % 5 == 0)
    hospital_zone_distance = 250.0 if hospital_zone else 1500.0
    
    road_classes = ["Primary Highway", "Arterial City Road", "Residential Collector Street", "Alley Local Road"]
    road_classification = road_classes[hash_val % len(road_classes)]
    
    population_options = ["Low (Rural/Industrial)", "Medium (Suburban)", "High (Urban Center)"]
    population_density = population_options[hash_val % len(population_options)]
    
    speed_limit = 20 if (school_zone or hospital_zone) else (65 if road_classification == "Primary Highway" else 35)
    
    return {
        "latitude": lat,
        "longitude": lng,
        "traffic_density": traffic_density,
        "school_zone": school_zone,
        "school_zone_distance_meters": school_zone_distance,
        "hospital_zone": hospital_zone,
        "hospital_zone_distance_meters": hospital_zone_distance,
        "road_classification": road_classification,
        "population_density": population_density,
        "speed_limit_mph": speed_limit,
        "queried_at": datetime.now(timezone.utc).isoformat() + "Z"
    }

@mcp.tool()
def save_incident(payload: dict) -> str:
    """
    Saves a verified hazard incident to the incidents.json registry and updates analytics/workorders.
    """
    incidents = read_json_file(INCIDENTS_FILE, [])
    
    # Generate unique ID if not present
    incident_id = payload.get("incident_id")
    if not incident_id:
        incident_id = f"HZ-RG-{int(datetime.now(timezone.utc).timestamp()) % 100000:05d}"
        payload["incident_id"] = incident_id
        
    payload["created_at"] = payload.get("created_at", datetime.now(timezone.utc).isoformat() + "Z")
    payload["status"] = payload.get("status", "Open")
    
    incidents.append(payload)
    write_json_file(INCIDENTS_FILE, incidents)
    
    # Auto-generate work order
    workorders = read_json_file(WORKORDERS_FILE, [])
    wo_id = f"WO-RG-{incident_id.split('-')[-1]}"
    
    gov_details = payload.get("government", {})
    repair_details = payload.get("repair", {})
    
    new_workorder = {
        "work_order_id": wo_id,
        "incident_id": incident_id,
        "assigned_department": gov_details.get("assigned_department", "Public Works Division"),
        "priority": payload.get("risk", {}).get("priority", "Medium"),
        "status": "Assigned",
        "materials": repair_details.get("materials", ["Standard Repair Mix"]),
        "budget": repair_details.get("budget", 250.0),
        "labor_hours": float(repair_details.get("timeline", "4 hours").split()[0]) if repair_details.get("timeline") else 4.0,
        "scheduled_start": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat() + "Z",
        "created_at": datetime.now(timezone.utc).isoformat() + "Z"
    }
    workorders.append(new_workorder)
    write_json_file(WORKORDERS_FILE, workorders)
    
    # Update Government summary link
    payload["government"]["work_order_id"] = wo_id
    
    # Update Analytics
    analytics = read_json_file(ANALYTICS_FILE, {})
    if "summary" in analytics:
        analytics["summary"]["total_incidents"] = len(incidents)
        analytics["summary"]["pending_incidents"] = len([i for i in incidents if i["status"] in ["Open", "Scheduled", "In Progress"]])
        
        dtype = payload.get("detection", {}).get("damage_type", "Pothole")
        if dtype not in analytics.get("by_type", {}):
            analytics.setdefault("by_type", {})[dtype] = 0
        analytics["by_type"][dtype] = analytics["by_type"].get(dtype, 0) + 1
        
        priority = payload.get("risk", {}).get("priority", "Medium")
        analytics.setdefault("by_priority", {})
        analytics["by_priority"][priority] = analytics["by_priority"].get(priority, 0) + 1
        
        # Check hotspots
        city = "Chennai" if (11.0 < payload.get("latitude", 0) < 14.0) else "San Francisco"
        found_city = False
        for hs in analytics.setdefault("hotspots", []):
            if hs["city"].lower() == city.lower():
                hs["incidents_count"] += 1
                r_score = payload.get("risk", {}).get("risk_score", 50.0)
                hs["risk_score_avg"] = round((hs["risk_score_avg"] * (hs["incidents_count"] - 1) + r_score) / hs["incidents_count"], 1)
                found_city = True
                break
        if not found_city:
            analytics["hotspots"].append({
                "city": city,
                "coordinates": [payload.get("latitude"), payload.get("longitude")],
                "incidents_count": 1,
                "risk_score_avg": payload.get("risk", {}).get("risk_score", 50.0)
            })
            
        write_json_file(ANALYTICS_FILE, analytics)
        
    add_audit_log(
        event_type="INCIDENT_SUBMISSION",
        username=payload.get("username", "citizen"),
        details=f"Registered incident {incident_id} ({dtype}, Severity: {payload.get('detection', {}).get('severity')})"
    )
    
    return f"Incident successfully registered. ID: {incident_id}"

@mcp.tool()
def get_incident_registry() -> list:
    """Retrieves all registered incidents."""
    return read_json_file(INCIDENTS_FILE, [])

@mcp.tool()
def award_reward_points(username: str, points: int, severity: str, incident_id: str) -> dict:
    """
    Awards points to the citizen, creates transactions, updates badges, and rebuilds leaderboard.
    """
    users = read_json_file(USERS_FILE, [])
    rewards = read_json_file(REWARDS_FILE, [])
    
    target_user = None
    for u in users:
        if u["username"] == username:
            target_user = u
            break
            
    if not target_user:
        return {"status": "error", "message": f"User {username} not found."}
        
    # Award points
    old_points = target_user.get("points", 0)
    new_points = old_points + points
    target_user["points"] = new_points
    
    # Evaluate badge progression
    # Badges: Road Protector, Community Guardian, Infrastructure Hero, National Contributor
    current_badges = target_user.setdefault("badges", [])
    badge_earned = None
    
    if new_points >= 10 and "Road Protector" not in current_badges:
        current_badges.append("Road Protector")
        badge_earned = "Road Protector"
    if new_points >= 50 and "Community Guardian" not in current_badges:
        current_badges.append("Community Guardian")
        badge_earned = "Community Guardian"
    if new_points >= 120 and "Infrastructure Hero" not in current_badges:
        current_badges.append("Infrastructure Hero")
        badge_earned = "Infrastructure Hero"
    if new_points >= 200 and "National Contributor" not in current_badges:
        current_badges.append("National Contributor")
        badge_earned = "National Contributor"
        
    write_json_file(USERS_FILE, users)
    
    # Save transaction
    tx_id = f"TX-RG-{int(datetime.now(timezone.utc).timestamp()) % 100000:05d}-{len(rewards)}"
    new_tx = {
        "transaction_id": tx_id,
        "username": username,
        "incident_id": incident_id,
        "points": points,
        "reason": f"Points awarded for reporting road hazard (Severity: {severity})",
        "badge_earned": badge_earned,
        "created_at": datetime.now(timezone.utc).isoformat() + "Z"
    }
    rewards.append(new_tx)
    write_json_file(REWARDS_FILE, rewards)
    
    # Sync leaderboard
    sync_leaderboard()
    
    add_audit_log(
        event_type="REWARDS_AWARDED",
        username=username,
        details=f"Awarded {points} points for incident {incident_id}. New balance: {new_points}. Badge: {badge_earned}"
    )
    
    # Update Analytics distributed points
    analytics = read_json_file(ANALYTICS_FILE, {})
    if "summary" in analytics:
        analytics["summary"]["total_points_distributed"] = analytics["summary"].get("total_points_distributed", 0) + points
        write_json_file(ANALYTICS_FILE, analytics)
        
    return {
        "status": "success",
        "points_awarded": points,
        "new_balance": new_points,
        "badge_earned": badge_earned,
        "transaction_id": tx_id
    }

@mcp.tool()
def get_leaderboard() -> list:
    """Retrieves current citizen ranking leaderboard."""
    return read_json_file(LEADERBOARD_FILE, [])

@mcp.tool()
def detect_duplicate_reports(lat: float, lng: float, description: str) -> dict:
    """
    Checks if an incident is a duplicate based on location proximity (~150m) or high text similarity.
    """
    incidents = read_json_file(INCIDENTS_FILE, [])
    threshold_distance_meters = 150.0
    
    # 1. Geo proximity check
    for inc in incidents:
        dist = haversine_distance(lat, lng, inc.get("latitude", 0), inc.get("longitude", 0))
        if dist <= threshold_distance_meters:
            # Found geodetic collision
            return {
                "is_duplicate": True,
                "type": "proximity",
                "incident_id": inc["incident_id"],
                "distance_meters": round(dist, 1),
                "existing_description": inc["description"]
            }
            
    # 2. Text similarity check (simple word intersection ratio)
    desc_words = set(description.lower().split())
    for inc in incidents:
        inc_words = set(inc.get("description", "").lower().split())
        if not desc_words or not inc_words:
            continue
        intersection = desc_words.intersection(inc_words)
        union = desc_words.union(inc_words)
        similarity = len(intersection) / len(union)
        
        if similarity >= 0.70: # 70% word correlation
            return {
                "is_duplicate": True,
                "type": "text_similarity",
                "incident_id": inc["incident_id"],
                "similarity_score": round(similarity, 2),
                "existing_description": inc["description"]
            }
            
    return {
        "is_duplicate": False,
        "message": "No duplicates detected."
    }

@mcp.tool()
def generate_city_report(city: str) -> dict:
    """
    Generates statistics/hotspots and forecasting summaries for a specific city.
    """
    incidents = read_json_file(INCIDENTS_FILE, [])
    workorders = read_json_file(WORKORDERS_FILE, [])
    
    # Filter incidents belonging to city (mock coordinate bounding box)
    city_incidents = []
    for inc in incidents:
        lat = inc.get("latitude", 0)
        # Chennai: lat 12-14, lng 79-81
        if city.lower() == "chennai":
            if 12.0 <= lat <= 14.0:
                city_incidents.append(inc)
        # SF: lat 36-38, lng -123 to -121
        elif city.lower() == "san francisco":
            if 36.0 <= lat <= 38.0:
                city_incidents.append(inc)
        else:
            # Fallback check by word match
            if city.lower() in inc.get("description", "").lower():
                city_incidents.append(inc)
                
    if not city_incidents:
        # Generate clean mock return if no incidents in db matches
        return {
            "city": city,
            "total_incidents": 0,
            "resolved_count": 0,
            "pending_count": 0,
            "risk_score_average": 0.0,
            "hotspots": [],
            "recommendation": "No infrastructure hazards reported in this city yet. Ready for patrol."
        }
        
    resolved_count = len([i for i in city_incidents if i["status"] == "Resolved"])
    pending_count = len([i for i in city_incidents if i["status"] != "Resolved"])
    r_scores = [i.get("risk", {}).get("risk_score", 50) for i in city_incidents]
    r_avg = round(sum(r_scores) / len(r_scores), 1) if r_scores else 0.0
    
    # Count damage types
    type_counts = {}
    for inc in city_incidents:
        dtype = inc.get("detection", {}).get("damage_type", "Pothole")
        type_counts[dtype] = type_counts.get(dtype, 0) + 1
        
    # Recommendation reasoning
    recommendation = (
        f"Immediate focus should be given to resolving the {pending_count} active road hazards. "
        f"Critical issues represent the largest risk. Average safety risk score is at {r_avg}/100. "
        f"Recommend dispatching road patching teams to high-volume coordinate clusters."
    )
    
    return {
        "city": city,
        "total_incidents": len(city_incidents),
        "resolved_count": resolved_count,
        "pending_count": pending_count,
        "risk_score_average": r_avg,
        "damage_type_counts": type_counts,
        "recommendation": recommendation,
        "generated_at": datetime.now(timezone.utc).isoformat() + "Z"
    }

@mcp.tool()
def get_user_contribution_history(username: str) -> dict:
    """
    Returns user profile details, rewards history logs, and reported incidents.
    """
    users = read_json_file(USERS_FILE, [])
    rewards = read_json_file(REWARDS_FILE, [])
    incidents = read_json_file(INCIDENTS_FILE, [])
    
    target_user = None
    for u in users:
        if u["username"] == username:
            target_user = u.copy()
            break
            
    if not target_user:
        return {"error": f"User {username} not found."}
        
    # Remove password hash for safety
    if "password" in target_user:
        del target_user["password"]
        
    user_rewards = [r for r in rewards if r["username"] == username]
    user_reports = [inc for inc in incidents if inc.get("username") == username]
    
    target_user["rewards_history"] = user_rewards
    target_user["reports"] = [
        {
            "incident_id": inc["incident_id"],
            "description": inc["description"],
            "status": inc["status"],
            "severity": inc.get("detection", {}).get("severity", "Low"),
            "created_at": inc["created_at"]
        }
        for inc in user_reports
    ]
    
    return target_user

@mcp.tool()
def verify_report(description: str, latitude: float, longitude: float, image_url: str = "") -> dict:
    """
    Analyzes submission metadata (description, latitude, longitude, image_url) to verify authenticity.
    Checks for location realism, image spoofing indicators, and description completeness.
    """
    lat = latitude
    lng = longitude
    
    # 1. Location bounds validation (e.g. check if coordinates are valid)
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lng <= 180.0):
        return {
            "verified": False,
            "trust_score": 0.0,
            "fraud_score": 100.0,
            "status": "Flagged",
            "reason": "Invalid geographic coordinates (out of range)."
        }
        
    # 2. Check for empty or too short description
    if len(description.strip()) < 15:
        return {
            "verified": False,
            "trust_score": 30.0,
            "fraud_score": 70.0,
            "status": "Flagged",
            "reason": "Vague or extremely short hazard description. Insufficient detail."
        }
        
    # 3. Simulate image analysis if present
    trust_score = 95.0
    fraud_score = 5.0
    reason = "Report details verified successfully. Coordinates are consistent and description is detailed."
    
    if image_url:
        # Check for simulated dummy flags in URL
        if "fake" in image_url.lower() or "generate" in image_url.lower() or "ai" in image_url.lower():
            trust_score = 15.0
            fraud_score = 85.0
            reason = "Warning: AI-Generated/Manipulated metadata signature detected in photo."
        elif "stock" in image_url.lower():
            trust_score = 45.0
            fraud_score = 55.0
            reason = "Warning: Stock/Duplicate image database match detected. Image may not represent current location state."
            
    return {
        "verified": trust_score >= 50.0,
        "trust_score": trust_score,
        "fraud_score": fraud_score,
        "status": "Passed" if trust_score >= 50.0 else "Flagged",
        "reason": reason
    }

if __name__ == "__main__":
    mcp.run()
