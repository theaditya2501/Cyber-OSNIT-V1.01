import requests
import json
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_gaia_metadata(email):
    """THE GOLDEN KEY: Queries the legacy Picasa API."""
    url = f"https://picasaweb.google.com/data/entry/api/user/{email}?alt=json"
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            data = r.json()
            entry = data.get("entry", {})
            return {
                "found": True,
                "gaia_id": entry.get("gphoto$user", {}).get("$t"),
                "name": entry.get("gphoto$nickname", {}).get("$t"),
                "avatar": entry.get("gphoto$thumbnail", {}).get("$t"),
                "source": "Picasa API"
            }
    except:
        pass
    return {"found": False}

def check_google_calendar(email):
    """Checks if a Gmail address has a public Calendar."""
    url = f"https://calendar.google.com/calendar/ical/{email}/public/basic.ics"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            cal_name = re.search(r'X-WR-CALNAME:(.*)', r.text)
            timezone = re.search(r'X-WR-TIMEZONE:(.*)', r.text)
            last_mod = r.headers.get("Last-Modified", "Unknown")
            return {
                "found": True, 
                "public": True, 
                "message": "Public Calendar (Downloadable)",
                "url": url,
                "cal_name": cal_name.group(1).strip() if cal_name else "Unknown",
                "timezone": timezone.group(1).strip() if timezone else "Unknown",
                "last_active": last_mod
            }
        elif r.status_code == 404:
            return {"found": True, "public": False, "message": "Calendar is Private"}
    except:
        pass
    return {"found": False, "public": False, "message": "No Data"}

def generate_advanced_dorks(email, gaia_id=None):
    dorks = [
        {"name": "LinkedIn Profile", "url": f"https://www.google.com/search?q=\"{email}\"+site:linkedin.com"},
        {"name": "Facebook Account", "url": f"https://www.google.com/search?q=\"{email}\"+site:facebook.com"},
        {"name": "Pastebin Leaks", "url": f"https://www.google.com/search?q=\"{email}\"+site:pastebin.com"},
        {"name": "Gravatar Profile", "url": f"http://en.gravatar.com/site/check/{email}"}
    ]
    if gaia_id:
        dorks.insert(0, {"name": "📍 Maps Reviews", "url": f"https://www.google.com/maps/contrib/{gaia_id}"})
        dorks.insert(1, {"name": "🖼️ Album Archive", "url": f"https://get.google.com/albumarchive/{gaia_id}"})
    else:
        dorks.insert(0, {"name": "Maps Reviews (Search)", "url": f"https://www.google.com/search?q=\"{email}\"+site:google.com/maps/contrib"})
    
    return dorks

def google_osint(email):
    if not email or "@" not in email: return {}
    gaia_data = get_gaia_metadata(email)
    calendar_data = check_google_calendar(email)
    dorks = generate_advanced_dorks(email, gaia_data.get("gaia_id"))
    return {
        "gaia_data": gaia_data,
        "calendar": calendar_data,
        "dorks": dorks,
        "summary": {
            "real_name": gaia_data.get("name") or calendar_data.get("cal_name"),
            "location_indicator": calendar_data.get("timezone"),
            "gaia_id": gaia_data.get("gaia_id"),
            "last_active": calendar_data.get("last_active")
        }
    }