from flask import Flask, request, jsonify, render_template
import json
import requests
import pdf_handler
import github_analyzer
import portfolio_analyzer
import ai_analyzer

app = Flask(__name__)

# ============================================================================
# 🌐 PAGES
# ============================================================================

@app.route("/")
def index():
    return render_template('index.html')


# ============================================================================
# 📄 PDF UPLOAD
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
        return jsonify({
            'source': 'pdf',
            'filename': file.filename,
            'text_preview': text[:500],
            'char_count': len(text)
        })
    except Exception as e:
        return jsonify({'error': f'PDF processing failed: {str(e)}'}), 500


# ============================================================================
# 🐙 GITHUB ANALYSIS
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
# 🌐 PORTFOLIO ANALYSIS
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


# ============================================================================
# 🤖 AI — CONNECTION TEST
# ============================================================================

@app.route('/ai-test', methods=['POST'])
def ai_test_endpoint():
    data = request.json or {}
    endpoint = data.get('endpoint', 'http://localhost:1234/v1')
    api_key = data.get('api_key', '')
    try:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        r = requests.get(f"{endpoint}/models", headers=headers, timeout=10)
        if r.status_code == 200:
            models = r.json().get('data', [])
            model_name = models[0].get('id', 'unknown') if models else 'unknown'
            return jsonify({'connected': True, 'model': model_name, 'models_count': len(models)})
        return jsonify({'connected': False, 'error': f'HTTP {r.status_code}'}), 400
    except requests.RequestException as e:
        return jsonify({'connected': False, 'error': str(e)}), 400


# ============================================================================
# 🤖 AI — PROFILE ANALYSIS
# ============================================================================

@app.route('/ai-analyze', methods=['POST'])
def ai_analyze_endpoint():
    data = request.json or {}
    resume_text = data.get('resume_text', '')
    url_data = data.get('url_data', [])
    url_skills = data.get('url_skills', [])
    career_intent = data.get('career_intent', 'same')
    endpoint = data.get('endpoint', 'http://localhost:1234/v1')
    api_key = data.get('api_key', '')
    model = data.get('model', '')

    if not resume_text and not url_skills:
        return jsonify({'error': 'No resume text or URL skills provided'}), 400

    try:
        result = ai_analyzer.analyze_with_ai(resume_text, url_data, url_skills, career_intent, endpoint, api_key, model)
        return jsonify(result)
    except requests.RequestException as e:
        return jsonify({'error': f'AI connection failed: {str(e)}', 'fallback': True}), 503


# ============================================================================
# 🤖 AI — ADAPTIVE QUESTION
# ============================================================================

@app.route('/ai-question', methods=['POST'])
def ai_question_endpoint():
    data = request.json or {}
    profile = data.get('profile', {})
    career_intent = data.get('career_intent', 'same')
    qa_history = data.get('qa_history', [])
    question_number = data.get('question_number', 0)
    url_data = data.get('url_data', [])
    endpoint = data.get('endpoint', 'http://localhost:1234/v1')
    api_key = data.get('api_key', '')
    model = data.get('model', '')

    try:
        result = ai_analyzer.get_next_question(profile, career_intent, qa_history, question_number, url_data, endpoint, api_key, model)
        return jsonify(result)
    except requests.RequestException as e:
        return jsonify({'error': f'AI connection failed: {str(e)}', 'fallback': True}), 503


# ============================================================================
# 🤖 AI — ROLE SUGGESTIONS (replaces hardcoded job matching)
# ============================================================================

@app.route('/ai-suggest', methods=['POST'])
def ai_suggest_endpoint():
    data = request.json or {}
    profile = data.get('profile', {})
    career_intent = data.get('career_intent', 'same')
    qa_history = data.get('qa_history', [])
    endpoint = data.get('endpoint', 'http://localhost:1234/v1')
    api_key = data.get('api_key', '')
    model = data.get('model', '')

    try:
        result = ai_analyzer.suggest_roles(profile, career_intent, qa_history, endpoint, api_key, model)
        if isinstance(result, dict) and 'suggestions' in result:
            result = result['suggestions']
        if isinstance(result, dict) and 'error' in result:
            return jsonify(result)
        if not isinstance(result, list):
            result = [result] if isinstance(result, dict) else []
        return jsonify(result)
    except requests.RequestException as e:
        return jsonify({'error': f'AI connection failed: {str(e)}'}), 503


# ============================================================================
# 🚀 RUN
# ============================================================================

if __name__ == '__main__':
    print('Job Finder AI Starting...')
    print('Open http://localhost:5000 in browser...')
    app.run(debug=True, port=5000)
