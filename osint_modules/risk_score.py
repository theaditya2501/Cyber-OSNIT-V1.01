def calculate_risk(data):
    score = 0
    
    score += len(data["linked_platforms"]) * 15
    if data["phone_valid"]:
        score += 10
    if data["dob_exposed"]:
        score += 30
        
    return {
        "risk_score": score,
        "level": "LOW" if score < 30 else "MEDIUM" if score < 70 else "HIGH"
    }