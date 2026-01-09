import os
import json
import uuid
from datetime import datetime, timezone

BASE_DIR = "cases"

# -----------------------------
# CASE CREATION
# -----------------------------
def create_case(case_name, analyst, scope):
    case_id = str(uuid.uuid4())
    case_path = os.path.join(BASE_DIR, f"case_{case_id}")
    os.makedirs(case_path, exist_ok=True)

    metadata = {
        "case_id": case_id,
        "case_name": case_name,
        "analyst": analyst,
        "scope": scope,
        "status": "OPEN",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    with open(os.path.join(case_path, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    # Initialize empty files
    for file in ["investigation.json", "analyst_notes.json", "evidence.json"]:
        with open(os.path.join(case_path, file), "w") as f:
            json.dump([], f)

    return case_id

# -----------------------------
# UPDATE CASE FILE
# -----------------------------
def update_case(case_id, data, filename):
    path = os.path.join(BASE_DIR, f"case_{case_id}", filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# -----------------------------
# ANALYST NOTES
# -----------------------------
def save_analyst_notes(case_id, notes):
    path = os.path.join(BASE_DIR, f"case_{case_id}", "analyst_notes.json")
    notes["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    with open(path, "w") as f:
        json.dump(notes, f, indent=2)

# -----------------------------
# EVIDENCE LOGGING
# -----------------------------
def add_evidence(case_id, evidence):
    path = os.path.join(BASE_DIR, f"case_{case_id}", "evidence.json")
    
    evidence_log = []
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                evidence_log = json.load(f)
        except:
            evidence_log = []

    evidence_entry = {
        "evidence_id": str(uuid.uuid4()),
        "platform": evidence.get("platform"),
        "url": evidence.get("url"),
        "type": evidence.get("type", "profile"),
        "analyst": evidence.get("analyst", "Unknown"),
        "notes": evidence.get("notes", ""),
        "confidence": evidence.get("confidence", "MEDIUM"),
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "images": evidence.get("images", [])
    }

    evidence_log.append(evidence_entry)

    with open(path, "w") as f:
        json.dump(evidence_log, f, indent=2)

    return evidence_entry