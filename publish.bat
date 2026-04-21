@echo off
title ✦ Amit AI : Publisher ✦
cls
echo ==========================================
echo    AMIT AI : THE NEURAL HEART PUBLISHER
echo ==========================================
echo.

:: 1. Git Push
echo [1/3] Step: Pushing Source Code to GitHub...
git add .
git commit -m "Auto-update version 1.0.3: Neural Heart Integration"
git push origin main
if %ERRORLEVEL% NEQ 0 (
    echo [!] Git push failed. Please check your internet or git credentials.
) else (
    echo [+] GitHub upload successful!
)
echo.

:: 2. Build Package
echo [2/3] Step: Building Package (Wheel and SDist)...
python -m build
if %ERRORLEVEL% NEQ 0 (
    echo [!] Build failed. Installing 'build' package first...
    pip install build
    python -m build
)
echo [+] Build successful!
echo.

:: 3. Publish to PyPI
echo [3/3] Step: Publishing to PyPI...
echo [TIP] If you haven't uploaded to PyPI before, you'll need your token.
python -m twine upload dist/amit_sharma_neural_heart-1.0.3* --skip-existing
if %ERRORLEVEL% NEQ 0 (
    echo [!] Upload failed. Installing 'twine' first...
    pip install twine
    python -m twine upload dist/amit_sharma_neural_heart-1.0.3* --skip-existing
)
echo.
echo ==========================================
echo    DONE! Your Neural Heart is Worldwide.
echo ==========================================
pause
