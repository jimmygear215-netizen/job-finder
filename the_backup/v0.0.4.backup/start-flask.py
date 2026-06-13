import os
import sys

# Activate virtual environment if exists
venv_path = os.path.join(os.path.dirname(__file__), 'venv')
if os.path.exists(venv_path):
    sys.path.insert(0, venv_path)
    
# Add working directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import and run the Flask app
from app import app

app.run(debug=True, port=5000)