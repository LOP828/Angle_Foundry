@echo off
setlocal
cd /d "%~dp0.."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_scheduler.ps1"
exit /b %ERRORLEVEL%
