@echo off
echo ==================================================
echo       VYOM AI - KOBOLDPP LAUNCHER (GT 730)
echo ==================================================
echo.

if not exist "koboldcpp.exe" (
    echo ❌ koboldcpp.exe not found!
    echo 👉 Please download it from: https://github.com/LostRuins/koboldcpp/releases
    echo    and place it in this folder: D:\ai
    pause
    exit
)

echo 🔍 Looking for GGUF models...
set MODEL_FILE=""
for %%f in (*.gguf) do set MODEL_FILE="%%f"

if %MODEL_FILE% == "" (
    echo ❌ No .gguf model file found in this folder.
    echo.
    echo 👉 Step 1: Download a model (e.g., Llama-3-8B-Quantized)
    echo    Link: https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf
    echo.
    echo 👉 Step 2: Put the file in D:\ai folder.
    echo.
    pause
    exit
)

echo ✅ Found Model: %MODEL_FILE%
echo 🚀 Launching Optimized for GT 730 (Kepler)...

:: --usecublas: Uses NVIDIA GPU
:: --gpulayers 12: Puts 12 layers on GPU (Safe for 2GB/4GB VRAM)
:: --contextsize 2048: Standard context
:: --stream: Faster response
koboldcpp.exe %MODEL_FILE% --usecublas --gpulayers 12 --contextsize 2048 --stream --port 5001

pause
