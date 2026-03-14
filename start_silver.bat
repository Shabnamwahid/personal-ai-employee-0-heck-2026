@echo off
REM Start script for AI Employee - Silver Tier
REM Starts all watchers and orchestrator in separate terminal windows

echo Starting AI Employee - Silver Tier...
echo.

REM Get the current directory
set BASE_DIR=%~dp0

REM Start Filesystem Watcher
start "Filesystem Watcher" cmd /k "cd %BASE_DIR% && python scripts\filesystem_watcher.py AI_Employee_Vault"
timeout /t 2 /nobreak > nul

REM Start Gmail Watcher
start "Gmail Watcher" cmd /k "cd %BASE_DIR% && python scripts\gmail_watcher.py AI_Employee_Vault 120"
timeout /t 2 /nobreak > nul

REM Start LinkedIn Watcher (in background - longer interval)
start "LinkedIn Watcher" cmd /k "cd %BASE_DIR% && python scripts\linkedin_watcher.py AI_Employee_Vault 300"
timeout /t 2 /nobreak > nul

REM Start Orchestrator
start "Orchestrator" cmd /k "cd %BASE_DIR% && python scripts\orchestrator.py AI_Employee_Vault"

echo.
echo All services started!
echo.
echo Services running:
echo   - Filesystem Watcher (checking every 5s)
echo   - Gmail Watcher (checking every 2m)
echo   - LinkedIn Watcher (checking every 5m)
echo   - Orchestrator (processing every 10s)
echo.
echo To stop: Close all terminal windows
echo.
echo Check AI_Employee_Vault\Dashboard.md for status
echo.
pause
