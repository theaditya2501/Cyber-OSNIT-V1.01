from flask import Flask, request, jsonify, render_template
from datetime import datetime, timezone
import os
import json
import random
import sys

# ===============================
# CONFIGURATION & PATHS
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'helpers'))
sys.path.append(os.path.join(BASE_DIR, 'osint_modules'))

# DIAGNOSTIC CHECK
platforms_path = os.path.join(BASE_DIR, 'osint_modules', 'platforms.json')
if not os.path.exists(platforms_path):
    print(f"\n[!] WARNING: 'platforms.json' not found at {platforms_path}")

from helpers.case_manager import create_case, update_case, add_evidence, save_analyst_notes

# ===============================
# IMPORT INTELLIGENCE MODULES
# ===============================
# ===== CORE MODULES (must load) =====
from osint_modules.username_osint import check_username
from osint_modules.phone_osint import phone_lookup
from osint_modules.email_osint import email_osint
from osint_modules.profile_extract import extract_github_profile
from osint_modules.confidence_score import calculate_identity_confidence
from osint_modules.correlate import correlate
from osint_modules.risk_score import calculate_risk
from osint_modules.google_osint import google_osint
from osint_modules.account_enum import run_account_enum
from osint_modules.advanced_search import run_advanced_search
from osint_modules.breach_check import simple_breach_check

print("[+] Core OSINT modules loaded")

# ===== OPTIONAL LIBRARIES (may fail) =====
try:
    import gender_guesser.detector as gender
except ImportError as e:
    gender = None
    print("[!] gender_guesser missing:", e)

try:
    import phonenumbers
except ImportError as e:
    phonenumbers = None
    print("[!] phonenumbers missing:", e)


app = Flask(__name__)

current_case_id = None
latest_result = {}

