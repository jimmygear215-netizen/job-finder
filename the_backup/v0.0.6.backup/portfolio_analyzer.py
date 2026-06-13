import re
import requests
from bs4 import BeautifulSoup

TECH_KEYWORDS = [
    "python", "javascript", "typescript", "react", "vue", "angular", "node",
    "django", "flask", "fastapi", "express", "ruby", "rails", "java", "spring",
    "go", "rust", "c++", "c#", "php", "laravel", "swift", "kotlin",
    "html", "css", "sass", "scss", "tailwind", "bootstrap",
    "sql", "postgresql", "mysql", "mongodb", "redis", "docker", "kubernetes",
    "aws", "gcp", "azure", "firebase", "vercel", "netlify",
    "figma", "adobe", "sketch", "ui", "ux", "design", "prototype",
    "machine learning", "ai", "data science", "analytics",
    "api", "rest", "graphql", "git", "agile", "scrum"
]

EXPERIENCE_INDICATORS = {
    "junior": r"\bjunior\b|\b(junior\s+developer)\b|\b(entry.level)\b",
    "mid-level": r"\bmid.level\b|\b(mid\s+senior)\b|\b(2\+?\s+years)\b|\b(3\+?\s+years)\b",
    "senior": r"\bsenior\b|\b(lead)\b|\b(principal)\b|\b(5\+?\s+years)\b|\b(7\+?\s+years)\b|\b(10\+?\s+years)\b",
    "manager": r"\bmanager\b|\b(director)\b|\b(head\s+of)\b|\b(cto)\b"
}

def analyze_portfolio_url(url):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        resp = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"error": f"Could not fetch URL: {str(e)}"}

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    page_text = soup.get_text(separator=" ", strip=True).lower()
    title = soup.title.string.strip() if soup.title and soup.title.string else url

    found_skills = set()
    for kw in TECH_KEYWORDS:
        if kw in page_text:
            found_skills.add(kw)

    found_level = "unknown"
    for level, pattern in EXPERIENCE_INDICATORS.items():
        if re.search(pattern, page_text, re.IGNORECASE):
            found_level = level
            break

    meta_desc = ""
    meta = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
    if meta and meta.get("content"):
        meta_desc = meta["content"]

    return {
        "source": "portfolio",
        "url": url,
        "title": title,
        "meta_description": meta_desc,
        "skills_found": sorted(found_skills),
        "experience_level": found_level,
        "combined_text": page_text[:3000]
    }
