import os
import sys
import asyncio
import json

# Prevent UnicodeEncodeError on Windows terminals when printing emojis
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from typing import AsyncGenerator
from google.adk.agents.llm_agent import LlmAgent
from google.adk.workflow import Workflow
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp import StdioServerParameters
from google.genai import types

# Import tool functions from mcp_server.py for simulation mode
try:
    from mcp_server import (
        detect_duplicate_reports,
        verify_report,
        get_location_context,
        save_incident,
        award_reward_points,
        generate_city_report
    )
except ImportError:
    # Fallback in case of import path issues in some envs
    detect_duplicate_reports = None
    verify_report = None
    get_location_context = None
    save_incident = None
    award_reward_points = None
    generate_city_report = None

def is_valid_gemini_key() -> bool:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return False
    key_lower = key.lower().strip()
    placeholders = [
        "your_gemini_api_key_here",
        "your_key",
        "your_api_key_here",
        "your_api_key",
        "placeholder",
        "none",
        "null",
        ""
    ]
    if key_lower in placeholders or "your" in key_lower:
        return False
    if len(key) < 10:
        return False
    return True

# Safety Check for API Key
if not is_valid_gemini_key():
    print("WARNING: GEMINI_API_KEY environment variable is not set or is a placeholder. RoadGuard AI is running in high-fidelity SIMULATION MODE.")

# Define MCP connection params globally so we don't recreate the class overhead
mcp_tool = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=["mcp_server.py"],
            env=os.environ.copy()
        )
    )
)