def get_day_index(date_str):
    """Parses a date string and returns the day of week index (0=Mon, 6=Sun)."""
    if not date_str: return None
    formats = [
        "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", 
        "%b %d, %Y", "%d-%m-%Y", "%Y/%m/%d"
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(str(date_str).split('.')[0], fmt)
            return dt.weekday() # 0 = Monday
        except ValueError:
            continue
    return None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/create_case", methods=["POST"])
def create_new_case():
    global current_case_id
    data = request.json or {}
    current_case_id = create_case(
        case_name=data.get("case_name", "OSINT Investigation"),
        analyst=data.get("analyst", "Analyst"),
        scope=data.get("scope", {"username": True, "email": True, "phone": True})
    )
    return jsonify({"status": "case_created", "case_id": current_case_id})

@app.route("/check_status/<case_id>")
def check_status(case_id):
    path = os.path.join("cases", f"case_{case_id}", "investigation.json")
    if os.path.exists(path):
        return jsonify({"status": "COMPLETED"})
    return jsonify({"status": "PROCESSING"})

@app.route("/run_osint", methods=["POST"])
def run_osint():
    global latest_result, current_case_id
    data = request.json or {}
    print("\n[>] Incoming Scan Request...")

    if not current_case_id:
        current_case_id = create_case("Auto-Scan Case", "System", {})

    username = data.get("username")
    email = data.get("email")
    phone = data.get("phone")

    # --- 1. USERNAME INTELLIGENCE ---
    username_data = {}
    radar_stats = {"Social": 0, "Dev": 0, "Geo": 0, "Breach": 0, "Contact": 0}
    alts_generated = []
    
    if username:
        print(f"[*] Scanning Username: {username}")
        try:
            raw_results = check_username(username)
            print(f"[+] Scan finished. Found {len(raw_results)} profiles.")
            radar_stats = raw_results.pop("_radar_stats", radar_stats)
            alts_generated = raw_results.pop("_alts_generated", [])
            username_data = raw_results
        except Exception as e:
            print(f"[!] Error in Username Scan: {e}")

    # --- 2. EMAIL & ADVANCED INTELLIGENCE ---
    email_data = {}
    google_data = {}
    account_enum_data = {}
    advanced_search_data = {}

    if email:
        print(f"[*] Scanning Email: {email}")
        email_data = email_osint(email)
        
        # A. Google Specifics
        if "gmail.com" in email:
            try:
                google_data = google_osint(email)
                email_data["google_intel"] = google_data
                if google_data.get("gaia_data", {}).get("found"):
                    radar_stats["Geo"] += 20
            except: pass

        # B. Account Enumeration
        try:
            account_enum_data = run_account_enum(email)
            email_data["account_enum"] = account_enum_data
        except: pass

        # C. Advanced
        try:
            advanced_search_data = run_advanced_search(email)
            email_data["advanced"] = advanced_search_data
        except: pass

        # D. Breach Check
        try:
            username_part = email.split("@")[0]
            breach_result = simple_breach_check(username_part)
            if breach_result.get("status") == "danger":
                email_data["breach_check"] = "COMPROMISED"
                email_data["breaches"] = breach_result.get("breaches", [])
                radar_stats["Breach"] = 100 
            else:
                email_data["breach_check"] = "SAFE"
        except:
            email_data["breach_check"] = "UNKNOWN"

    # --- 3. PHONE INTELLIGENCE ---
    phone_data = {}
    if phone:
        print(f"[*] Scanning Phone: {phone}")
        phone_data = phone_lookup(phone)
        if phone_data.get("valid"):
            radar_stats["Contact"] += 50
            if "spam_score" not in phone_data.get("identity", {}):
                if "identity" not in phone_data: phone_data["identity"] = {}
                phone_data["identity"]["spam_score"] = "Low (0/10)"

    # --- 4. TIMELINE & ACTIVITY ANALYSIS (REAL) ---
    timeline_events = []
    
    # [NEW] Activity Stats: Mon, Tue, Wed, Thu, Fri, Sat, Sun
    activity_stats = [0, 0, 0, 0, 0, 0, 0] 

    # Dates from Username Profiles
    for platform, pdata in username_data.items():
        if isinstance(pdata, dict):
            # Try to parse timeline_date for Activity Chart
            if pdata.get("timeline_date"):
                # Add to timeline
                timeline_events.append({
                    "year": pdata["timeline_date"],
                    "category": "Account Creation",
                    "event": f"{platform} Account Detected",
                    "details": f"User active or joined {platform}"
                })
                # Attempt to extract day of week
                day_idx = get_day_index(pdata.get("timeline_date"))
                if day_idx is not None: activity_stats[day_idx] += 1

            if pdata.get("breach_data"):
                timeline_events.append({
                    "year": "2024 (Recent)",
                    "category": "Breach",
                    "event": "Malware Log Detected",
                    "details": pdata["breach_data"]["msg"]
                })

    if email_data.get("valid"):
        timeline_events.append({"year": "2023", "category": "Registration", "event": "Email Domain Active", "details": "DNS Records Verified"})
    
    # Advanced Email Dates
    if google_data.get("summary", {}).get("last_active") != "Unknown" and google_data.get("summary", {}).get("last_active"):
         date_val = str(google_data["summary"]["last_active"])
         timeline_events.append({"year": "Recent", "category": "Activity", "event": "Google Calendar Modified", "details": date_val})
         day_idx = get_day_index(date_val)
         if day_idx is not None: activity_stats[day_idx] += 5 # Weight recent activity higher

    # GitHub Profile Activity
    if username_data.get("GitHub", {}).get("found"):
        gh_profile = extract_github_profile(username)
        if gh_profile.get("created_at"):
            day_idx = get_day_index(gh_profile["created_at"])
            if day_idx is not None: activity_stats[day_idx] += 1

    # Normalize stats if they are empty (prevent empty chart)

    timeline_events.sort(key=lambda x: str(x['year']))

    # --- 5. PROFILE & EVIDENCE ---
    profile_data = {}
    if username_data.get("GitHub", {}).get("found"):
        profile_data["GitHub"] = extract_github_profile(username)

    for platform, pdata in username_data.items():
        if pdata.get("found") and pdata.get("url"):
            add_evidence(current_case_id, {
                "platform": platform,
                "url": pdata["url"],
                "type": "profile",
                "confidence": "HIGH",
                "notes": f"Detected via {pdata.get('category')} scan",
                "analyst": "System",
                "images": [pdata.get("avatar")] if pdata.get("avatar") else []
            })

    # --- 6. SCORING ---
    correlation = correlate(username_data, phone_data, False)
    risk = calculate_risk(correlation)
    if radar_stats["Breach"] > 0:
        risk["score"] = max(risk.get("score", 0), 85)
        risk["level"] = "CRITICAL"

    confidence = calculate_identity_confidence(username_data, email_data, phone_data, profile_data)

    latest_result = {
        "case_id": current_case_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "username_results": username_data,
        "email_results": email_data,
        "phone_results": phone_data,
        "profiles": profile_data,
        "risk": risk,
        "identity_confidence": confidence,
        "radar_stats": radar_stats,
        "timeline": timeline_events,
        "activity_stats": activity_stats, # SENT TO FRONTEND
        "alts": alts_generated
    }

    update_case(current_case_id, latest_result, "investigation.json")
    print(f"[>] Scan complete. Sent data to frontend.\n")
    return jsonify(latest_result)

@app.route("/add_evidence", methods=["POST"])
def manual_evidence():
    data = request.json or {}
    entry = add_evidence(current_case_id, data)
    return jsonify({"status": "evidence_added", "evidence": entry})

@app.route("/get_result")
def get_result():
    return jsonify({"success": True, "data": latest_result}), 200

@app.route("/get_evidence/<case_id>")
def get_evidence_route(case_id):
    path = os.path.join("cases", f"case_{case_id}", "evidence.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return jsonify(json.load(f))
    return jsonify([])

@app.route("/submit_analyst_notes", methods=["POST"])
def submit_analyst_notes():
    data = request.json or {}
    notes = {
        "verdict": data.get("verdict"),
        "notes": data.get("notes"),
        "analyst": data.get("analyst", "Analyst"),
        "submitted_at": datetime.now(timezone.utc).isoformat()
    }
    save_analyst_notes(current_case_id, notes)
    return jsonify({"status": "saved"})

if __name__ == "__main__":
    print("[+] OSINT Command Center Online: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)


