"""
🎯 Job Finder App - Flask Backend
Analyzes resumes and recommends best-fit jobs!
"""

from flask import Flask, request, jsonify, render_template
import re
from datetime import datetime
import pdf_handler
import github_analyzer
import portfolio_analyzer

app = Flask(__name__)

# ============================================================================
# 🎓 JOB DATABASE (Mock data - replace with real API later)
# ============================================================================

JOB_DATABASE = [
    # Design & Creative
    {
        "title": "Product Designer",
        "company": "StartupX",
        "remote_type": "Remote",
        "salary_min": 80000,
        "skills_required": ["design", "ux", "figma", "adobe", "wireframe"],
        "description": "Design beautiful products that users love!"
    },
    {
        "title": "UX Researcher",
        "company": "InnovateCo",
        "remote_type": "Hybrid",
        "salary_min": 75000,
        "skills_required": ["research", "analytics", "design", "data analysis"],
        "description": "Find out what users really want!"
    },
    {
        "title": "UI Developer",
        "company": "CreativeStudio",
        "remote_type": "Remote",
        "salary_min": 90000,
        "skills_required": ["html", "css", "javascript", "react"],
        "description": "Build beautiful interfaces!"
    },
    # Tech & Engineering
    {
        "title": "Backend Engineer",
        "company": "DataCorp",
        "remote_type": "Hybrid",
        "salary_min": 110000,
        "skills_required": ["python", "database", "api", "cloud"],
        "description": "Build powerful backends!"
    },
    {
        "title": "Senior Product Manager",
        "company": "TechGiant Inc.",
        "remote_type": "On-Site",
        "salary_min": 120000,
        "skills_required": ["management", "strategy", "leadership", "agile"],
        "description": "Lead the product vision!"
    },
    {
        "title": "QA Engineer",
        "company": "TestMaster Ltd",
        "remote_type": "Remote",
        "salary_min": 65000,
        "skills_required": ["testing", "qa", "quality assurance", "bug"],
        "description": "Ensure quality across the product line!"
    },
    # Driving & Logistics
    {
        "title": "Truck Driver",
        "company": "FreightCorp",
        "remote_type": "On-Site",
        "salary_min": 55000,
        "skills_required": ["driving", "cdl", "logistics", "routes"],
        "description": "Haul freight across regional routes with a safe record."
    },
    {
        "title": "Delivery Driver",
        "company": "QuickShip Logistics",
        "remote_type": "On-Site",
        "salary_min": 38000,
        "skills_required": ["driving", "delivery", "routes", "logistics"],
        "description": "Deliver packages to residential and commercial customers."
    },
    {
        "title": "Fleet Manager",
        "company": "LogiCo Transport",
        "remote_type": "Hybrid",
        "salary_min": 72000,
        "skills_required": ["fleet", "logistics", "management", "planning"],
        "description": "Oversee fleet operations, maintenance schedules, and driver assignments."
    },
    {
        "title": "Logistics Coordinator",
        "company": "SupplyChain Inc",
        "remote_type": "Hybrid",
        "salary_min": 48000,
        "skills_required": ["logistics", "planning", "coordination", "data entry"],
        "description": "Coordinate shipments, track inventory, and manage supplier communications."
    },
    {
        "title": "Dispatcher",
        "company": "RoutePro Dispatch",
        "remote_type": "On-Site",
        "salary_min": 42000,
        "skills_required": ["dispatch", "scheduling", "communication", "logistics"],
        "description": "Dispatch drivers, optimize routes, and handle real-time logistics issues."
    },
    {
        "title": "Route Planner",
        "company": "OptiRoute Solutions",
        "remote_type": "Remote",
        "salary_min": 52000,
        "skills_required": ["route planning", "logistics", "data analysis", "mapping"],
        "description": "Design and optimize delivery routes for maximum efficiency."
    },
    {
        "title": "Warehouse Manager",
        "company": "StorageMax Corp",
        "remote_type": "On-Site",
        "salary_min": 58000,
        "skills_required": ["warehouse", "inventory", "management", "logistics"],
        "description": "Manage warehouse operations, inventory accuracy, and team productivity."
    },
    # General & Administrative
    {
        "title": "Customer Service Representative",
        "company": "ServiceFirst",
        "remote_type": "Remote",
        "salary_min": 35000,
        "skills_required": ["communication", "customer service", "data entry"],
        "description": "Assist customers with inquiries, orders, and issue resolution."
    },
    {
        "title": "Office Administrator",
        "company": "BizOps Inc.",
        "remote_type": "On-Site",
        "salary_min": 40000,
        "skills_required": ["data entry", "communication", "planning", "management"],
        "description": "Keep office operations running smoothly and efficiently."
    }
]

