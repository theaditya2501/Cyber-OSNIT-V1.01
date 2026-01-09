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
# CORE MODULE IMPORTS (MUST LOAD)
# ===============================
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

# ===============================
# OPTIONAL DEPENDENCIES (SAFE)
# ===============================
try:
    import gender_guesser.detector as gender
except ImportError:
    gender = None
    print("[!] gender-guesser missing → demographics disabled")

try:
    import phonenumbers
except ImportError:
    phonenumbers = None
    print("[!] phonenumbers missing → phone analysis limited")

# ===============================
# FLASK APP
# ===============================
app = Flask(__name__)

current_case_id = None
latest_result = {}

# ===============================
# HELPERS
# ===============================
def get_day_index(date_str):
    if not date_str:
        return None
    formats = [
        "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ", "%b %d, %Y",
        "%d-%m-%Y", "%Y/%m/%d"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(str(date_str).split('.')[0], fmt).weekday()
        except ValueError:
            continue
    return None

# ===============================
# ROUTES
# ===============================
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
            radar_stats = raw_results.pop("_radar_stats", radar_stats)
            alts_generated = raw_results.pop("_alts_generated", [])
            username_data = raw_results
        except Exception as e:
            print(f"[!] Username scan error: {e}")
            username_data = {"error": str(e)}

    # --- 2. EMAIL INTELLIGENCE ---
    email_data = {}
    google_data = {}
    account_enum_data = {}
    advanced_search_data = {}

    if email:
        print(f"[*] Scanning Email: {email}")
        try:
            email_data = email_osint(email)
        except Exception as e:
            email_data = {"valid": False, "error": str(e)}

        if "gmail.com" in email:
            try:
                google_data = google_osint(email)
                email_data["google_intel"] = google_data
                if google_data.get("gaia_data", {}).get("found"):
                    radar_stats["Geo"] += 20
            except:
                pass

        try:
            account_enum_data = run_account_enum(email)
            email_data["account_enum"] = account_enum_data
        except:
            pass

        try:
            advanced_search_data = run_advanced_search(email)
            email_data["advanced"] = advanced_search_data
        except:
            pass

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
        try:
            phone_data = phone_lookup(phone)
        except Exception as e:
            phone_data = {"valid": False, "error": str(e)}

        if phone_data.get("valid"):
            radar_stats["Contact"] += 50
            phone_data.setdefault("identity", {})
            phone_data["identity"].setdefault("spam_score", "Low (0/10)")

    # --- 4. SCORING ---
    correlation = correlate(username_data, phone_data, False)
    risk = calculate_risk(correlation)

    confidence = calculate_identity_confidence(
        username_data, email_data, phone_data, {}
    )

    latest_result = {
        "case_id": current_case_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "username_results": username_data,
        "email_results": email_data,
        "phone_results": phone_data,
        "risk": risk,
        "identity_confidence": confidence,
        "radar_stats": radar_stats,
        "alts": alts_generated
    }

    update_case(current_case_id, latest_result, "investigation.json")

    print("[>] Scan complete.")
    return jsonify({
        "success": True,
        "data": latest_result
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
