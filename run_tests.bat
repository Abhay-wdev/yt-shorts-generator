@echo off
title AI YouTube Shorts Generator - Test Suite
echo ========================================================
echo  Running E2E Production Pipeline Automated Tests
echo ========================================================
echo.
python -m pytest backend/tests/test_pipeline_e2e.py -v
echo.
echo ========================================================
pause
