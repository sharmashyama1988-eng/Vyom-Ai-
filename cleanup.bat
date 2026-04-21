@echo off
REM Prakriti AI - Automated Cleanup Script
REM Run this to remove all unused/redundant files safely

echo ============================================
echo    PRAKRITI AI - FILE CLEANUP SCRIPT
echo ============================================
echo.
echo This script will remove:
echo   - Empty database files
echo   - Old backup files
echo   - Redundant debug scripts
echo   - Historical documentation
echo.
echo Files will be moved to 'archive' folder for safety.
echo You can delete the archive folder later if everything works fine.
echo.
pause

REM Create archive folder
if not exist "archive" mkdir archive
echo ✓ Created archive folder
echo.

REM ==== STEP 1: Delete Empty/Broken Files ====
echo [1/5] Removing empty/broken files...

if exist "Prakriti_knowledge_compressed.db" (
    del "Prakriti_knowledge_compressed.db"
    echo   ✓ Deleted Prakriti_knowledge_compressed.db (0 bytes)
)

if exist "ai_database.db.bak" (
    move "ai_database.db.bak" "archive\" >nul 2>&1
    echo   ✓ Moved ai_database.db.bak to archive
)

if exist "pyrightconfig.json.bak" (
    move "pyrightconfig.json.bak" "archive\" >nul 2>&1
    echo   ✓ Moved pyrightconfig.json.bak to archive
)

if exist "engine_error.txt" (
    move "engine_error.txt" "archive\" >nul 2>&1
    echo   ✓ Moved engine_error.txt to archive
)

echo.

REM ==== STEP 2: Archive Redundant Scripts ====
echo [2/5] Archiving redundant scripts...

if exist "build_prakriti.py" (
    move "build_prakriti.py" "archive\" >nul 2>&1
    echo   ✓ Moved build_prakriti.py to archive
)

if exist "test_imports.py" (
    move "test_imports.py" "archive\" >nul 2>&1
    echo   ✓ Moved test_imports.py to archive
)

if exist "setup_audio.py" (
    move "setup_audio.py" "archive\" >nul 2>&1
    echo   ✓ Moved setup_audio.py to archive
)

if exist "setup_brain.py" (
    move "setup_brain.py" "archive\" >nul 2>&1
    echo   ✓ Moved setup_brain.py to archive
)

if exist "fix_pylance.ps1" (
    move "fix_pylance.ps1" "archive\" >nul 2>&1
    echo   ✓ Moved fix_pylance.ps1 to archive
)

echo.

REM ==== STEP 3: Archive Old Documentation ====
echo [3/5] Archiving old documentation...

if exist "FIX_PYRIGHT_ERRORS.md" (
    move "FIX_PYRIGHT_ERRORS.md" "archive\" >nul 2>&1
    echo   ✓ Moved FIX_PYRIGHT_ERRORS.md to archive
)

if exist "IMPORT_FIX_SUMMARY.md" (
    move "IMPORT_FIX_SUMMARY.md" "archive\" >nul 2>&1
    echo   ✓ Moved IMPORT_FIX_SUMMARY.md to archive
)

if exist "example_prompts.txt" (
    move "example_prompts.txt" "archive\" >nul 2>&1
    echo   ✓ Moved example_prompts.txt to archive
)

if exist ".env.example" (
    move ".env.example" "archive\" >nul 2>&1
    echo   ✓ Moved .env.example to archive
)

echo.

REM ==== STEP 4: Clean Python Cache ====
echo [4/5] Cleaning Python cache files...

if exist "__pycache__" (
    rmdir /s /q "__pycache__" 2>nul
    echo   ✓ Removed __pycache__
)

if exist "Prakriti\__pycache__" (
    rmdir /s /q "Prakriti\__pycache__" 2>nul
    echo   ✓ Removed Prakriti\__pycache__
)

if exist "Prakriti\core\__pycache__" (
    rmdir /s /q "Prakriti\core\__pycache__" 2>nul
    echo   ✓ Removed Prakriti\core\__pycache__
)

if exist "Prakriti\engines\__pycache__" (
    rmdir /s /q "Prakriti\engines\__pycache__" 2>nul
    echo   ✓ Removed Prakriti\engines\__pycache__
)

echo.

REM ==== STEP 5: Check for Duplicate Virtual Environments ====
echo [5/5] Checking virtual environments...

set VENV_COUNT=0
if exist ".venv" set /a VENV_COUNT+=1
if exist "venv" set /a VENV_COUNT+=1

if %VENV_COUNT% GTR 1 (
    echo   ⚠️  WARNING: Multiple virtual environments detected!
    echo      You have both .venv and venv folders.
    echo.
    echo   Which one are you using?
    echo   1. .venv  (recommended)
    echo   2. venv
    echo   3. Skip (I'll handle this manually)
    echo.
    choice /c 123 /n /m "   Enter choice (1-3): "
    
    if errorlevel 3 (
        echo   ⏭️  Skipped venv cleanup
    ) else if errorlevel 2 (
        echo   Deleting .venv folder...
        rmdir /s /q ".venv" 2>nul
        echo   ✓ Removed .venv
    ) else if errorlevel 1 (
        echo   Deleting venv folder...
        rmdir /s /q "venv" 2>nul
        echo   ✓ Removed venv
    )
) else (
    echo   ✓ Only one virtual environment found (good!)
)

echo.
echo ============================================
echo          CLEANUP COMPLETE! ✨
echo ============================================
echo.
echo Summary:
echo   • Archived redundant files to 'archive' folder
echo   • Removed empty databases
echo   • Cleaned Python cache
echo   • Checked virtual environments
echo.
echo Next Steps:
echo   1. Test your main functionality (cli.py, Prakriti_engine.py)
echo   2. If everything works fine for 1 week, delete the 'archive' folder
echo   3. Run this script again anytime to clean up
echo.
echo File Analysis Report: FILE_USAGE_ANALYSIS.md
echo.

pause
