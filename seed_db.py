import json
import os
import hashlib
from datetime import datetime, timedelta

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def seed_database():
    print("Seeding database JSON files...")
    
    # 1. users.json
    users = [
        {
            "username": "citizen_lokesh",
            "password": hash_password("password123"),
            "fullname": "Lokesh Raj",
            "role": "citizen",
            "points": 210,
            "badges": ["Road Protector", "Community Guardian"],
            "status": "active",
            "created_at": (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"
        },
        {
            "username": "citizen_jane",
            "password": hash_password("password123"),
            "fullname": "Jane Doe",
            "role": "citizen",
            "points": 75,
            "badges": ["Road Protector"],
            "status": "active",
            "created_at": (datetime.utcnow() - timedelta(days=20)).isoformat() + "Z"
        },
        {
            "username": "citizen_bob",
            "password": hash_password("password123"),
            "fullname": "Bob Smith",
            "role": "citizen",
            "points": 10,
            "badges": [],
            "status": "active",
            "created_at": (datetime.utcnow() - timedelta(days=5)).isoformat() + "Z"
        },
        {
            "username": "gov_officer",
            "password": hash_password("govpass123"),
            "fullname": "Officer Suresh",
            "role": "government",
            "points": 0,
            "badges": [],
            "status": "active",
            "created_at": (datetime.utcnow() - timedelta(days=60)).isoformat() + "Z"
        },
        {
            "username": "admin_user",
            "password": hash_password("adminpass123"),
            "fullname": "System Admin",
            "role": "admin",
            "points": 0,
            "badges": [],
            "status": "active",
            "created_at": (datetime.utcnow() - timedelta(days=90)).isoformat() + "Z"
        },
        {
            "username": "malicious_user",
            "password": hash_password("malpass123"),
            "fullname": "Spam Reporter",
            "role": "citizen",
            "points": 0,
            "badges": [],
            "status": "restricted",
            "created_at": (datetime.utcnow() - timedelta(days=10)).isoformat() + "Z"
        }
    ]
    with open("users.json", "w") as f:
        json.dump(users, f, indent=2)
    print("OK: Created users.json")

    # 2. incidents.json
    incidents = [
        {
            "incident_id": "HZ-RG-84912",
            "username": "citizen_lokesh",
            "description": "Massive pothole in Chennai near Velachery Main Road. It is deep (about 15cm) and filled with rain water. Cars are swerving abruptly and it's dangerous for motorcycles.",
            "latitude": 12.9784,
            "longitude": 80.2184,
            "image_url": "https://images.unsplash.com/photo-1515162305285-0293e4767cc2?auto=format&fit=crop&w=800&q=80",
            "status": "Resolved",
            "created_at": (datetime.utcnow() - timedelta(days=12)).isoformat() + "Z",
            "fraud_guard": {
                "trust_score": 95.0,
                "fraud_score": 5.0,
                "status": "Passed",
                "reasoning": "Original citizen description matching coordinates. Location consistent. Image checks clear."
            },
            "detection": {
                "damage_type": "Deep Pothole",
                "severity": "Critical",
                "confidence": 0.98,
                "summary": "Large, deep pothole in primary arterial road filled with water, blocking lane flow."
            },
            "risk": {
                "risk_score": 90.0,
                "priority": "Critical",
                "explanation": "Located on a high-density arterial road. swerving hazards for all motor vehicles. High risk of accidents."
            },
            "repair": {
                "materials": ["Asphalt Mix", "Base Aggregate", "Tack Coat Sealant"],
                "labor": "3-person crew",
                "budget": 450.0,
                "timeline": "4 hours",
                "recommendation": "Excavate water, clean loose debris, backfill aggregate, compact hot-mix asphalt and seal edges."
            },
            "government": {
                "assigned_department": "Chennai Corporation Road Maintenance",
                "work_order_id": "WO-RG-84912",
                "summary": "Dispatched emergency crew for hot-mix asphalt patch."
            },
            "rewards": {
                "points_awarded": 100,
                "badge_earned": "National Contributor",
                "level": "Critical Hazard"
            },
            "intelligence": {
                "hotspot_updated": True,
                "regional_forecast": "High risk area during monsoon seasons due to poor sub-base drainage."
            }
        },
        {
            "incident_id": "HZ-RG-42109",
            "username": "citizen_jane",
            "description": "Damaged and faded stop sign hidden behind tree branches at the intersection of 5th Ave and B Street. Drivers are crossing without stopping.",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "image_url": "https://images.unsplash.com/photo-1582268611958-ebfd161ef9cf?auto=format&fit=crop&w=800&q=80",
            "status": "In Progress",
            "created_at": (datetime.utcnow() - timedelta(days=5)).isoformat() + "Z",
            "fraud_guard": {
                "trust_score": 88.0,
                "fraud_score": 12.0,
                "status": "Passed",
                "reasoning": "Valid community report, description matches GPS context. No manipulation detected."
            },
            "detection": {
                "damage_type": "Missing/Obstructed Road Sign",
                "severity": "High",
                "confidence": 0.94,
                "summary": "Stop sign obstructed by foliage and faded, causing intersection danger."
            },
            "risk": {
                "risk_score": 75.0,
                "priority": "High",
                "explanation": "Intersection collision risk. High density residential zone with school nearby."
            },
            "repair": {
                "materials": ["Standard Reflective STOP Sign", "Metal Post & Bolts", "Pruning Tools"],
                "labor": "2-person technician crew",
                "budget": 200.0,
                "timeline": "2 hours",
                "recommendation": "Trim overlapping tree branches, replace sign panel with high-grade reflective STOP sign."
            },
            "government": {
                "assigned_department": "Traffic Control Signage Division",
                "work_order_id": "WO-RG-42109",
                "summary": "Scheduled sign replacement and trimming dispatch."
            },
            "rewards": {
                "points_awarded": 50,
                "badge_earned": "Road Protector",
                "level": "High Severity"
            },
            "intelligence": {
                "hotspot_updated": False,
                "regional_forecast": "Low recurrence rating once foliage is trimmed."
            }
        },
        {
            "incident_id": "HZ-RG-11023",
            "username": "citizen_lokesh",
            "description": "Large cracks and minor surface deformation along the slow lane on Anna Salai Road, Chennai. Starting to crumble near the edges.",
            "latitude": 13.0601,
            "longitude": 80.2496,
            "image_url": "",
            "status": "Scheduled",
            "created_at": (datetime.utcnow() - timedelta(days=3)).isoformat() + "Z",
            "fraud_guard": {
                "trust_score": 90.0,
                "fraud_score": 10.0,
                "status": "Passed",
                "reasoning": "Text-only report with realistic description. Verified GPS within active municipal zone."
            },
            "detection": {
                "damage_type": "Road Surface Cracks",
                "severity": "Medium",
                "confidence": 0.89,
                "summary": "Fatigue cracking and crumbling along edge asphalt."
            },
            "risk": {
                "risk_score": 55.0,
                "priority": "Medium",
                "explanation": "Medium density traffic. Poses moderate risk of water infiltration causing pothole expansion."
            },
            "repair": {
                "materials": ["Rubberized Crack Sealant", "Compressed Air Cleansing"],
                "labor": "2-person crew",
                "budget": 150.0,
                "timeline": "3 hours",
                "recommendation": "Clean cracks with high-pressure air, apply hot pour rubberized sealant to prevent water ingress."
            },
            "government": {
                "assigned_department": "Chennai Corporation Road Maintenance",
                "work_order_id": "WO-RG-11023",
                "summary": "Standard routine maintenance crack-sealing task queued."
            },
            "rewards": {
                "points_awarded": 25,
                "badge_earned": "Community Guardian",
                "level": "Medium Severity"
            },
            "intelligence": {
                "hotspot_updated": True,
                "regional_forecast": "High water-table zone prone to asphalt subgrade shifting."
            }
        }
    ]
    with open("incidents.json", "w") as f:
        json.dump(incidents, f, indent=2)
    print("OK: Created incidents.json")

    # 3. rewards.json
    rewards = [
        {
            "transaction_id": "TX-RG-90812",
            "username": "citizen_lokesh",
            "incident_id": "HZ-RG-84912",
            "points": 100,
            "reason": "Reported Critical Road Hazard: Deep Pothole (Chennai)",
            "badge_earned": "National Contributor",
            "created_at": (datetime.utcnow() - timedelta(days=12)).isoformat() + "Z"
        },
        {
            "transaction_id": "TX-RG-77211",
            "username": "citizen_jane",
            "incident_id": "HZ-RG-42109",
            "points": 50,
            "reason": "Reported High Severity Incident: Obstructed STOP Sign (SF)",
            "badge_earned": "Road Protector",
            "created_at": (datetime.utcnow() - timedelta(days=5)).isoformat() + "Z"
        },
        {
            "transaction_id": "TX-RG-66190",
            "username": "citizen_lokesh",
            "incident_id": "HZ-RG-11023",
            "points": 25,
            "reason": "Reported Medium Severity Road Cracks (Chennai)",
            "badge_earned": "Community Guardian",
            "created_at": (datetime.utcnow() - timedelta(days=3)).isoformat() + "Z"
        },
        {
            "transaction_id": "TX-RG-11002",
            "username": "citizen_lokesh",
            "incident_id": "HZ-RG-84912",
            "points": 85,
            "reason": "Bonus points for report verification with photographic evidence and detailed location description.",
            "badge_earned": None,
            "created_at": (datetime.utcnow() - timedelta(days=11)).isoformat() + "Z"
        }
    ]
    with open("rewards.json", "w") as f:
        json.dump(rewards, f, indent=2)
    print("OK: Created rewards.json")

    # 4. leaderboard.json
    leaderboard = [
        {
            "username": "citizen_lokesh",
            "fullname": "Lokesh Raj",
            "points": 210,
            "rank": 1,
            "badges_count": 2,
            "reports_count": 2
        },
        {
            "username": "citizen_jane",
            "fullname": "Jane Doe",
            "points": 75,
            "rank": 2,
            "badges_count": 1,
            "reports_count": 1
        },
        {
            "username": "citizen_bob",
            "fullname": "Bob Smith",
            "points": 10,
            "rank": 3,
            "badges_count": 0,
            "reports_count": 0
        }
    ]
    with open("leaderboard.json", "w") as f:
        json.dump(leaderboard, f, indent=2)
    print("OK: Created leaderboard.json")

    # 5. analytics.json
    analytics = {
        "summary": {
            "total_incidents": 3,
            "resolved_incidents": 1,
            "in_progress_incidents": 1,
            "scheduled_incidents": 1,
            "total_points_distributed": 295,
            "active_reporters": 2,
            "fraudulent_attempts_blocked": 1
        },
        "by_type": {
            "Pothole": 1,
            "Signage Obstruction": 1,
            "Surface Crack": 1,
            "Damaged Surface": 0
        },
        "by_priority": {
            "Critical": 1,
            "High": 1,
            "Medium": 1,
            "Low": 0
        },
        "hotspots": [
            {
                "city": "Chennai",
                "coordinates": [12.9784, 80.2184],
                "incidents_count": 2,
                "risk_score_avg": 72.5
            },
            {
                "city": "San Francisco",
                "coordinates": [37.7749, -122.4194],
                "incidents_count": 1,
                "risk_score_avg": 75.0
            }
        ],
        "monthly_trends": [
            {"month": "January 2026", "reported": 12, "resolved": 10},
            {"month": "February 2026", "reported": 15, "resolved": 13},
            {"month": "March 2026", "reported": 22, "resolved": 18},
            {"month": "April 2026", "reported": 18, "resolved": 16},
            {"month": "May 2026", "reported": 25, "resolved": 20},
            {"month": "June 2026", "reported": 3, "resolved": 2}
        ]
    }
    with open("analytics.json", "w") as f:
        json.dump(analytics, f, indent=2)
    print("OK: Created analytics.json")

    # 6. workorders.json
    workorders = [
        {
            "work_order_id": "WO-RG-84912",
            "incident_id": "HZ-RG-84912",
            "assigned_department": "Chennai Corporation Road Maintenance",
            "priority": "Critical",
            "status": "Completed",
            "materials": ["Asphalt Mix", "Base Aggregate", "Tack Coat Sealant"],
            "budget": 450.0,
            "labor_hours": 4.0,
            "scheduled_start": (datetime.utcnow() - timedelta(days=11)).isoformat() + "Z",
            "created_at": (datetime.utcnow() - timedelta(days=12)).isoformat() + "Z"
        },
        {
            "work_order_id": "WO-RG-42109",
            "incident_id": "HZ-RG-42109",
            "assigned_department": "Traffic Control Signage Division",
            "priority": "High",
            "status": "In Progress",
            "materials": ["Standard Reflective STOP Sign", "Metal Post & Bolts", "Pruning Tools"],
            "budget": 200.0,
            "labor_hours": 2.0,
            "scheduled_start": (datetime.utcnow() - timedelta(days=4)).isoformat() + "Z",
            "created_at": (datetime.utcnow() - timedelta(days=5)).isoformat() + "Z"
        },
        {
            "work_order_id": "WO-RG-11023",
            "incident_id": "HZ-RG-11023",
            "assigned_department": "Chennai Corporation Road Maintenance",
            "priority": "Medium",
            "status": "Assigned",
            "materials": ["Rubberized Crack Sealant", "Compressed Air Cleansing"],
            "budget": 150.0,
            "labor_hours": 3.0,
            "scheduled_start": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
            "created_at": (datetime.utcnow() - timedelta(days=3)).isoformat() + "Z"
        }
    ]
    with open("workorders.json", "w") as f:
        json.dump(workorders, f, indent=2)
    print("OK: Created workorders.json")

    # 7. audit_logs.json
    audit_logs = [
        {
            "log_id": "AUD-RG-00102",
            "timestamp": (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z",
            "event_type": "USER_REGISTRATION",
            "username": "citizen_lokesh",
            "ip_address": "127.0.0.1",
            "details": "Registered citizen profile for Lokesh Kumar."
        },
        {
            "log_id": "AUD-RG-00103",
            "timestamp": (datetime.utcnow() - timedelta(days=12)).isoformat() + "Z",
            "event_type": "INCIDENT_SUBMISSION",
            "username": "citizen_lokesh",
            "ip_address": "127.0.0.1",
            "details": "Submitted incident report (Deep Pothole near Velachery)."
        },
        {
            "log_id": "AUD-RG-00104",
            "timestamp": (datetime.utcnow() - timedelta(days=12)).isoformat() + "Z",
            "event_type": "FRAUD_DETECTED",
            "username": "malicious_user",
            "ip_address": "192.168.1.15",
            "details": "High similarity duplicate report detected from the same GPS zone within 5 minutes. Flagged as duplicate. Warned user."
        },
        {
            "log_id": "AUD-RG-00105",
            "timestamp": (datetime.utcnow() - timedelta(days=12)).isoformat() + "Z",
            "event_type": "ACCOUNT_RESTRICTED",
            "username": "malicious_user",
            "ip_address": "192.168.1.15",
            "details": "Repeated violations of false and duplicate reports. Account status updated to restricted."
        }
    ]
    with open("audit_logs.json", "w") as f:
        json.dump(audit_logs, f, indent=2)
    print("OK: Created audit_logs.json")
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    seed_database()
