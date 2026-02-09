# Emergency fix script for Pylance import errors
# Run this if reloading VS Code doesn't fix the issue

Write-Host "🔧 Pyright/Pylance Emergency Fix Script" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Verify virtual environment
Write-Host "Step 1: Checking virtual environment..." -ForegroundColor Yellow
if (Test-Path "d:\ai\.venv\Scripts\python.exe") {
    Write-Host "✓ Virtual environment found" -ForegroundColor Green
    $pythonVersion = & "d:\ai\.venv\Scripts\python.exe" --version
    Write-Host "  Python version: $pythonVersion" -ForegroundColor Gray
} else {
    Write-Host "✗ Virtual environment NOT found!" -ForegroundColor Red
    Write-Host "  Please create a virtual environment first" -ForegroundColor Red
    exit 1
}

# Step 2: Verify packages are installed
Write-Host "`nStep 2: Verifying installed packages..." -ForegroundColor Yellow
$packages = @("torch", "python-dotenv", "langchain", "langchain-text-splitters", "datasets", "tqdm")
foreach ($pkg in $packages) {
    $installed = & "d:\ai\.venv\Scripts\python.exe" -m pip show $pkg 2>$null
    if ($installed) {
        Write-Host "✓ $pkg is installed" -ForegroundColor Green
    } else {
        Write-Host "✗ $pkg is NOT installed" -ForegroundColor Red
    }
}

# Step 3: Clear Pylance cache
Write-Host "`nStep 3: Clearing Pylance cache..." -ForegroundColor Yellow
$pylanceCache = "$env:LOCALAPPDATA\Microsoft\pylance"
if (Test-Path $pylanceCache) {
    try {
        Remove-Item -Recurse -Force "$pylanceCache\*" -ErrorAction Stop
        Write-Host "✓ Pylance cache cleared" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Could not clear cache (VS Code might be running)" -ForegroundColor Yellow
        Write-Host "  Close VS Code and run this script again" -ForegroundColor Yellow
    }
} else {
    Write-Host "ℹ No Pylance cache found (this is okay)" -ForegroundColor Gray
}

# Step 4: Verify configuration files
Write-Host "`nStep 4: Verifying configuration files..." -ForegroundColor Yellow
if (Test-Path "d:\ai\pyrightconfig.json") {
    Write-Host "✓ pyrightconfig.json exists" -ForegroundColor Green
} else {
    Write-Host "✗ pyrightconfig.json missing!" -ForegroundColor Red
}

if (Test-Path "d:\ai\.vscode\settings.json") {
    Write-Host "✓ .vscode/settings.json exists" -ForegroundColor Green
} else {
    Write-Host "✗ .vscode/settings.json missing!" -ForegroundColor Red
}

# Step 5: Test imports
Write-Host "`nStep 5: Testing imports at runtime..." -ForegroundColor Yellow
if (Test-Path "d:\ai\test_imports.py") {
    Write-Host "Running test_imports.py...`n" -ForegroundColor Gray
    & "d:\ai\.venv\Scripts\python.exe" "d:\ai\test_imports.py"
} else {
    Write-Host "⚠ test_imports.py not found, skipping" -ForegroundColor Yellow
}

# Final instructions
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "🎯 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Close VS Code COMPLETELY" -ForegroundColor White
Write-Host "2. Reopen VS Code" -ForegroundColor White
Write-Host "3. Press Ctrl+Shift+P → 'Python: Select Interpreter'" -ForegroundColor White
Write-Host "4. Choose: .venv (Python 3.10.11)" -ForegroundColor White
Write-Host "5. Wait for Pylance to finish indexing" -ForegroundColor White
Write-Host "`nIf errors persist, check the Pylance output:" -ForegroundColor Yellow
Write-Host "Ctrl+Shift+U → Select 'Pylance' from dropdown" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan
