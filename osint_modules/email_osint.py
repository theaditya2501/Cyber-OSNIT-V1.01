import re
import hashlib
import requests

def generate_email_variations(email):
    local, domain = email.split("@")
    variations = set([
        email,
        local.replace(".", "") + "@" + domain,
        local.replace("_", "") + "@" + domain,
        local.replace("-", "") + "@" + domain
    ])

    if len(local) > 4:
        variations.add(local[:-1] + "@" + domain)
    
    return list(variations)

def email_osint(email):
    result = {
        "valid": False,
        "provider": None,
        "email_variations": [],
        "gravatar": {"exists": False, "profile_url": None},
        "breach_indicator": "UNKNOWN"
    }

    if not email:
        return result

    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(pattern, email):
        return result

    result["valid"] = True
    result["provider"] = email.split("@")[1]
    result["email_variations"] = generate_email_variations(email)

    # Gravatar check
    email_hash = hashlib.md5(email.lower().encode()).hexdigest()
    url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"
    
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            result["gravatar"]["exists"] = True
            result["gravatar"]["profile_url"] = f"https://www.gravatar.com/{email_hash}"
    except:
        pass
        
    result["breach_indicator"] = "Check via trusted breach intelligence (HIBP)"
    
    return result