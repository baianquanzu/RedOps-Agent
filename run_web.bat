@echo off
chcp 65001 >nul
title RedOps Web
cd /d "%~dp0web"
python -m uvicorn main:app --host 0.0.0.0 --port 8000