# ============================================================================
# 🧠 RESUME ANALYZER - KEYWORD-BASED SKILL EXTRACTION
# ============================================================================

def analyze_resume(resume_text):
    """Analyze resume text and extract skills, experience level"""
    
    resume_lower = resume_text.lower()
    
    skill_keywords = {
        "design": ["design", "figma", "adobe", "sketch", "wireframe", "prototype"],
        "ux": ["ux", "user experience", "usability", "user journey"],
        "testing": ["testing", "qa", "quality assurance", "bug", "debug"],
        "management": ["manager", "lead", "senior", "leadership", "team"],
        "research": ["research", "analyze", "data analysis", "survey"],
        "development": ["python", "javascript", "react", "node", "html", "css", "api"],
        "data": ["data", "database", "sql", "excel", "analytics"],
        "driving": ["driving", "cdl", "trucking", "delivery", "fleet"],
        "logistics": ["logistics", "dispatch", "route planning", "warehouse", "inventory", "supply chain"],
        "communication": ["communication", "customer service"],
        "planning": ["planning", "scheduling"]
    }

    skills_found = []
    for skill, keywords in skill_keywords.items():
        if any(re.search(r'\b' + re.escape(kw) + r'\b', resume_lower) for kw in keywords):
            skills_found.append(skill)
    
    # Determine experience level based on years mentioned
    years_mentioned = len([
        line.lower() 
        for line in resume_text.split('\n') 
        if 'year' in line and ('experience' in line or 'of' in line)
    ])
    
    experience_level = {
        0: "junior",
        1: "mid-level", 
        2: "senior"
    }.get(years_mentioned, "unknown")
    
    # Extract industry interest (basic heuristic)
    industries = []
    if "tech" in resume_lower or "software" in resume_lower:
        industries.append("Technology")
    if "healthcare" in resume_lower or "medical" in resume_lower:
        industries.append("Healthcare")
    if "finance" in resume_lower or "banking" in resume_lower:
        industries.append("Finance")
    if "retail" in resume_lower or "store" in resume_lower:
        industries.append("Retail")
    
    return {
        "skills_found": list(set(skills_found)),
        "experience_level": experience_level,
        "industries_mentioned": list(set(industries))
    }

# ============================================================================
# 🔍 JOB MATCHING ALGORITHM
# ============================================================================

