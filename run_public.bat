@echo off
TITLE Vyom AI - Public Local Server
CLS

echo ========================================================
echo   VYOM AI - PUBLIC SERVER (LOCALHOST)
echo ========================================================
echo.
echo [1] Starting Vyom AI (Flask Server)...
start "Vyom AI Server" cmd /k "python app.py"

echo.
echo [2] Waiting for server to initialize...
timeout /t 5 >nul

echo.
echo ========================================================
echo   NGROK SETUP (Public Link)
echo ========================================================
echo.
echo Agar aapke paas Ngrok ka Static Domain hai 
echo (jaise: vyom-ai.ngrok-free.app), to niche type karein.
echo.
echo Agar nahi hai, to bas ENTER dabayein (Random link milega).
echo.
set /p domain="Enter Domain (ya ENTER dabayein): "

if "%domain%"=="" (
    echo.
    echo Starting Random Public Link...
    ngrok http 5000
) else (
    echo.
    echo Starting Fixed Domain: %domain%...
    ngrok http --domain=%domain% 5000
)

pause