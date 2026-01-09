import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (OSINT Platform)"
}

def extract_github_profile(username):
    url = f"https://github.com/{username}"
    r = requests.get(url, headers=HEADERS, timeout=10)

    if r.status_code != 200:
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    def get_text(selector):
        el = soup.select_one(selector)
        return el.text.strip() if el else None

    avatar = None
    avatar_tag = soup.select_one("img.avatar-user")
    if avatar_tag:
        avatar = avatar_tag.get("src")

    return {
        "platform": "GitHub",
        "profile_url": url,
        "name": get_text("span.p-name"),
        "bio": get_text("div.p-note"),
        "location": get_text("li[itemprop='homeLocation'] span"),
        "company": get_text("li[itemprop='worksFor'] span"),
        "email": get_text("li[itemprop='email'] a"),
        "website": get_text("li[itemprop='url'] a"),
        "public_repos": get_text("span.Counter"),
        "avatar": avatar
    }