async def run_simulated_roadguard_pipeline(username: str, description: str, lat: float, lng: float, image_url: str = None) -> AsyncGenerator[dict, None]:
    """
    Simulates the 7-agent pipeline execution when GEMINI_API_KEY is missing.
    Interacts directly with the MCP server database functions for state changes and rewards.
    """
    await asyncio.sleep(0.5)

    # ------------------ AGENT 5: FRAUDGUARD AGENT ------------------
    node = "fraudguard_agent"
    yield {"node": node, "text": "🔍 **FraudGuard Agent (Trust & Safety Officer)** starting verification...\n"}
    await asyncio.sleep(0.3)
    yield {"node": node, "text": f"Calling tool `detect_duplicate_reports(lat={lat:.5f}, lng={lng:.5f}, description='{description[:30]}...')`\n"}
    
    dup_res = detect_duplicate_reports(lat, lng, description) if detect_duplicate_reports else {"is_duplicate": False}
    await asyncio.sleep(0.4)
    yield {"node": node, "text": f"Tool Output: {json.dumps(dup_res)}\n"}
    
    if dup_res.get("is_duplicate"):
        await asyncio.sleep(0.3)
        yield {
            "node": node,
            "text": (
                f"\n🛑 **PROCESS HALTED: Incident flagged as duplicate**\n"
                f"- Detection Type: {dup_res.get('type')}\n"
                f"- Matching Incident ID: {dup_res.get('incident_id')}\n"
                f"- Distance: {dup_res.get('distance_meters', 0.0)}m\n"
                f"- Reasoning: Proximity checks indicate this hazard is already registered in the registry. "
                f"Halting pipeline to prevent municipal database pollution. Penalty: Warning issued."
            )
        }
        return

    img_url_str = image_url or ""
    yield {"node": node, "text": f"\nCalling tool `verify_report(description='...', latitude={lat}, longitude={lng}, image_url='{img_url_str}')`\n"}
    
    verify_res = verify_report(description, lat, lng, img_url_str) if verify_report else {"verified": True, "trust_score": 95.0, "fraud_score": 5.0, "status": "Passed", "reason": "Verified"}
    await asyncio.sleep(0.4)
    yield {"node": node, "text": f"Tool Output: {json.dumps(verify_res)}\n"}
    
    trust_score = verify_res.get("trust_score", 95.0)
    fraud_score = verify_res.get("fraud_score", 5.0)
    status = verify_res.get("status", "Passed")
    reason = verify_res.get("reason", "")

    if fraud_score >= 70 or trust_score <= 30:
        await asyncio.sleep(0.3)
        penalty = "Warning"
        if "AI-Generated" in reason:
            penalty = "Temporary Account Suspension"
        elif "Stock" in reason:
            penalty = "Points Deduction"
            
        yield {
            "node": node,
            "text": (
                f"\n🛑 **PROCESS HALTED: Incident flagged as fraudulent**\n"
                f"- Trust Score: {trust_score}/100\n"
                f"- Fraud Score: {fraud_score}/100\n"
                f"- Verification Status: {status}\n"
                f"- Reasoning: {reason}\n"
                f"- Penalty Applied: **{penalty}**"
            )
        }
        return

    await asyncio.sleep(0.3)
    yield {
        "node": node,
        "text": (
            f"\n✅ **Trust Evaluation Passed**\n"
            f"- Trust Score: {trust_score}/100\n"
            f"- Fraud Score: {fraud_score}/100\n"
            f"- Status: {status}\n"
            f"- Analysis: {reason}\n"
        )
    }
    await asyncio.sleep(0.5)

    # ------------------ AGENT 1: INFRASTRUCTURE DETECTION AGENT ------------------
    node = "road_damage_agent"
    yield {"node": node, "text": "🤖 **Infrastructure Detection Agent (AI Inspector)** starting analysis...\n"}
    await asyncio.sleep(0.4)
    yield {"node": node, "text": "Analyzing text characteristics and image pixel density...\n"}
    await asyncio.sleep(0.4)

    # Simple heuristic classification
    desc_lower = description.lower()
    if "crack" in desc_lower or "erosion" in desc_lower:
        damage_type = "Road Surface Crack"
        severity = "Medium"
        confidence = 0.89
    elif "sign" in desc_lower or "traffic light" in desc_lower:
        damage_type = "Obstructed/Missing Sign"
        severity = "High"
        confidence = 0.94
    elif "debris" in desc_lower or "trash" in desc_lower or "object" in desc_lower:
        damage_type = "Debris"
        severity = "Medium"
        confidence = 0.91
    elif "sinkhole" in desc_lower or "collapse" in desc_lower:
        damage_type = "Damaged Surface"
        severity = "Critical"
        confidence = 0.97
    else:
        damage_type = "Pothole"
        severity = "Critical" if ("pothole" in desc_lower and ("deep" in desc_lower or "danger" in desc_lower or "school" in desc_lower)) else "Medium"
        confidence = 0.96

    # Override severity based on explicit input keywords
    if "critical" in desc_lower or "danger" in desc_lower or "school" in desc_lower:
        severity = "Critical"
    elif "high" in desc_lower or "severe" in desc_lower:
        severity = "High"
    elif "low" in desc_lower or "minor" in desc_lower:
        severity = "Low"

    yield {
        "node": node,
        "text": (
            f"**Inspection Profile:**\n"
            f"- Damage Classification: **{damage_type}**\n"
            f"- Estimated Severity: **{severity}**\n"
            f"- Classifier Confidence: **{confidence:.2f}**\n\n"
            f"**Inspector Summary:** The report describes a {damage_type.lower()} of {severity.lower()} severity. "
            f"Surface degradation matches structural anomaly markers."
        )
    }
    await asyncio.sleep(0.5)

    # ------------------ AGENT 2: RISK ASSESSMENT AGENT ------------------
    node = "risk_assessment_agent"
    yield {"node": node, "text": "🚨 **Risk Assessment Agent (Public Safety Officer)** starting hazard risk scoring...\n"}
    await asyncio.sleep(0.3)
    yield {"node": node, "text": f"Calling tool `get_location_context(lat={lat:.5f}, lng={lng:.5f})`\n"}
    
    loc_res = get_location_context(lat, lng) if get_location_context else {
        "latitude": lat, "longitude": lng, "traffic_density": "Medium", "school_zone": False,
        "school_zone_distance_meters": 800, "hospital_zone": False, "road_classification": "Arterial City Road",
        "population_density": "Medium (Suburban)", "speed_limit_mph": 35
    }
    await asyncio.sleep(0.4)
    yield {"node": node, "text": f"Tool Output: {json.dumps(loc_res)}\n"}

    # Compute risk score
    base_scores = {"Low": 25, "Medium": 50, "High": 75, "Critical": 90}
    risk_score = base_scores.get(severity, 50)
    
    if loc_res.get("school_zone"):
        risk_score += 10
    if loc_res.get("hospital_zone"):
        risk_score += 5
    if loc_res.get("traffic_density") == "High":
        risk_score += 5
    elif loc_res.get("traffic_density") == "Low":
        risk_score -= 10
        
    risk_score = max(0, min(100, risk_score))
    
    # Priority
    if risk_score >= 80:
        priority = "Critical"
    elif risk_score >= 60:
        priority = "High"
    elif risk_score >= 40:
        priority = "Medium"
    else:
        priority = "Low"

    school_dist = loc_res.get("school_zone_distance_meters", 800)
    hospital_dist = loc_res.get("hospital_zone_distance_meters", 1500)
    road_class = loc_res.get("road_classification", "Local Road")
    traffic = loc_res.get("traffic_density", "Medium")

    yield {
        "node": node,
        "text": (
            f"\n**Risk Assessment Report:**\n"
            f"- Public Safety Risk Index: **{risk_score}/100**\n"
            f"- Action Priority Level: **{priority}**\n"
            f"- Risk Explanation: Hazard is situated on a {road_class} with {traffic} traffic volume. "
            f"Proximity context: School Zone = {loc_res.get('school_zone')} ({school_dist:.1f}m), "
            f"Hospital Zone = {loc_res.get('hospital_zone')} ({hospital_dist:.1f}m). "
            f"Compounding risk factor rating: {priority.upper()}."
        )
    }
    await asyncio.sleep(0.5)

    # ------------------ AGENT 3: REPAIR RECOMMENDATION AGENT ------------------
    node = "repair_recommendation_agent"
    yield {"node": node, "text": "👷 **Repair Recommendation Agent (Civil Engineering Consultant)** starting design...\n"}
    await asyncio.sleep(0.4)
    yield {"node": node, "text": "Formulating structural repair plan & estimating costs...\n"}
    await asyncio.sleep(0.4)

    # Determine repair plan details
    if damage_type == "Road Surface Crack":
        method = "Clean cracks with high-pressure air, apply hot pour rubberized crack sealant to prevent water ingress."
        cost = 150.0
        timeline = "3 hours"
        materials = ["Rubberized Crack Sealant", "Compressed Air Cleansing"]
        labor = "2-person maintenance crew"
    elif damage_type == "Obstructed/Missing Sign":
        method = "Trim overlapping tree branches, replace sign panel with high-grade reflective signage."
        cost = 200.0
        timeline = "2 hours"
        materials = ["Standard Reflective STOP Sign", "Metal Post & Bolts", "Pruning Tools"]
        labor = "2-person technician crew"
    elif damage_type == "Debris":
        method = "Dispatch sweeping truck and safety crew to clear road hazards."
        cost = 100.0
        timeline = "1 hour"
        materials = ["Safety Barricades"]
        labor = "2-person sweep crew"
    else: # Pothole
        method = "Excavate standing water, clean loose debris, backfill with compacted aggregate base, apply hot-mix asphalt (HMA) patch, compact and seal joints."
        cost = 450.0 if priority == "Critical" else 300.0
        timeline = "4 hours"
        materials = ["Asphalt Mix", "Base Aggregate", "Tack Coat Sealant"]
        labor = "3-person road patching crew"

    materials_str = ", ".join(materials)
    yield {
        "node": node,
        "text": (
            f"**Structural Repair Plan:**\n"
            f"- Recommended Method: **{method}**\n"
            f"- Cost Estimate: **${cost:.2f} USD**\n"
            f"- Timeline: **{timeline}**\n"
            f"- Labor Allocation: **{labor}**\n"
            f"- Material List: **{materials_str}**"
        )
    }
    await asyncio.sleep(0.5)

    # ------------------ AGENT 4: GOVERNMENT ASSISTANCE AGENT ------------------
    node = "government_assistance_agent"
    yield {"node": node, "text": "🏢 **Government Assistance Agent (Public Works Coordinator)** starting coordination...\n"}
    await asyncio.sleep(0.3)
    
    # Assign department
    if lat > 30.0: # SF bounding box
        if damage_type == "Obstructed/Missing Sign":
            department = "SFMTA Traffic Signage Division"
        elif damage_type == "Debris":
            department = "SF Public Works Debris Team"
        else:
            department = "SF Road Maintenance Division"
    else: # Chennai bounding box
        if damage_type == "Obstructed/Missing Sign":
            department = "Traffic Control Signage Division"
        elif damage_type == "Debris":
            department = "Emergency Response Team"
        else:
            department = "Chennai Corporation Road Maintenance"

    yield {"node": node, "text": f"Calling tool `save_incident(payload)`...\n"}
    
    payload = {
        "username": username,
        "description": description,
        "latitude": lat,
        "longitude": lng,
        "image_url": image_url,
        "status": "Open",
        "fraud_guard": {
            "trust_score": trust_score,
            "fraud_score": fraud_score,
            "status": "Passed",
            "reasoning": reason
        },
        "detection": {
            "damage_type": damage_type,
            "severity": severity,
            "confidence": confidence,
            "summary": f"Identified {damage_type.lower()} of {severity.lower()} severity."
        },
        "risk": {
            "risk_score": risk_score,
            "priority": priority,
            "explanation": f"Located on {road_class} in area with {traffic} traffic. Proximity to safety zone is critical."
        },
        "repair": {
            "recommendation": method,
            "budget": cost,
            "timeline": timeline,
            "materials": materials,
            "labor": labor
        },
        "government": {
            "assigned_department": department,
            "summary": f"Automatically generated municipal work order for dispatching {department}."
        }
    }
    
    save_str = save_incident(payload) if save_incident else "Incident successfully registered. ID: HZ-RG-11005"
    await asyncio.sleep(0.4)
    yield {"node": node, "text": f"Tool Output: {save_str}\n"}
    
    # Extract incident ID
    incident_id = save_str.split("ID: ")[-1] if "ID: " in save_str else f"HZ-RG-{int(asyncio.get_event_loop().time()) % 100000}"
    suffix = incident_id.split("-")[-1]
    work_order_id = f"WO-RG-{suffix}"

    yield {
        "node": node,
        "text": (
            f"\n**Municipal Operations Dispatch:**\n"
            f"- Registered Incident ID: **{incident_id}**\n"
            f"- Work Order ID: **{work_order_id}**\n"
            f"- Assigned Department: **{department}**\n"
            f"- Government Report Summary: Dispatch system has successfully registered incident **{incident_id}** and compiled work order **{work_order_id}**. Budget authorization completed."
        )
    }
    await asyncio.sleep(0.5)

    # ------------------ AGENT 6: CIVIC REWARDS AGENT ------------------
    node = "civic_rewards_agent"
    yield {"node": node, "text": "🏆 **Civic Rewards Agent (Citizen Contribution Evaluator)** starting evaluation...\n"}
    await asyncio.sleep(0.3)
    
    points_map = {"Low": 10, "Medium": 25, "High": 50, "Critical": 100}
    points = points_map.get(severity, 10)
    
    yield {"node": node, "text": f"Calling tool `award_reward_points(username='{username}', points={points}, severity='{severity}', incident_id='{incident_id}')`...\n"}
    
    reward_res = award_reward_points(username, points, severity, incident_id) if award_reward_points else {
        "status": "success", "points_awarded": points, "new_balance": 310, "badge_earned": "National Contributor", "transaction_id": f"TX-RG-{suffix}"
    }
    await asyncio.sleep(0.4)
    yield {"node": node, "text": f"Tool Output: {json.dumps(reward_res)}\n"}

    new_balance = reward_res.get("new_balance", 210)
    badge = reward_res.get("badge_earned")
    badge_str = f"earned new badge: **{badge}** 🏅" if badge else "no new badge earned."
    tx_id = reward_res.get("transaction_id", f"TX-RG-{suffix}")

    yield {
        "node": node,
        "text": (
            f"\n**Citizen Rewards Calculation:**\n"
            f"- Contribution Reputation Score: **+{points} points**\n"
            f"- New Points Balance: **{new_balance} points**\n"
            f"- Achievement Badges: {badge_str}\n"
            f"- Transaction ID: **{tx_id}**\n"
            f"- Summary: Citizen rewards database updated successfully. Thank you for making our roads safer!"
        )
    }
    await asyncio.sleep(0.5)

    # ------------------ AGENT 7: INFRASTRUCTURE INTELLIGENCE AGENT ------------------
    node = "infrastructure_intelligence_agent"
    yield {"node": node, "text": "📊 **Infrastructure Intelligence Agent (National Infrastructure Analyst)** starting final analysis...\n"}
    await asyncio.sleep(0.3)
    
    city = "Chennai" if lat < 30.0 else "San Francisco"
    yield {"node": node, "text": f"Calling tool `generate_city_report(city='{city}')`...\n"}
    
    report_res = generate_city_report(city) if generate_city_report else {
        "city": city, "total_incidents": 3, "resolved_count": 1, "pending_count": 2,
        "risk_score_average": 72.5, "recommendation": "Patch roads immediately."
    }
    await asyncio.sleep(0.4)
    yield {"node": node, "text": f"Tool Output: {json.dumps(report_res)}\n"}

    r_avg = report_res.get("risk_score_average", 72.5)
    total_reports = report_res.get("total_incidents", 3)
    rec_text = report_res.get("recommendation", "")

    yield {
        "node": node,
        "text": (
            f"\n**Regional Infrastructure Intel Summary:**\n"
            f"- Target Division: **{city}**\n"
            f"- Total Reports Tracked: **{total_reports}**\n"
            f"- Safety Risk Average: **{r_avg}/100**\n"
            f"- Strategic Maintenance Insights: {rec_text}\n"
            f"- Infrastructure Forecast: High probability of sub-grade damage in hotspot coordinate clusters during rainy seasons. Proactive preventative sealing recommended."
        )
    }
    await asyncio.sleep(0.2)