def match_jobs(resume_text, preferences):
    """Match jobs based on resume analysis and user preferences"""
    
    # Analyze resume first
    resume_analysis = analyze_resume(resume_text)
    resume_skills = set(resume_analysis['skills_found'])
    
    # Get preferences
    remote_pref = preferences.get('remote_pref', 'hybrid')
    min_salary = preferences.get('min_salary', 50000)
    industry_filter = preferences.get('industry', '')
    
    filtered_jobs = []
    
    for job in JOB_DATABASE:
        # Skip if salary requirement is too low (<80% of expected)
        if job['salary_min'] < min_salary * 0.8:
            continue
        
        # Skip based on remote preference
        if remote_pref == 'yes' and job['remote_type'] == 'On-Site':
            continue
        
        # Calculate skill match score
        matching_skills = resume_skills & set(job['skills_required'])
        total_job_skills = len(job['skills_required'])
        
        if total_job_skills > 0:
            skill_match_ratio = len(matching_skills) / total_job_skills
        else:
            skill_match_ratio = 1.0
        
        # Calculate match score (base 70 + bonus for skill overlap)
        base_score = 70
        skill_bonus = min(30, skill_match_ratio * 45)
        final_score = int(base_score + skill_bonus)
        
        # Bonus for experience level match
        if resume_analysis['experience_level'] == 'senior' and job.get('title', '').startswith('Senior'):
            final_score += 10
        elif resume_analysis['experience_level'] in ['junior', 'mid-level'] and 'Junior' in job.get('title', ''):
            final_score += 5
        
        # Filter by industry if specified
        if industry_filter and industry_filter.lower() not in [i.lower() for i in resume_analysis['industries_mentioned']]:
            continue
        
        filtered_jobs.append({
            'title': job['title'],
            'company': job['company'],
            'remote_type': job['remote_type'],
            'salary_min': job['salary_min'],
            'description': job['description'],
            'match_score': min(100, final_score),
            'matching_skills': list(matching_skills),
            'match_reason': (
                f"Great skill match ({len(matching_skills)}/{total_job_skills}) " + 
                f"+ {remote_pref.replace('no', 'office').replace('yes', 'remote')}. " +
                f"You're looking at: {final_score}%"
            )
        })
    
    # Sort by match score (highest first)
    filtered_jobs.sort(key=lambda x: x['match_score'], reverse=True)
    
    return filtered_jobs[:5]  # Return top 5 matches

# ============================================================================
# 🌐 API ENDPOINTS
# ============================================================================

