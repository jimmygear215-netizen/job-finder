import requests
import json
import re


def call_ai(payload, endpoint, api_key, timeout=60):
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    r = requests.post(f"{endpoint}/chat/completions", headers=headers, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def extract_json(text, expect_object=False):
    text = re.sub(r'```(?:json)?\s*|\s*```', '', text.strip())
    if not text.endswith(('}', ']')):
        raise json.JSONDecodeError("Truncated response", text[:100], 0)
    try:
        result = json.loads(text)
        if expect_object and isinstance(result, list):
            pass
        else:
            return result
    except json.JSONDecodeError:
        pass
    brace = re.search(r'\{.*\}', text, re.DOTALL)
    if brace:
        try:
            return json.loads(brace.group(0))
        except json.JSONDecodeError:
            pass
    if not expect_object:
        bracket = re.search(r'\[.*\]', text, re.DOTALL)
        if bracket:
            try:
                return json.loads(bracket.group(0))
            except json.JSONDecodeError:
                pass
    raise json.JSONDecodeError("No valid JSON found", text[:200], 0)


def analyze_with_ai(resume_text, url_data, career_intent, endpoint, api_key="", model=""):
    intent = "stay on the same career path" if career_intent == "same" else "pursue their dream job / career change"
    urls_str = "\n".join(url_data) if url_data else "None provided"

    prompt = f"""A user is looking for a job and wants to {intent}.

RESUME:
{resume_text[:2000]}

URL INFORMATION:
{urls_str[:1000]}

Analyze their profile. Return valid JSON with these exact keys:
- summary: 1-2 sentence summary of their career and background
- top_skills: array of their main skill categories (e.g. ["driving","logistics","management"])
- experience_level: "junior" or "mid-level" or "senior"
- current_industry: their current field (e.g. "Towing & Recovery", "Software Development")
- knowledge_gaps: what key information is missing to recommend the right job

Example format:
{{"summary":"Driver with 10 years of CDL experience.","top_skills":["driving","logistics"],"experience_level":"senior","current_industry":"Transportation","knowledge_gaps":"management experience"}}"""

    payload = {
        "messages": [
            {"role": "system", "content": "You are a career advisor AI. Return ONLY valid JSON. No markdown, no code fences, just the JSON object."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
    }
    if model:
        payload["model"] = model

    try:
        content = call_ai(payload, endpoint, api_key)
        result = extract_json(content, expect_object=True)
        if isinstance(result, list):
            return {"error": "AI returned array instead of object", "raw_response": content[:500]}
        return result
    except json.JSONDecodeError as e:
        return {"error": "JSON parse failed", "raw_response": content[:500]}
    except Exception as e:
        return {"error": str(e)[:100]}


def get_next_question(profile, career_intent, qa_history, question_number, endpoint, api_key="", model=""):
    intent = "stay in their current career path" if career_intent == "same" else "move into their dream career"
    prev_qa = "\n".join([f"Q: {qa['q'][:80]}\nA: {qa['a'][:40]}" for q, qa in enumerate(qa_history)])
    profile_flat = f"{profile.get('summary','')} | Skills: {', '.join(profile.get('top_skills',[]))} | Level: {profile.get('experience_level','')} | Industry: {profile.get('current_industry','')}"

    prompt = f"""You are a career advisor. The user wants to {intent}.

THEIR PROFILE: {profile_flat}

PREVIOUS CONVERSATION:
{prev_qa if qa_history else "None yet"}

This is question #{question_number + 1} of 5.

Return valid JSON with:
- question: short, simple question (under 20 words)
- options: array of 4 objects with "value" and "label" keys
- why_before: if not the first question, a brief acknowledgment of their last answer (skip if first)

Keep the question simple and conversational. Options should be 3-6 words each, clear and concrete.

Example format:
{{"question":"What type of driving role interests you?","options":[{{"value":"trucking","label":"Trucking / Heavy Haul"}},{{"value":"delivery","label":"Local Delivery"}},{{"value":"fleet","label":"Fleet Management"}},{{"value":"dispatch","label":"Dispatch / Routing"}}],"why_before":"Great choice! Fleet management is a natural next step."}}"""

    payload = {
        "messages": [
            {"role": "system", "content": "You are a career advisor AI. Return ONLY valid JSON. No markdown, no code fences."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    if model:
        payload["model"] = model

    try:
        content = call_ai(payload, endpoint, api_key)
        result = extract_json(content, expect_object=True)
        if isinstance(result, list):
            return {"error": "AI returned array instead of object", "raw_response": content[:500]}
        return result
    except json.JSONDecodeError as e:
        return {"error": "JSON parse failed", "raw_response": content[:500]}
    except Exception as e:
        return {"error": str(e)[:100]}


def suggest_roles(profile, career_intent, qa_history, endpoint, api_key="", model=""):
    intent = "stay on their current career path" if career_intent == "same" else "pursue their dream career"
    prev_qa = "\n".join([f"Q: {qa['q'][:80]}\nA: {qa['a'][:40]}" for q, qa in enumerate(qa_history)])
    profile_flat = f"{profile.get('summary','')} | Skills: {', '.join(profile.get('top_skills',[]))} | Level: {profile.get('experience_level','')} | Industry: {profile.get('current_industry','')}"

    prompt = f"""You are a career advisor suggesting jobs for a user. They want to {intent}.

USER PROFILE:
{profile_flat}

THEIR ANSWERS:
{prev_qa}

Suggest 10 specific job titles that would be a great fit. Return a JSON array of objects, each with:
- title: a specific job title (e.g. "Fleet Operations Manager" not just "Manager")
- match_score: integer 0-100 (how well this fits)
- why_it_fits: one sentence explanation
- industry: what industry this role is typically in
- typical_salary_range: salary range string (e.g. "$55K-$75K")

Sort by match_score descending. Make titles specific and realistic for their experience level.

Example format:
[{{"title":"Fleet Operations Manager","match_score":94,"why_it_fits":"Your fleet management experience and logistics background make this a strong fit.","industry":"Transportation & Logistics","typical_salary_range":"$65K-$85K"}}]"""

    payload = {
        "messages": [
            {"role": "system", "content": "You are a career advisor AI. Return ONLY valid JSON array. No markdown, no code fences."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    if model:
        payload["model"] = model

    try:
        content = call_ai(payload, endpoint, api_key, timeout=90)
        return extract_json(content)
    except json.JSONDecodeError as e:
        return {"error": "JSON parse failed", "raw_response": content[:500]}
    except Exception as e:
        return {"error": str(e)[:100]}
