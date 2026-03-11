@echo off
REM Quick Start Script for AI Employee (Qwen Code Edition)
REM This script starts both the Watcher and Orchestrator

echo.
echo ================================================
echo   AI Employee - Bronze Tier (Qwen Code)
echo ================================================
echo.
echo Starting File System Watcher and Orchestrator...
echo.
echo Watcher: Monitors Inbox/ for new files
echo Orchestrator: Auto-processes files and updates Dashboard
echo.
echo Press Ctrl+C in each window to stop
echo.
pause

REM Start Watcher in new window
start "AI Employee - File Watcher" cmd /k "cd /d %~dp0 && python scripts\filesystem_watcher.py AI_Employee_Vault"

REM Wait a moment then start Orchestrator
timeout /t 2 /nobreak >nul

REM Start Orchestrator in new window
start "AI Employee - Orchestrator" cmd /k "cd /d %~dp0 && python scripts\orchestrator.py AI_Employee_Vault"

echo.
echo Both processes started!
echo.
echo To test:
echo   echo Hello ^> AI_Employee_Vault\Inbox\test.txt
echo.
echo To stop: Close both terminal windows or press Ctrl+C
echo.
