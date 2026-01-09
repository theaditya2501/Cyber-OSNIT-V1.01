import requests
import json
import time

# --- CONFIGURATION ---
# To make this robust, you eventually want an API Key from haveibeenpwned.com
# For now, we will use a free preview technique or simulation based on real data structures.

def get_github_email(username):
    """
    TRICK: Scrapes GitHub's public API for commit activity.
    Developers often accidentally leave their email in their git config.
    """
    url = f"https://api.github.com/users/{username}/events/public"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            events = r.json()
            for event in events:
                if event["type"] == "PushEvent":
                    for commit in event["payload"]["commits"]:
                        email = commit["author"]["email"]
                        # Filter out generic github no-reply emails
                        if "users.noreply.github.com" not in email:
                            return email
    except Exception as e:
        pass
    return None

def check_hudson_rock(email):
    """
    REAL DATA: Checks Hudson Rock's free 'Cavalier' preview.
    Returns a list of 'Stealer Logs' or breaches if found.
    """
    url = f"https://cavalier.hudsonrock.com/api/json/v2/preview/search-by-login/osint-tools?login={email}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            # If the response contains 'stealers', the email is compromised
            if data.get("stealers"):
                return {
                    "compromised": True,
                    "count": len(data.get("stealers")),
                    "sources": [s.get("computer_name", "Unknown Infostealer") for s in data.get("stealers")[:3]]
                }
    except:
        pass
    return None

def simple_breach_check(username):
    """
    The Main Controller Function.
    1. Tries to find an email via GitHub.
    2. Checks that email against breach datasets.
    """
    print(f"[*] Attempting Email Pivot for user: {username}...")
    
    # 1. PIVOT: Username -> Email
    email = get_github_email(username)
    
    if not email:
        return {"status": "skipped", "reason": "No email found in public sources"}

    print(f"[+] SUCCESS: Found associated email: {email}")

    # 2. CHECK: Email -> Breach Data
    # (Using Hudson Rock as the free 'Real' source)
    breach_data = check_hudson_rock(email)

    if breach_data and breach_data["compromised"]:
        return {
            "status": "danger",
            "email": email,
            "breaches": breach_data["sources"], # e.g., ["RedLine Stealer", "Raccoon Stealer"]
            "timeline_event": f"Compromised in {len(breach_data['sources'])} Malware Campaigns"
        }
    
    return {"status": "clean", "email": email}

# CLI Test
if __name__ == "__main__":
    target = input("Enter target GitHub username: ")
    result = simple_breach_check(target)
    print(json.dumps(result, indent=2))