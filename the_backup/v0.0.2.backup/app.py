"""
🎯 Job Finder App - Flask Backend
Analyzes resumes and recommends best-fit jobs!
"""

from flask import Flask, request, jsonify, render_template
import re
from datetime import datetime

app = Flask(__name__)

# ============================================================================
# 🎓 JOB DATABASE (Mock data - replace with real API later)
# ============================================================================

JOB_DATABASE = [
    {
        "title": "Product Designer",
        "company": "StartupX",
        "remote_type": "Remote",
        "salary_min": 80000,
        "skills_required": ["design", "ux", "figma", "adobe", "wireframe"],
        "description": "Design beautiful products that users love! 🎨"
    },
    {
        "title": "UX Researcher", 
        "company": "InnovateCo",
        "remote_type": "Hybrid",
        "salary_min": 75000,
        "skills_required": ["research", "analytics", "design", "data analysis"],
        "description": "Find out what users really want! 🧠"
    },
    {
        "title": "Senior Product Manager",
        "company": "TechGiant Inc.",
        "remote_type": "On-Site",
        "salary_min": 120000,
        "skills_required": ["management", "strategy", "leadership", "agile"],
        "description": "Lead the product vision! 🚀"
    },
    {
        "title": "Product Tester & Designer",
        "company": "TestMaster Ltd",
        "remote_type": "Remote",
        "salary_min": 65000,
        "skills_required": ["testing", "design", "qa", "quality assurance"],
        "description": "You're the Picasso of quality! 🎨🧪"
    },
    {
        "title": "UI Developer",
        "company": "CreativeStudio",
        "remote_type": "Remote",
        "salary_min": 90000,
        "skills_required": ["html", "css", "javascript", "react"],
        "description": "Build beautiful interfaces! 💻"
    },
    {
        "title": "Backend Engineer",
        "company": "DataCorp",
        "remote_type": "Hybrid",
        "salary_min": 110000,
        "skills_required": ["python", "database", "api", "cloud"],
        "description": "Build powerful backends! 🔧"
    },
    {
        "title": "Freelance Designer",
        "company": "GigHub",
        "remote_type": "Remote",
        "salary_min": 50000,
        "skills_required": ["design", "figma", "sketch", "adobe"],
        "description": "Work from anywhere! 🌍"
    }
]

# ============================================================================
# 🧠 RESUME ANALYZER - KEYWORD-BASED SKILL EXTRACTION
# ============================================================================

def analyze_resume(resume_text):
    """Analyze resume text and extract skills, experience level"""
    
    resume_lower = resume_text.lower()
    
    # Skill keywords mapping
    skill_keywords = {
        "design": ["design", "figma", "adobe", "sketch", "wireframe", "prototype", "ui"],
        "ux": ["ux", "user experience", "usability", "user journey"],
        "testing": ["test", "testing", "qa", "quality assurance", "bug", "debug"],
        "management": ["manager", "lead", "senior", "leadership", "team"],
        "research": ["research", "analyze", "data analysis", "survey"],
        "development": ["python", "javascript", "react", "node", "html", "css", "api"],
        "data": ["data", "database", "sql", "excel", "analytics"]
    }
    
    # Extract skills found
    skills_found = []
    for skill, keywords in skill_keywords.items():
        if any(kw in resume_lower for kw in keywords):
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
# 🚀 RUN THE APP
# ============================================================================

if __name__ == '__main__':
    print('Job Finder Flask App Starting...')
    print('Opening http://localhost:5000 in browser...')
    app.run(debug=True, port=5000)
