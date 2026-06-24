import json
import os
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server
mcp = FastMCP("RoadGuard Registry Server")

# File path for the local mock database registry
REGISTRY_FILE = "hazard_registry.json"

@mcp.tool()
def get_location_context(lat: float, lng: float) -> dict:
    """
    Fetch simulated traffic volume and school-zone proximity context for a latitude and longitude.
    
    Args:
        lat: Latitude coordinate of the incident.
        lng: Longitude coordinate of the incident.
    
    Returns:
        A dictionary containing simulated location variables: traffic_density, school_zone, etc.
    """
    # Deterministic simulation based on coordinates to make testing consistent
    hash_val = abs(hash((lat, lng)))
    
    # 1. Traffic density simulation
    traffic_options = ["Low", "Medium", "High"]
    traffic_density = traffic_options[hash_val % len(traffic_options)]
    
    # 2. School zone proximity simulation
    school_zone = (hash_val % 2 == 0)
    school_zone_distance = 120.5 if school_zone else 750.0  # meters
    
    # 3. Speed limit simulation
    speed_limit = 20 if school_zone else 45
    
    return {
        "latitude": lat,
        "longitude": lng,
        "traffic_density": traffic_density,
        "school_zone": school_zone,
        "school_zone_distance_meters": school_zone_distance,
        "speed_limit_mph": speed_limit,
        "queried_at": datetime.utcnow().isoformat() + "Z"
    }

@mcp.tool()
def save_hazard_incident(payload: dict) -> str:
    """
    Saves a verified hazard incident to the local JSON database registry.
    
    Args:
        payload: Incident details dictionary including damage_type, severity, risk_score, 
                 repair_recommendations, and government priority details.
                 
    Returns:
        A success string confirmation including the assigned incident registry ID.
    """
    # Generate unique registry ID
    incident_id = f"HZ-RG-{int(datetime.now().timestamp()) % 100000:05d}"
    payload["incident_id"] = incident_id
    payload["saved_at"] = datetime.utcnow().isoformat() + "Z"
    
    # Read existing data safely
    data = []
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = []
            
    # Append the new hazard incident
    data.append(payload)
    
    # Save back to file
    try:
        with open(REGISTRY_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return f"Incident successfully registered. ID: {incident_id}"
    except Exception as e:
        return f"Error registering incident: {str(e)}"

@mcp.tool()
def get_hazard_registry() -> list:
    """
    Retrieves all registered hazard incidents from the database registry.
    
    Returns:
        A list of all registered hazard incident dictionaries.
    """
    if not os.path.exists(REGISTRY_FILE):
        return []
    try:
        with open(REGISTRY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

if __name__ == "__main__":
    # Start the server using the default stdio transport for local agent connections
    mcp.run()
