@echo off
setlocal
cd /d "%~dp0.."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0register_startup_task.ps1"
exit /b %ERRORLEVEL%

