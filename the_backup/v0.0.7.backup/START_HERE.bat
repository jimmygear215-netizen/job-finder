@echo off
cd /d "%~dp0"
title Job Finder App - Flask Server
echo ==============================================
echo    JOBS FINDER APP - STARTING SERVER...
echo ==============================================
echo 
echo Opening http://localhost:5000 in browser...
python app.py

pause