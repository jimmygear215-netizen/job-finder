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


def extract_json(text):
    text = re.sub(r'```(?:json)?\s*|\s*```', '', text.strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for m in [re.search(r'\{.*\}', text, re.DOTALL), re.search(r'\[.*\]', text, re.DOTALL)]:
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                continue
    raise json.JSONDecodeError("No valid JSON found", text[:200], 0)


def _fmt_qa(qa_list):
    return ' | '.join([f"Q: {q['q'][:60]} A: {q['a'][:40]}" for q in qa_list])


def _fmt_profile(p):
    return f"{p.get('summary','')} | Skills: {','.join(p.get('top_skills',[]))} | {p.get('experience_level','')} | Industry: {p.get('current_industry','')}"


def analyze_with_ai(resume_text, url_data, career_intent, endpoint, api_key="", model=""):
    intent = "same career path" if career_intent == "same" else "dream job / career change"
    prompt = f"Job seeker wants {intent}.\nResume:\n{resume_text[:2000]}\nURLs:\n{''.join(url_data)[:500]}\n\nReturn this exact JSON structure with real values:\n{{\"summary\":\"1-2 sentence description\",\"top_skills\":[\"skill1\",\"skill2\"],\"experience_level\":\"senior\",\"current_industry\":\"industry name\",\"knowledge_gaps\":\"missing info\"}}"

    payload = {
        "messages": [
            {"role": "system", "content": "Return valid JSON only. No markdown, no code fences."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }
    if model: payload["model"] = model

    try:
        content = call_ai(payload, endpoint, api_key)
        return extract_json(content)
    except json.JSONDecodeError as e:
        return {"error": "JSON parse failed", "raw_response": content[:500], "fallback": True}
    except Exception as e:
        return {"error": str(e)[:100], "fallback": True}


def get_next_question(profile, career_intent, qa_history, question_number, endpoint, api_key="", model=""):
    intent = "same path" if career_intent == "same" else "dream job"
    prompt = f"Goal: {intent} | Q#{question_number+1}/5\nProfile: {_fmt_profile(profile)}\nHistory: {_fmt_qa(qa_history) if qa_history else 'none'}\n\nReturn JSON:\n- question: string (under 20 words, simple language)\n- options: array of objects with \"value\" (string) and \"label\" (string) keys\n- why_before: string or null (acknowledge their last answer, skip if first question)"

    payload = {
        "messages": [
            {"role": "system", "content": "Return valid JSON only. No markdown."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }
    if model: payload["model"] = model

    try:
        content = call_ai(payload, endpoint, api_key)
        return extract_json(content)
    except json.JSONDecodeError as e:
        return {"error": "JSON parse failed", "raw_response": content[:500]}
    except Exception as e:
        return {"error": str(e)[:100]}


def suggest_roles(profile, career_intent, qa_history, endpoint, api_key="", model=""):
    intent = "same path" if career_intent == "same" else "dream job"
    prompt = f"Goal: {intent}\nProfile: {_fmt_profile(profile)}\nQ&A: {_fmt_qa(qa_history)}\n\nReturn JSON array of 10 role suggestion objects. Each object:\n- title: string (specific job title)\n- match_score: integer 0-100\n- why_it_fits: string (one sentence)\n- industry: string\n- typical_salary_range: string"

    payload = {
        "messages": [
            {"role": "system", "content": "Return valid JSON array only. No markdown."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 1200
    }
    if model: payload["model"] = model

    try:
        content = call_ai(payload, endpoint, api_key, timeout=90)
        return extract_json(content)
    except json.JSONDecodeError as e:
        return {"error": "JSON parse failed", "raw_response": content[:500]}
    except Exception as e:
        return {"error": str(e)[:100]}
