# Job Finder App - README

## What is this?
A Flask web app that analyzes resumes and recommends best-fit jobs!

## Quick Start

### 1. Install Dependencies
```bash
pip install flask pywebview streamlit requests
```

### 2. Run the App
```bash
cd c:\jimdev\job_finder\the_working
python app.py
```

### 3. Open in Browser
Go to: http://localhost:5000

## Features

- Analyzes resume content for skills & experience
- Detects keywords (design, Python, React, etc.)
- Asks questions about preferences (remote/salary/industry)
- Matches against job database
- Provides match scores & explanations
- Can be wrapped in PyWebView or Electron later

## How It Works

1. Paste Resume - App analyzes skills & experience level
2. Answer Questions - Remote preference, salary, industry
3. Get Recommendations - Top 5-10 job matches with scores

## Tech Stack

- Backend: Flask (Python)
- Frontend: HTML + JavaScript (no build needed!)
- Desktop Wrapper: PyWebView / Electron (future)

## Project Structure

the_working/
- app.py              Main backend
- index.html          Frontend UI
- style.css           Styles (embedded now)
- requirements.txt    Python dependencies
- README.md           This file

## Future Enhancements

- PDF resume upload support
- Real job board API integration
- Export matches to PDF
- Desktop app with PyWebView
- Vercel deployment for cloud hosting
