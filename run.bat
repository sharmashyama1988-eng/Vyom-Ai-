
@echo off
echo Starting Vyom AI...
if not exist ".env" (
    echo NOTE: No .env file found. You will be asked for an API Key on first run.
)
VyomAI.exe
pause
