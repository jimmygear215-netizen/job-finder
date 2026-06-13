import re
import requests

GITHUB_API = "https://api.github.com"

def analyze_github_url(url):
    username = extract_username(url)
    if not username:
        return {"error": "Could not extract GitHub username from URL"}

    profile = fetch_user_profile(username)
    if "error" in profile:
        return profile

    repos = fetch_user_repos(username)
    languages = aggregate_languages(repos)

    skills = map_languages_to_skills(languages)
    bio_text = profile.get("bio") or ""
    top_repos = sorted(repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:5]

    return {
        "source": "github",
        "username": username,
        "name": profile.get("name") or username,
        "bio": bio_text,
        "public_repos": profile.get("public_repos", 0),
        "followers": profile.get("followers", 0),
        "top_languages": dict(sorted(languages.items(), key=lambda x: x[1], reverse=True)[:8]),
        "top_repos": [
            {"name": r["name"], "stars": r["stargazers_count"], "description": r.get("description", ""), "language": r.get("language", "")}
            for r in top_repos
        ],
        "skills_found": skills,
        "combined_text": f"{bio_text} {' '.join(skills)}"
    }

def extract_username(url):
    match = re.search(r"github\.com/([^/?#]+)", url.lower())
    return match.group(1) if match else None

def fetch_user_profile(username):
    resp = requests.get(f"{GITHUB_API}/users/{username}", timeout=10)
    if resp.status_code != 200:
        return {"error": f"GitHub user '{username}' not found (HTTP {resp.status_code})"}
    return resp.json()

def fetch_user_repos(username):
    repos = []
    page = 1
    while len(repos) < 30:
        resp = requests.get(
            f"{GITHUB_API}/users/{username}/repos",
            params={"per_page": 30, "page": page, "sort": "updated"},
            timeout=10
        )
        if resp.status_code != 200:
            break
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos[:30]

def aggregate_languages(repos):
    lang_counts = {}
    for repo in repos:
        lang = repo.get("language")
        if lang:
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
    return lang_counts

def map_languages_to_skills(languages):
    lang_to_skill = {
        "Python": "development",
        "JavaScript": "development",
        "TypeScript": "development",
        "Java": "development",
        "Go": "development",
        "Rust": "development",
        "C": "development",
        "C++": "development",
        "C#": "development",
        "Ruby": "development",
        "PHP": "development",
        "Swift": "development",
        "Kotlin": "development",
        "HTML": "development",
        "CSS": "design",
        "SCSS": "design",
        "Sass": "design",
        "Jupyter Notebook": "data",
        "R": "data",
        "SQL": "data",
    }
    skills = set()
    for lang in languages:
        skill = lang_to_skill.get(lang, "development")
        skills.add(skill)
        skills.add(lang.lower())
    return list(skills)