@app.route("/")
def index():
    """Render main index page"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_endpoint():
    """Analyze resume and return skills/experience level"""
    data = request.json
    resume_text = data.get('resume_text', '')
    
    if not resume_text:
        return jsonify({'error': 'No resume text provided'}), 400
    
    analysis = analyze_resume(resume_text)
    
    return jsonify({
        'skills_found': analysis['skills_found'],
        'experience_level': analysis['experience_level'],
        'industries_mentioned': analysis['industries_mentioned']
    })

@app.route('/match', methods=['POST'])
def match_endpoint():
    """Find best job matches"""
    data = request.json
    resume_text = data.get('resume_text', '')
    preferences = {
        'remote_pref': data.get('remote_pref', 'hybrid'),
        'min_salary': data.get('min_salary', 50000),
        'industry': data.get('industry', '')
    }
    
    matches = match_jobs(resume_text, preferences)
    
    return jsonify(matches[:10])  # Return top 10 matches

@app.route('/jobs', methods=['GET'])
def list_all_jobs():
    """List all available jobs (for debugging)"""
    return jsonify(JOB_DATABASE)


# ============================================================================
# 📄 PDF UPLOAD ENDPOINT
# ============================================================================

@app.route('/upload-pdf', methods=['POST'])
def upload_pdf_endpoint():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'}), 400
    try:
        text = pdf_handler.extract_text_from_pdf(file.stream)
        if not text:
            return jsonify({'error': 'Could not extract text from PDF (file may be scanned or empty)'}), 400
        analysis = analyze_resume(text)
        return jsonify({
            'source': 'pdf',
            'filename': file.filename,
            'text_preview': text[:500],
            'skills_found': analysis['skills_found'],
            'experience_level': analysis['experience_level'],
            'industries_mentioned': analysis['industries_mentioned']
        })
    except Exception as e:
        return jsonify({'error': f'PDF processing failed: {str(e)}'}), 500


# ============================================================================
# 🐙 GITHUB ANALYSIS ENDPOINT
# ============================================================================

@app.route('/analyze-github', methods=['POST'])
def analyze_github_endpoint():
    data = request.json
    url = data.get('url', '')
    if not url:
        return jsonify({'error': 'No GitHub URL provided'}), 400
    result = github_analyzer.analyze_github_url(url)
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    return jsonify(result)


# ============================================================================
# 🌐 PORTFOLIO ANALYSIS ENDPOINT
# ============================================================================

@app.route('/analyze-portfolio', methods=['POST'])
def analyze_portfolio_endpoint():
    data = request.json
    url = data.get('url', '')
    if not url:
        return jsonify({'error': 'No portfolio URL provided'}), 400
    result = portfolio_analyzer.analyze_portfolio_url(url)
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    return jsonify(result)


def is_github_url(url):
    return re.match(r'https?://(www\.)?github\.com/.+', url) is not None


# ============================================================================
# 🔗 COMBINED ANALYSIS (merge all sources)
# ============================================================================

@app.route('/combine-analysis', methods=['POST'])
def combine_analysis_endpoint():
    data = request.json or {}
    resume_text = data.get('resume_text', '')
    urls = data.get('urls', [])

    all_skills = []
    all_industries = []
    experience_level = "unknown"
    sources_used = []
    url_results = []

    analysis = None
    if resume_text.strip():
        analysis = analyze_resume(resume_text)
        all_skills.extend(analysis['skills_found'])
        all_industries.extend(analysis['industries_mentioned'])
        if analysis['experience_level'] != 'unknown':
            experience_level = analysis['experience_level']
        sources_used.append("resume")

    for url in urls:
        if not url.strip():
            continue
        url = url.strip()
        if is_github_url(url):
            gh_result = github_analyzer.analyze_github_url(url)
            if 'error' not in gh_result:
                gh_skills = gh_result.get('skills_found', [])
                all_skills.extend(gh_skills)
                all_skills.append(gh_result.get('username', '').lower())
                sources_used.append(f"github:{gh_result.get('username', url)}")
                for lang in gh_result.get('top_languages', {}):
                    all_skills.append(lang.lower())
                url_results.append({
                    'url': url,
                    'type': 'github',
                    'title': gh_result.get('username', url),
                    'skills_count': len(gh_skills),
                    'details': f"{gh_result.get('public_repos', 0)} repos, {gh_result.get('followers', 0)} followers"
                })
            else:
                url_results.append({'url': url, 'type': 'github', 'title': url, 'skills_count': 0, 'details': gh_result.get('error', 'error')})
        else:
            pf_result = portfolio_analyzer.analyze_portfolio_url(url)
            if 'error' not in pf_result:
                pf_skills = pf_result.get('skills_found', [])
                all_skills.extend(pf_skills)
                sources_used.append(f"portfolio:{url}")
                url_results.append({
                    'url': url,
                    'type': 'portfolio',
                    'title': pf_result.get('title', url),
                    'skills_count': len(pf_skills),
                    'details': ''
                })
            else:
                url_results.append({'url': url, 'type': 'portfolio', 'title': url, 'skills_count': 0, 'details': pf_result.get('error', 'error')})

    for kw in ["tech", "software", "technology"]:
        if kw in ' '.join(all_skills).lower():
            all_industries.append("Technology")
            break

    resume_skills = list(set(analysis['skills_found'])) if analysis else []

    return jsonify({
        'skills_found': sorted(set(all_skills)),
        'resume_skills': resume_skills,
        'experience_level': experience_level,
        'industries_mentioned': sorted(set(all_industries)),
        'sources_used': sources_used,
        'url_results': url_results
    })


# ============================================================================
# 💬 FOLLOW-UP QUESTIONS (based on skills + career intent)
# ============================================================================

TOPIC_QUESTIONS = {
    "development": {
        "question": "What area of development interests you most?",
        "multi": True,
        "options": [
            {"value": "backend", "label": "Backend / APIs", "icon": "🔧"},
            {"value": "frontend", "label": "Frontend / UI", "icon": "🎨"},
            {"value": "fullstack", "label": "Full Stack", "icon": "⚡"},
            {"value": "devops", "label": "DevOps / Cloud", "icon": "☁️"},
            {"value": "mobile", "label": "Mobile Development", "icon": "📱"},
            {"value": "ml", "label": "Machine Learning / AI", "icon": "🧠"}
        ]
    },
    "design": {
        "question": "What type of design work do you do?",
        "multi": True,
        "options": [
            {"value": "ui", "label": "UI Design", "icon": "🖥️"},
            {"value": "ux", "label": "UX Research", "icon": "🔍"},
            {"value": "product", "label": "Product Design", "icon": "📐"},
            {"value": "graphic", "label": "Graphic / Visual Design", "icon": "🎯"},
            {"value": "motion", "label": "Motion / Animation", "icon": "🎬"}
        ]
    },
    "data": {
        "question": "What data role fits you best?",
        "multi": False,
        "options": [
            {"value": "analyst", "label": "Data Analyst", "icon": "📊"},
            {"value": "scientist", "label": "Data Scientist", "icon": "🧪"},
            {"value": "engineer", "label": "Data Engineer", "icon": "🏗️"},
            {"value": "ml", "label": "ML Engineer", "icon": "🤖"}
        ]
    },
    "management": {
        "question": "What level of management?",
        "multi": False,
        "options": [
            {"value": "team-lead", "label": "Team Lead", "icon": "👥"},
            {"value": "product-manager", "label": "Product Manager", "icon": "📋"},
            {"value": "engineering-manager", "label": "Engineering Manager", "icon": "⚙️"},
            {"value": "director", "label": "Director / VP", "icon": "🏢"}
        ]
    },
    "testing": {
        "question": "What kind of testing/QA?",
        "multi": True,
        "options": [
            {"value": "manual", "label": "Manual QA", "icon": "🔎"},
            {"value": "automation", "label": "Test Automation", "icon": "🤖"},
            {"value": "performance", "label": "Performance Testing", "icon": "📈"},
            {"value": "security", "label": "Security Testing", "icon": "🛡️"}
        ]
    },
    "driving": {
        "question": "What type of driving role?",
        "multi": True,
        "options": [
            {"value": "trucking", "label": "Trucking / Heavy Haul", "icon": "🚛"},
            {"value": "delivery", "label": "Local Delivery", "icon": "📦"},
            {"value": "fleet", "label": "Fleet Management", "icon": "⚙️"},
            {"value": "dispatch", "label": "Dispatch / Routing", "icon": "📡"}
        ]
    },
    "logistics": {
        "question": "Which area of logistics?",
        "multi": True,
        "options": [
            {"value": "warehouse", "label": "Warehouse Operations", "icon": "🏭"},
            {"value": "supply-chain", "label": "Supply Chain Management", "icon": "🔗"},
            {"value": "inventory", "label": "Inventory Management", "icon": "📋"},
            {"value": "planning", "label": "Logistics Planning", "icon": "🗺️"}
        ]
    },
    "communication": {
        "question": "What kind of customer-facing role?",
        "multi": False,
        "options": [
            {"value": "support", "label": "Customer Support", "icon": "🎧"},
            {"value": "sales", "label": "Sales / Account Management", "icon": "💼"},
            {"value": "reception", "label": "Reception / Front Desk", "icon": "🏢"},
            {"value": "service", "label": "Field Service", "icon": "🔧"}
        ]
    }
}

DREAM_JOB_QUESTIONS = [
    {
        "question": "What's your ideal work environment?",
        "multi": False,
        "options": [
            {"value": "startup", "label": "Startup — fast pace, big impact", "icon": "🚀"},
            {"value": "mid-size", "label": "Mid-size — growing team", "icon": "📈"},
            {"value": "enterprise", "label": "Enterprise — stability, scale", "icon": "🏛️"},
            {"value": "freelance", "label": "Freelance / Own business", "icon": "💼"}
        ]
    },
    {
        "question": "What motivates you most in a role?",
        "multi": True,
        "options": [
            {"value": "impact", "label": "Making a real impact", "icon": "💥"},
            {"value": "growth", "label": "Learning & growth opportunities", "icon": "🌱"},
            {"value": "compensation", "label": "High compensation", "icon": "💰"},
            {"value": "culture", "label": "Great team culture", "icon": "🤝"},
            {"value": "autonomy", "label": "Autonomy & flexibility", "icon": "🕊️"},
            {"value": "innovation", "label": "Cutting-edge tech / innovation", "icon": "💡"}
        ]
    }
]


@app.route('/follow-up-questions', methods=['POST'])
def follow_up_questions_endpoint():
    data = request.json or {}
    skills = data.get('skills', [])
    resume_skills = data.get('resume_skills', [])
    career_intent = data.get('career_intent', 'same')

    questions = []
    matched_topics = set()

    topics_to_check = resume_skills if resume_skills else skills
    for skill in topics_to_check:
        if skill in TOPIC_QUESTIONS:
            matched_topics.add(skill)

    for topic in matched_topics:
        questions.append(TOPIC_QUESTIONS[topic])

    if career_intent == 'dream':
        questions.extend(DREAM_JOB_QUESTIONS)

    if not questions:
        questions.append({
            "question": "What kind of role are you aiming for?",
            "multi": False,
            "options": [
                {"value": "technical", "label": "Technical / IC role", "icon": "💻"},
                {"value": "management", "label": "Management / Lead", "icon": "👥"},
                {"value": "creative", "label": "Creative / Design", "icon": "🎨"},
                {"value": "other", "label": "Something else", "icon": "🌟"}
            ]
        })

    return jsonify({'questions': questions, 'topic_count': len(matched_topics)})


# ============================================================================
# 🎯 MATCH FROM EXTERNAL SKILLS
# ============================================================================

@app.route('/match-from-skills', methods=['POST'])
def match_from_skills_endpoint():
    data = request.json
    skills = data.get('skills', [])
    preferences = {
        'remote_pref': data.get('remote_pref', 'hybrid'),
        'min_salary': data.get('min_salary', 50000),
        'industry': data.get('industry', '')
    }
    if not skills:
        return jsonify({'error': 'No skills provided'}), 400
    remote_pref = preferences['remote_pref']
    min_salary = preferences['min_salary']
    filtered_jobs = []
    for job in JOB_DATABASE:
        if job['salary_min'] < min_salary * 0.8:
            continue
        if remote_pref == 'yes' and job['remote_type'] == 'On-Site':
            continue
        matching_skills = set(skills) & set(job['skills_required'])
        total_job_skills = len(job['skills_required'])
        skill_match_ratio = len(matching_skills) / total_job_skills if total_job_skills > 0 else 1.0
        base_score = 70
        skill_bonus = min(30, skill_match_ratio * 45)
        final_score = int(base_score + skill_bonus)
        filtered_jobs.append({
            'title': job['title'],
            'company': job['company'],
            'remote_type': job['remote_type'],
            'salary_min': job['salary_min'],
            'description': job['description'],
            'match_score': min(100, final_score),
            'matching_skills': list(matching_skills),
            'match_reason': f"Skill match ({len(matching_skills)}/{total_job_skills}) + {remote_pref.replace('no', 'office').replace('yes', 'remote')}. Score: {final_score}%"
        })
    filtered_jobs.sort(key=lambda x: x['match_score'], reverse=True)
    return jsonify(filtered_jobs[:10])


# ============================================================================
# 🚀 RUN THE APP
# ============================================================================

if __name__ == '__main__':
    print('Job Finder Flask App Starting...')
    print('Opening http://localhost:5000 in browser...')
    app.run(debug=True, port=5000)
