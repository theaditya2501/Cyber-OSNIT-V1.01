import requests
import json
import os
import re
import hashlib
import concurrent.futures
from bs4 import BeautifulSoup
import gender_guesser.detector as gender

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLATFORMS_FILE = os.path.join(BASE_DIR, 'platforms.json')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

def load_platforms():
    try:
        with open(PLATFORMS_FILE, 'r', encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

# ==========================================
#  SECTION 1: GENERATORS (Alts & Leetspeak)
# ==========================================

def generate_permutations(username):
    """
    Standard Variations: Adds numbers, underscores, official tags.
    """
    return [
        username + "1", username + "123", username + "_",
        "its" + username, "real" + username, username + "official"
    ]

def generate_leetspeak(username):
    """
    Hacker Variations: Swaps letters for numbers (e.g., 'hello' -> 'h3ll0').
    """
    subs = {'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5', 't': '7'}
    leet = "".join([subs.get(c, c) for c in username.lower()])

    # Return original leet and an underscore variant
    return [leet, f"_{leet}", f"{leet}_"]

def get_all_variations(username):
    """Master function to get unique alternatives."""
    # Combine lists and remove duplicates using set()
    all_vars = set(generate_permutations(username) + generate_leetspeak(username))
    return list(all_vars)

# ==========================================
#  SECTION 2: ENRICHMENT MODULES
# ==========================================

def predict_demographics(real_name):
    """
    1. Demographic Profiling: Guesses gender from First Name.
    """
    if not real_name: return "Unknown"
    d = gender.Detector()
    first_name = real_name.split()[0]
    guess = d.get_gender(first_name)

    if "female" in guess: return "Female"
    if "male" in guess: return "Male"
    return "Uncertain"

def check_wayback_machine(url):
    """
    2. Time Machine: Checks Internet Archive for deleted profiles.
    """
    api_url = f"http://archive.org/wayback/available?url={url}"
    try:
        r = requests.get(api_url, timeout=3)
        data = r.json()
        if data.get("archived_snapshots", {}).get("closest"):
            return data["archived_snapshots"]["closest"]["url"]
    except:
        pass
    return None

def check_gravatar_pivot(username):
    """
    3. Gravatar Pivot: Hashes email guesses to find a photo/profile.
    """
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "protonmail.com"]
    for domain in domains:
        email = f"{username}@{domain}"
        email_hash = hashlib.md5(email.lower().encode()).hexdigest()
        url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                return {"found": True, "email": email, "image": url}
        except:
            pass
    return None

def get_github_connections(username):
    """
    7. Social Graph: Grabs who the target follows on GitHub.
    """
    url = f"https://api.github.com/users/{username}/following"
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return [u['login'] for u in r.json()[:5]] # Return top 5
    except:
        pass
    return []

# ==========================================
#  SECTION 3: CORE SCRAPING & ANALYSIS
# ==========================================

def scrape_metadata(html_content, platform_name):
    """
    Extracts Bio, Secrets, and Dates.
    Includes 'Bio Hunter' logic.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    data = {'title': None, 'image': None, 'bio': None, 'secrets': [], 'created_at': None}

    # Standard Extraction
    if soup.title: data['title'] = soup.title.string.strip()
    og_img = soup.find("meta", property="og:image")
    if og_img: data['image'] = og_img.get("content")

    desc = soup.find("meta", {"name": "description"}) or soup.find("meta", property="og:description")
    if desc:
        data['bio'] = desc.get("content", "")[:300]

        # --- BIO HUNTER LOGIC ---
        # 1. Emails
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', data['bio'])
        for e in emails: data['secrets'].append(f"Email: {e}")

        # 2. Crypto
        btc = re.findall(r'\b(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b', data['bio'])
        if btc: data['secrets'].append(f"BTC: {btc[0]}")

    # --- TIMELINE LOGIC ---
    if platform_name == "GitHub":
        time_tag = soup.find("relative-time")
        if time_tag: data['created_at'] = time_tag.get("datetime")[:10]

    return data

def check_single_platform(p, username):
    url = p["url"].format(username)
    check_type = p.get("check_type", "status_code")

    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        exists = False

        if check_type == "status_code" and r.status_code == 200: exists = True
        elif check_type == "string_match" and r.status_code == 200 and p.get("error_msg") not in r.text: exists = True

        if exists:
            meta = scrape_metadata(r.text, p["name"])

            # Run Deep Scans on specific platforms
            if p["name"] == "GitHub":
                meta["connections"] = get_github_connections(username)

            if meta.get("title"):
                meta["demographics"] = predict_demographics(meta["title"])

            # --- KEY FIX HERE: Changed "exists": True to "found": True ---
            return {
                "platform": p["name"], "url": url, "category": p["category"],
                "found": True, "metadata": meta, "avatar": meta.get("image")
            }

        # 5. Fallback: Check Wayback Machine for 'Social' sites if not found
        elif p["category"] == "Social":
            archive = check_wayback_machine(url)
            if archive:
                return {
                    "platform": p["name"], "url": archive, "category": "Archive",
                    "found": True, "metadata": {"bio": "Profile deleted. Found in Wayback Machine."}
                }

    except:
        pass
    return None

def generate_radar_stats(results):
    """
    Calculates the exact numbers for your VECTORS Chart.
    """
    stats = {"Social": 0, "Dev": 0, "Contact": 0, "Breach": 0, "Geo": 0}

    for r in results.values():
        cat = r.get("category", "")

        if cat == "Social": stats["Social"] += 20
        if cat in ["Tech", "Developer", "Gaming"]: stats["Dev"] += 25

        # Check Contact (Did we find secrets/emails?)
        if r.get("metadata", {}).get("secrets"): stats["Contact"] += 50

        # Check Geo (Did we find demographics?)
        if r.get("metadata", {}).get("demographics", "Unknown") != "Unknown": stats["Geo"] += 40

        # Check Breach (Placeholder logic)
        if r.get("breach_data"): stats["Breach"] += 100

    # Cap at 100
    for k in stats: stats[k] = min(stats[k], 150) # Your chart goes to 150
    return stats

# --- MAIN RUNNER ---

def check_username(username):
    platforms = load_platforms()
    results = {}

    # 1. MAIN SCAN
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(check_single_platform, p, username): p["name"] for p in platforms}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res: results[res["platform"]] = res

    # 2. GRAVATAR PIVOT
    grav = check_gravatar_pivot(username)
    if grav:
        results["Gravatar"] = {
            "platform": "Gravatar", "url": grav["image"], "category": "Contact",
            "found": True, "metadata": {"secrets": [f"Email: {grav['email']}"]}
        }

    # 3. GOOGLE DORKING (Fallback)
    if "Instagram" not in results:
        results["Instagram (Dork)"] = {
            "platform": "Google",
            "url": f"https://www.google.com/search?q=site:instagram.com+%22{username}%22",
            "category": "Search", "found": False, "metadata": {"bio": "Manual Search Link"}
        }

    # 4. LEETSPEAK/ALT GENERATOR (If result count is low)
    if len(results) < 2:
        print("[!] Low results. Generating Alts...")
        alts = get_all_variations(username)
        results["_alts_generated"] = alts # Pass to frontend to suggest new scans

    # 5. GENERATE RADAR DATA
    results["_radar_stats"] = generate_radar_stats(results)

    return results

if __name__ == "__main__":
    target = input("Username: ")
    data = check_username(target)
    print(json.dumps(data, indent=2, default=str))