async def run_roadguard_pipeline(username: str, description: str, lat: float, lng: float, image_url: str = None) -> AsyncGenerator[dict, None]:
    """
    Runs the RoadGuard AI 7-agent sequential workflow and yields streamed trace updates.
    Falls back to high-fidelity simulation mode if GEMINI_API_KEY is not set.
    """
    if not is_valid_gemini_key():
        async for chunk in run_simulated_roadguard_pipeline(username, description, lat, lng, image_url):
            yield chunk
        return

    # Real LLM ADK workflow runs here
    # Agent 5: FraudGuard Agent (Trust & Safety Officer)
    fraud_agent = LlmAgent(
        name="fraudguard_agent",
        model="gemini-2.5-flash",
        instruction=(
            "You are the FraudGuard Agent (Trust and Safety Officer) for CivicGuard AI.\n"
            "Your job is to analyze the incoming citizen report coordinates and details.\n"
            "You MUST call the `detect_duplicate_reports` tool with the latitude, longitude, and description to check for duplicates.\n"
            "You MUST call the `verify_report` tool with the description, latitude, longitude, and image_url to assess legitimacy.\n"
            "Synthesize these findings and output a clear trust evaluation containing:\n"
            "- Trust Score (0 to 100)\n"
            "- Fraud Score (0 to 100)\n"
            "- Verification Status (Passed or Flagged)\n"
            "- Reasoning Summary: explanation of potential fraud or duplicity.\n"
            "If the report is a Duplicate, False Report, or AI Generated, specify the penalty:\n"
            "- Duplicate Report -> Warning\n"
            "- Misleading Description -> Point Deduction\n"
            "- Fake Incident -> Account Restriction\n"
            "- AI Generated Fake Image -> Account Suspension\n"
            "If Fraud Score >= 70 or trust score <= 30, output 'PROCESS HALTED: Incident flagged as fraudulent' in your text."
        ),
        tools=[mcp_tool]
    )

    # Agent 1: Infrastructure Detection Agent (AI Infrastructure Inspector)
    damage_agent = LlmAgent(
        name="road_damage_agent",
        model="gemini-2.5-flash",
        instruction=(
            "You are the Infrastructure Detection Agent (AI Infrastructure Inspector).\n"
            "Review the report details. If the previous agent (FraudGuard) outputted 'PROCESS HALTED', "
            "then print 'PROCESS HALTED: Incident flagged as fraudulent' and skip all detection work.\n"
            "Otherwise, analyze the description and image metadata. Classify the hazard under one of these types:\n"
            "- Pothole\n"
            "- Road Surface Crack\n"
            "- Obstructed/Missing Sign\n"
            "- Damaged Surface\n"
            "- Debris\n"
            "Estimate severity (Low, Medium, High, Critical), Confidence Score (0.0 to 1.0), and provide a brief Inspection Summary."
        )
    )

    # Agent 2: Risk Assessment Agent (Public Safety Officer)
    risk_agent = LlmAgent(
        name="risk_assessment_agent",
        model="gemini-2.5-flash",
        instruction=(
            "You are the Risk Assessment Agent (Public Safety Officer).\n"
            "If the process was halted due to fraud, skip and print 'PROCESS HALTED: Incident flagged as fraudulent'.\n"
            "Otherwise, you MUST call the `get_location_context` tool with the latitude and longitude from the report.\n"
            "Determine the risk score (0-100) and Priority Level (Low, Medium, High, Critical) based on coordinates, severity, and speed limits/school zone proximity.\n"
            "Output the Risk Score, Priority Level, and a Risk Explanation detailing how the location context factors compound the hazard."
        ),
        tools=[mcp_tool]
    )

    # Agent 3: Repair Recommendation Agent (Civil Engineering Consultant)
    repair_agent = LlmAgent(
        name="repair_recommendation_agent",
        model="gemini-2.5-flash",
        instruction=(
            "You are the Repair Recommendation Agent (Civil Engineering Consultant).\n"
            "If the process was halted due to fraud, skip and print 'PROCESS HALTED: Incident flagged as fraudulent'.\n"
            "Based on the damage type, severity, and risk assessment, generate a structural repair plan.\n"
            "Specify:\n"
            "- Repair Recommendation: recommended repair method\n"
            "- Cost Estimate (in USD)\n"
            "- Timeline: estimated hours or days to complete\n"
            "- Resource Requirements: material types and crew size"
        )
    )

    # Agent 4: Government Assistance Agent (Public Works Coordinator)
    gov_agent = LlmAgent(
        name="government_assistance_agent",
        model="gemini-2.5-flash",
        instruction=(
            "You are the Government Assistance Agent (Public Works Coordinator).\n"
            "If the process was halted due to fraud, skip and print 'PROCESS HALTED: Incident flagged as fraudulent'.\n"
            "Synthesize all details from previous agents. Assign a public works department (e.g. 'Chennai Corporation Road Maintenance', 'Traffic Control Signage Division', or 'Emergency Response Team').\n"
            "You MUST call the `save_incident` tool with a payload containing:\n"
            "  - username: the citizen username\n"
            "  - description: description text\n"
            "  - latitude: float latitude\n"
            "  - longitude: float longitude\n"
            "  - image_url: image URL\n"
            "  - fraud_guard: {trust_score, fraud_score, status, reasoning}\n"
            "  - detection: {damage_type, severity, confidence, summary}\n"
            "  - risk: {risk_score, priority, explanation}\n"
            "  - repair: {recommendation, budget, timeline, materials, labor}\n"
            "  - government: {assigned_department, summary}\n"
            "Output the returned Incident ID, Work Order ID, assigned department, and a brief Government Summary."
        ),
        tools=[mcp_tool]
    )

    # Agent 6: Civic Rewards Agent (Citizen Contribution Evaluator)
    reward_agent = LlmAgent(
        name="civic_rewards_agent",
        model="gemini-2.5-flash",
        instruction=(
            "You are the Civic Rewards Agent (Citizen Contribution Evaluator).\n"
            "If the report was halted due to fraud, output the penalty applied and skip rewarding. "
            "For example: 'FRAUD DETECTED: Deducting points / restricting user'.\n"
            "Otherwise, evaluate the contribution. Calculate points to award based on severity:\n"
            "- Low Severity: 10 Points\n"
            "- Medium Severity: 25 Points\n"
            "- High Severity: 50 Points\n"
            "- Critical Hazard: 100 Points\n"
            "You MUST call the `award_reward_points` tool passing the citizen's username, points, severity, and the incident ID from the previous agent.\n"
            "Output: Points Awarded, Badge Earned (if any), and current Contribution Level."
        ),
        tools=[mcp_tool]
    )

    # Agent 7: Infrastructure Intelligence Agent (National Infrastructure Analyst)
    intel_agent = LlmAgent(
        name="infrastructure_intelligence_agent",
        model="gemini-2.5-flash",
        instruction=(
            "You are the Infrastructure Intelligence Agent (National Infrastructure Analyst).\n"
            "If the report was flagged as fraud, output 'PROCESS HALTED: Incident flagged as fraudulent' and skip.\n"
            "Otherwise, query the city status by calling `generate_city_report` tool with the appropriate city (e.g. 'Chennai' or 'San Francisco') depending on coordinates (lat ~13 is Chennai, lat ~37 is San Francisco).\n"
            "Provide the AI Generated Analytics Report summary, Risk Summary, Maintenance Insights, and Forecasts."
        ),
        tools=[mcp_tool]
    )

    # Rebuild the sequential ADK workflow graph
    workflow = Workflow(
        name="roadguard_workflow",
        edges=[
            ("START", fraud_agent, damage_agent, risk_agent, repair_agent, gov_agent, reward_agent, intel_agent)
        ]
    )

    session_service = InMemorySessionService()
    runner = Runner(agent=workflow, app_name="roadguard_app", session_service=session_service)
    session = await session_service.create_session(app_name="roadguard_app", user_id="citizen")
    
    input_text = (
        f"Citizen Infrastructure Report:\n"
        f"Username: {username}\n"
        f"Description: {description}\n"
        f"Location: Latitude {lat}, Longitude {lng}"
    )
    if image_url:
        input_text += f"\nImage URL: {image_url}"
        
    user_message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=input_text)]
    )
    
    try:
        async for event in runner.run_async(
            user_id=session.user_id,
            session_id=session.id,
            new_message=user_message
        ):
            node_name = "orchestrator"
            if event.node_info and event.node_info.name:
                node_name = event.node_info.name
            
            if event.content and event.content.parts:
                text_parts = [p.text for p in event.content.parts if p.text]
                if text_parts:
                    text = "".join(text_parts)
                    yield {"node": node_name, "text": text}
    finally:
        await runner.close()

