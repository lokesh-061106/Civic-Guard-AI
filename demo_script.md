# CivicGuard AI: 5-Minute Capstone Video Demo Script

This script coordinates your presentation narration with dashboard visuals to maximize scores in the **Pitch (30%)** and **Implementation (70%)** categories.

---

## ⏱️ Video Timeline Overview
- **0:00 - 0:45:** The Problem & The Solution
- **0:45 - 1:30:** Multi-Agent Architecture & MCP
- **1:30 - 3:00:** Live Demo: Citizen Submission & Real-time Stream
- **3:00 - 4:00:** Live Demo: FraudGuard Penalties & Government Dispatch
- **4:00 - 4:30:** Analytics, Auditing & Future Scope
- **4:30 - 5:00:** Outro & Call to Action

---

## 🎤 Script Detail

### Section 1: The Problem & The Solution (0:00 - 0:45)
- **Visuals:** Show the Landing Page of **CivicGuard AI**. Scroll through the metrics grid showing *Hazards Resolved*, *Points Awarded*, and *Active Patrol Citizens*. Hover over the Advanced Agentic Operations panel.
- **Narrator Speech:**
  > *"Every day, public infrastructure hazards like potholes, broken signage, and debris go unresolved because municipal reporting systems are disjointed and slow. Citizens don't know how to file actionable reports, and public works divisions struggle to prioritize repairs. More importantly, systems are vulnerable to duplicate submissions and fraud.*
  >
  > *Introducing **CivicGuard AI**, a citizen-powered infrastructure intelligence platform. Built for the Kaggle × Google AI Agents track, it leverages Google ADK multi-agent workflows, FastMCP database integration, and Gemini generative AI to transform user reports into immediate municipal action. Let's see how it works under the hood."*

### Section 2: Architecture & MCP (0:45 - 1:30)
- **Visuals:** Zoom into the System Architecture Diagram in the Landing Page view. Point out the Flask SSE Router, the 7 ADK Agents (FraudGuard, Inspector, Safety Officer, Consultant, Coordinator, Evaluator, Analyst), and the FastMCP database gateway.
- **Narrator Speech:**
  > *"The architecture is clean and robust. CivicGuard is built with a Flask API that handles JWT authentication and streams execution traces via Server-Sent Events. When a report is filed, it triggers a sequential graph of 7 specialized Google ADK agents.*
  >
  > *A core part of the system is the Model Context Protocol (MCP) server, implemented using FastMCP. The agents do not write directly to the database; instead, they call registered MCP tools to fetch location contexts, run geospatial duplicate scans, verify photo metadata, log security audit trails, and calculate rewards. This decouples our database layer, allowing seamless future migration to enterprise systems like MongoDB."*

### Section 3: Live Demo: Submission & Observability (1:30 - 3:00)
- **Visuals:** Go to the **File a Report** tab. Select the **School Zone Pothole** scenario preset. Explain the parameters (Deep pothole, near a school crossing, image URL). Click **Launch Multi-Agent Pipeline**. Watch the timeline switch to the **Agent Monitor** tab and start streaming results in real time.
- **Narrator Speech:**
  > *"Let's see it in action. We'll load our School Zone Pothole scenario preset and launch the pipeline. The app shifts to our real-time multi-agent observability dashboard. Here, Server-Sent Events stream the reasoning chain live.*
  >
  > *First, the **FraudGuard Agent** executes: it runs a geospatial duplicate search and checks our image metadata. It passes verification with a 95% trust score. Next, the **AI Inspector** parses the description, classifying it as a Pothole with Critical severity.*
  >
  > *The **Safety Officer Agent** then queries the location context tool. It detects the coordinates are in a high-traffic zone just 120 meters from a school, compounding the risk score to 90 out of 100. The **Civil Engineering Consultant** proposes a structural repair plan, estimating a $450 budget. The **Public Works Coordinator** then calls `save_incident` through the MCP tool, generating a work order and assigning it to the Chennai Corporation Road Maintenance. Finally, the **Civic Rewards Agent** awards 100 points to Lokesh, granting him the 'National Contributor' badge!"*

### Section 4: FraudGuard Penalties & Government Dispatch (3:00 - 4:00)
- **Visuals:** Go back to the report submission page. Select the **Duplicate Submission** scenario and submit. Show the timeline immediately halting at Agent 5 (FraudGuard) with the warning. Repeat for the **AI Generated Fake Image** scenario, showing the account restriction. Show the **Government Desk** tab, select the first work order, and update the status to "In Progress".
- **Narrator Speech:**
  > *"CivicGuard is built for real-world resilience. If a user submits a report for a hazard that is already registered, FraudGuard catches the duplicate within 150 meters and halts the process immediately.*
  >
  > *If a user submits an AI-generated image, our advanced metadata scanner flags it, halts the workflow, and locks the malicious account. This protects public works resources.*
  >
  > *Next, let's switch to our Government Officer role. In the Government Desk dashboard, our officer Suresh can review the automatically drafted work orders. He can authorize the crew and update the repair status to 'In Progress', which automatically synchronizes with the public incident tracker."*

### Section 5: Analytics, Security Audits & Future Scope (4:00 - 4:30)
- **Visuals:** Show the **Analytics** tab, highlighting the interactive metrics. Click **Generate Agent Report** for Chennai to show the markdown output from the Analyst Agent. Show the **Admin Panel** security logs, then the **Future Scope** tab displaying the WaterGuard, EnvironmentGuard, and CleanCity roadmaps.
- **Narrator Speech:**
  > *"On the Analytics page, we see real-time charts compiled from our MCP databases. We can also query our Infrastructure Intelligence Agent directly to generate a markdown risk forecast report. For administrators, the Admin Panel displays secure cryptographic JWT tokens and an immutable audit log database, tracking every security event and blocked fraud attempt.*
  >
  > *RoadGuard AI is only the first module. CivicGuard's modular design is ready to scale into WaterGuard, CleanCity, and EnvironmentGuard modules to support comprehensive digital governance."*

### Section 6: Outro (4:30 - 5:00)
- **Visuals:** Show the landing page with the main project title.
- **Narrator Speech:**
  > *"CivicGuard AI bridges the gap between civic participation and municipal efficiency, utilizing Google ADK, FastMCP, and Gemini to create a safer, smarter, and more transparent community.*
  >
  > *The application is fully containerized and deployable to Cloud Run, Railway, or Render. Thank you for watching. Together, let's build agents for good."*
