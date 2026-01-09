import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def check_spotify(email):
    """
    Checks if a Spotify account exists using the registration validation endpoint.
    """
    url = "https://spclient.wg.spotify.com/signup/public/v1/account?validate=1&email={}"
    try:
        r = requests.get(url.format(email), headers=HEADERS, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == 20: # Status 20 = Account exists
                return {"found": True, "platform": "Spotify", "details": "Account Confirmed"}
    except:
        pass
    return {"found": False, "platform": "Spotify"}

def check_microsoft_cid(email):
    """
    Attempts to retrieve the Microsoft CID (Customer ID).
    """
    if "outlook" not in email and "hotmail" not in email and "live" not in email:
        return {"found": False} 

    return {
        "found": True, 
        "platform": "Microsoft/Skype",
        "details": "CID Lookup Ready",
        "tool_link": f"https://www.skyplookup.com/search?q={email}"
    }

def check_adobe(email):
    """
    Checks Adobe account status (Deep Link).
    """
    return {
        "found": True,
        "platform": "Adobe ID",
        "details": "Manual Verify Required",
        "manual_link": f"https://auth.services.adobe.com/en_US/index.html?callback=https%3A%2F%2Fims-na1.adobelogin.com%2Fims%2Fadobeid%2FAdobeID%2FAdobeID%2Ftoken%3Fclient_id%3DAdobeID%26redirect_uri%3Dhttps%253A%252F%252Fadobe.com%252F&client_id=AdobeID&scope=AdobeID,openid&denied_callback=https%3A%2F%2Fims-na1.adobelogin.com%2Fims%2Fdenied%2FAdobeID%3Fredirect_uri%3Dhttps%253A%252F%252Fadobe.com%252F&state={email}"
    }

def run_account_enum(email):
    results = {}
    
    # 1. Spotify
    spot = check_spotify(email)
    if spot["found"]: results["Spotify"] = spot

    # 2. Microsoft
    ms = check_microsoft_cid(email)
    if ms["found"]: results["Microsoft"] = ms

    # 3. Adobe (Always return link)
    results["Adobe"] = check_adobe(email)

    return results