async def run_direct_intelligence_query(city: str) -> str:
    """
    Directly query the Infrastructure Intelligence Agent to generate a report for a specific city.
    """
    if not is_valid_gemini_key():
        # Simulated markdown report generated dynamically from incidents.json database stats
        res = generate_city_report(city) if generate_city_report else {
            "city": city, "total_incidents": 3, "resolved_count": 1, "pending_count": 2,
            "risk_score_average": 72.5, "recommendation": "Patch roads immediately."
        }
        
        r_avg = res.get("risk_score_average", 72.5)
        total_reports = res.get("total_incidents", 3)
        resolved = res.get("resolved_count", 1)
        pending = res.get("pending_count", 2)
        rec = res.get("recommendation", "")
        
        m_trends = (
            f"| Metric | Value |\n"
            f"|---|---|\n"
            f"| City Division | **{city}** |\n"
            f"| Total Incidents Registered | {total_reports} |\n"
            f"| Municipal Resolutions Completed | {resolved} |\n"
            f"| Active Hazards Queue | {pending} |\n"
            f"| Average Infrastructure Safety Risk | **{r_avg}/100** |\n"
        )
        
        md_output = (
            f"# 📊 INFRASTRUCTURE INTELLIGENCE ANALYTICS: {city.upper()}\n"
            f"**Generated by:** `Infrastructure Intelligence Agent (National Analyst)`\n"
            f"**Data Gateway:** MCP Registry Server Connection (`FastMCP`)\n"
            f"**Status:** Running in simulated fallback mode (GEMINI_API_KEY missing)\n\n"
            f"## 1. Executive Summary\n"
            f"A comprehensive diagnostic check was run on the geodetic registry for the city of **{city}**. "
            f"The active municipal service logs track the following parameters:\n\n"
            f"{m_trends}\n\n"
            f"## 2. Maintenance Insights\n"
            f"- {rec}\n"
            f"- Priority dispatching is centered around high-traffic zones and safety-sensitive areas (e.g. school crossings, hospital roads).\n\n"
            f"## 3. Infrastructure Risk Forecasts\n"
            f"- **Erosion Rating:** Moderate-High. Periodic rain cycles combined with subgrade soil shift will likely accelerate pavement cracking.\n"
            f"- **Preventative Strategy:** Recommending rubberized crack sealant overlays on arterial roads (such as Anna Salai Road) to prevent water filtration and stop pothole proliferation before the monsoon season.\n"
            f"- **Resource Forecast:** Budget reserves are sufficient for scheduled patching dispatches, but a 15% increase in crew allocations is recommended to reduce response lag from 48 hours to 24 hours."
        )
        return md_output

    intel_agent = LlmAgent(
        name="infrastructure_intelligence_agent",
        model="gemini-2.5-flash",
        instruction=(
            "You are the Infrastructure Intelligence Agent (National Infrastructure Analyst).\n"
            "The user wants a city infrastructure intelligence report.\n"
            "You MUST call the `generate_city_report` tool with the requested city name (e.g. 'Chennai' or 'San Francisco').\n"
            "Synthesize the data returned from the tool and write an analytical report including:\n"
            "1. City Name & Date\n"
            "2. Total, Resolved, and Pending Incident Counts\n"
            "3. Average Safety Risk Score\n"
            "4. Main Damage Categories identified\n"
            "5. Strategic Maintenance Insights & Infrastructure Risk Forecasts."
        ),
        tools=[mcp_tool]
    )
    
    session_service = InMemorySessionService()
    runner = Runner(agent=intel_agent, app_name="roadguard_app", session_service=session_service)
    session = await session_service.create_session(app_name="roadguard_app", user_id="admin")
    
    user_message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=f"Generate {city} Infrastructure Report")]
    )
    
    response_text = ""
    try:
        async for event in runner.run_async(
            user_id=session.user_id,
            session_id=session.id,
            new_message=user_message
        ):
            if event.content and event.content.parts:
                text_parts = [p.text for p in event.content.parts if p.text]
                if text_parts:
                    response_text += "".join(text_parts)
        return response_text
    finally:
        await runner.close()

if __name__ == "__main__":
    async def main():
        print("Testing direct city intelligence query...")
        report = await run_direct_intelligence_query("Chennai")
        print("\n=== CHENNAI REPORT ===")
        print(report)
        
        print("\nTesting sequential pipeline with a mock incident...")
        mock_user = "citizen_lokesh"
        mock_desc = "Massive pothole causing cars to swerve on Velachery Main Road."
        mock_lat = 12.9784
        mock_lng = 80.2184
        
        async for update in run_roadguard_pipeline(mock_user, mock_desc, mock_lat, mock_lng):
            print(f"\n[{update['node'].upper()}]: {update['text']}")
            
    asyncio.run(main())
