def calculate_identity_confidence(username_data, email_data, phone_data, profile_data):
    score = 0
    reasons = []

    # Username reuse
    platform_count = sum(1 for p in username_data.values() if p.get("found"))
    if platform_count >= 2:
        score += 30
        reasons.append("Username reused across multiple platforms")

    # Email validity
    if email_data.get("valid"):
        score += 10
        reasons.append("Valid email provided")

    # Email variations
    if email_data.get("email_variations"):
        score += 15
        reasons.append("Email variations correlate with username")

    # Email exposure
    if profile_data.get("GitHub", {}).get("email"):
        score += 20
        reasons.append("Email publicly exposed on GitHub")

    # Phone
    if phone_data.get("valid"):
        score += 10
        reasons.append("Valid phone number")
    
    # Gravatar
    if email_data.get("gravatar", {}).get("exists"):
        score += 10
        reasons.append("Public Gravatar profile detected")

    if score > 100:
        score = 100
        
    level = "LOW"
    if score >= 70:
        level = "HIGH"
    elif score >= 40:
        level = "MEDIUM"

    return {
        "confidence_score": score,
        "level": level,
        "reasons": reasons
    }