import os
import sys
import asyncio
from typing import AsyncGenerator
from google.adk.agents.llm_agent import LlmAgent
from google.adk.workflow import Workflow
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp import StdioServerParameters
from google.genai import types

# Safety Check for API Key
if not os.environ.get("GEMINI_API_KEY"):
    print("WARNING: GEMINI_API_KEY environment variable is not set. Please set it before running the agent pipeline.")

# 1. Initialize MCP toolset connection
# We use sys.executable to run mcp_server.py in the same python environment
mcp_tool = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=["mcp_server.py"],
            env=os.environ.copy()
        )
    )
)

# 2. Define the Road Damage Detection Agent
damage_agent = LlmAgent(
    name="road_damage_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are the Road Damage Detection Agent. Your job is to parse incoming citizen report descriptions "
        "and any image data metadata. Estimate the road damage type (e.g., pothole, structural crack, "
        "road erosion, debris, sinkhole) and severity (Low, Medium, High). Provide a structured "
        "response summarizing the identified type and severity, followed by a brief reasoning."
    )
)

# 3. Define the Risk Assessment Agent (Calls MCP tool: get_location_context)
risk_agent = LlmAgent(
    name="risk_assessment_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are the Risk Assessment Agent. Your job is to determine the hazard risk score (0-100) "
        "of the road damage. You MUST call the `get_location_context` tool by passing the latitude "
        "and longitude from the report to check traffic volume and school-zone status. "
        "Calculate the risk score as follows:\n"
        "- Baseline: 20\n"
        "- Traffic Proximity: Low (+5), Medium (+15), High (+30)\n"
        "- School Zone: True (+35), False (+0)\n"
        "- Severity: Low (+5), Medium (+15), High (+35)\n"
        "Explain your calculation breakdown step-by-step and output the final numeric risk score clearly."
    ),
    tools=[mcp_tool]
)

# 4. Define the Repair Recommendation Agent
repair_agent = LlmAgent(
    name="repair_recommendation_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are the Repair Recommendation Agent. Your job is to suggest the most appropriate repair "
        "materials, estimated repair time (in hours), and a realistic budget. Base your recommendation "
        "on the damage type, severity, and risk score identified in previous turns. Explain the rationale "
        "for the selected materials and budget."
    )
)

# 5. Define the Government Assistance Agent (Calls MCP tool: save_hazard_incident)
gov_agent = LlmAgent(
    name="government_assistance_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are the Government Assistance Agent. Your job is to synthesize all previous findings "
        "(damage details, risk score, repair recommendations) into a professional notification summary for "
        "public works. You MUST determine a Priority Level (Low, Medium, High, Critical) based on the risk score:\n"
        "- 0-30: Low\n"
        "- 31-60: Medium\n"
        "- 61-80: High\n"
        "- 81-100: Critical\n"
        "Finally, you MUST call the `save_hazard_incident` tool to register this incident in the public works registry, "
        "passing all details (damage_type, severity, risk_score, repair_materials, budget, priority). "
        "Confirm the registry database ID back to the user."
    ),
    tools=[mcp_tool]
)

# 6. Chain the agents in a sequential Graph Workflow
# In ADK, edges represent the workflow path from START to each node
workflow = Workflow(
    name="roadguard_workflow",
    edges=[
        ("START", damage_agent, risk_agent, repair_agent, gov_agent)
    ]
)

async def run_roadguard_pipeline(description: str, lat: float, lng: float, image_url: str = None) -> AsyncGenerator[dict, None]:
    """
    Runs the RoadGuard AI agentic workflow sequentially and yields streamed outputs for each agent.
    """
    session_service = InMemorySessionService()
    runner = Runner(agent=workflow, session_service=session_service)
    
    session = await session_service.create_session(app_name="roadguard_app", user_id="citizen")
    
    # Structure the report input
    input_text = (
        f"Citizen Report of Road Damage:\n"
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
            # Inspect the node generating the event and extract its text
            node_name = event.name or "orchestrator"
            
            # Check for content and yield text chunks in real-time
            if event.content and event.content.parts:
                text_parts = [p.text for p in event.content.parts if p.text]
                if text_parts:
                    text = "".join(text_parts)
                    yield {"node": node_name, "text": text}
    finally:
        # Gracefully shut down the runner and release stdio connections to MCP
        await runner.close()

if __name__ == "__main__":
    # Standard CLI test loop
    async def main():
        print("Testing RoadGuard AI workflow local CLI...")
        mock_desc = "Deep pothole right near the front gate of the Oakwood School, causing cars to swerve."
        mock_lat = 37.7749
        mock_lng = -122.4194
        
        async for update in run_roadguard_pipeline(mock_desc, mock_lat, mock_lng):
            print(f"\n[{update['node'].upper()}]: {update['text']}")
            
    if os.environ.get("GEMINI_API_KEY"):
        asyncio.run(main())
    else:
        print("Set GEMINI_API_KEY env variable to run this script directly.")
