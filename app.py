import os
import json
import asyncio
from flask import Flask, render_template, request, Response, jsonify
from agents import run_roadguard_pipeline

# Initialize Flask App with static and template directories mapped correctly
app = Flask(__name__, static_folder='static', template_folder='templates')

REGISTRY_FILE = "hazard_registry.json"

@app.route('/')
def index():
    """
    Renders the citizen reporting portal and public works dashboard.
    """
    return render_template('index.html')

@app.route('/api/incidents', methods=['GET'])
def get_incidents():
    """
    Fetches all registered hazards directly from our local database registry.
    """
    if not os.path.exists(REGISTRY_FILE):
        return jsonify([])
    try:
        with open(REGISTRY_FILE, "r") as f:
            data = json.load(f)
        # Return reversed to show newest incidents first
        return jsonify(list(reversed(data)))
    except Exception as e:
        return jsonify({"error": f"Failed to load registry: {str(e)}"}), 500

@app.route('/api/report', methods=['POST'])
def report_incident():
    """
    Accepts report details and starts the ADK workflow. 
    Streams agent trace events in real-time as Server-Sent Events (SSE).
    """
    data = request.json or {}
    description = data.get("description")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    image_url = data.get("image_url")
    
    # Validation
    if not description or latitude is None or longitude is None:
        return jsonify({"error": "Missing required fields: description, latitude, longitude"}), 400
        
    def sse_event_generator():
        # Create an isolated event loop for this thread's async generator execution
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Instantiate the asynchronous ADK workflow pipeline
            pipeline = run_roadguard_pipeline(description, float(latitude), float(longitude), image_url)
            
            while True:
                try:
                    # Fetch the next streamed token/chunk from the agent workflow
                    chunk = loop.run_until_complete(pipeline.__anext__())
                    yield f"data: {json.dumps(chunk)}\n\n"
                except StopAsyncIteration:
                    # Stream finished successfully
                    break
        except Exception as e:
            # Yield error event trace back to UI
            error_data = {"node": "error", "text": f"Agent Pipeline Exception: {str(e)}"}
            yield f"data: {json.dumps(error_data)}\n\n"
        finally:
            loop.close()
            
    return Response(sse_event_generator(), mimetype='text/event-stream')

if __name__ == "__main__":
    # Get port from environment or default to 5000
    port = int(os.environ.get("PORT", 5000))
    # Run the server locally on all interfaces
    app.run(host="0.0.0.0", port=port, debug=True)
