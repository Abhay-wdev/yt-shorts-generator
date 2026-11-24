@echo off
title AI YouTube Shorts Generator - Backend API (FastAPI)
echo ========================================================
echo  Starting AI YouTube Shorts Studio - Backend API Server
echo ========================================================
echo Running on http://127.0.0.1:8000
echo Swagger UI docs available at http://127.0.0.1:8000/docs
echo.
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
pause
