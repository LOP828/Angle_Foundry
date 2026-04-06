@echo off
setlocal
cd /d "%~dp0.."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0unregister_startup_task.ps1"
exit /b %ERRORLEVEL%

