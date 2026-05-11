@echo off
title EOD Tracker — Build Script
echo ============================================
echo  EOD Tracker Build Script
echo  CodeClouds Dev  ^|  Developed by Abhinay Kumar
echo ============================================
echo.

:: Find Python
set PYTHON=C:\Users\%USERNAME%\AppData\Local\Python\bin\python.exe
if not exist "%PYTHON%" (
    set PYTHON=python
)

echo [1/3] Installing / updating dependencies...
"%PYTHON%" -m pip install PyQt6 openpyxl pyinstaller --quiet
if errorlevel 1 (
    echo ERROR: pip install failed. Make sure Python is installed.
    pause & exit /b 1
)

echo [2/3] Building EXE with PyInstaller...
"%PYTHON%" -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name=EODTracker ^
    --add-data="assets;assets" ^
    --add-data="templates;templates" ^
    --hidden-import=openpyxl ^
    --hidden-import=sqlite3 ^
    main.py

if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    pause & exit /b 1
)

echo.
echo [3/3] EXE built successfully!
echo Output: dist\EODTracker.exe
echo.

:: Optional: build installer with Inno Setup
set INNO="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist %INNO% (
    echo Building installer with Inno Setup...
    if not exist "dist\installer" mkdir "dist\installer"
    %INNO% installer\setup.iss
    if errorlevel 1 (
        echo WARNING: Installer build failed. EXE is still available at dist\EODTracker.exe
    ) else (
        echo Installer built: dist\installer\EODTracker_Setup_v1.1.0.exe
    )
) else (
    echo NOTE: Inno Setup not found. Installer skipped.
    echo Install Inno Setup from https://jrsoftware.org/isinfo.php then re-run this script.
)

echo.
echo ============================================
echo  Build complete!
echo  EXE:       dist\EODTracker.exe
echo  Installer: dist\installer\ (if Inno Setup installed)
echo ============================================
pause
