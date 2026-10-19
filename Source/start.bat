@echo off
cd /d "%~dp0"
title Linh Ung Pagoda Audio Guide System

if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe start_all.py
) else (
    python start_all.py
)

pause
