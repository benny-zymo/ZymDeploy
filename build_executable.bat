@echo off
echo ===== ZymDeploy Executable Builder =====
echo.
echo This script will create an executable for the ZymDeploy application.
echo.

REM Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.8 or later and try again.
    pause
    exit /b 1
)

if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment.
    pause
    exit /b 1
)

echo Installing dependencies...
REM Install required packages
python -m pip install --upgrade pip
REM Use --only-binary option to force pip to use pre-built wheels for packages that might require compilation
pip install -r requirements.txt --only-binary=numpy,scipy,scikit-learn
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies.
    pause
    exit /b 1
)

echo Verifying NumPy installation...
python check_numpy_version.py
if %errorlevel% neq 0 (
    echo Error: NumPy verification failed.
    pause
    exit /b 1
)

REM Install PyInstaller if not already installed
pip install pyinstaller
if %errorlevel% neq 0 (
    echo Error: Failed to install PyInstaller.
    pause
    exit /b 1
)

echo Building executable...
REM Run PyInstaller to create the executable
pyinstaller --name ZymDeploy ^
            --icon=zymosoft_assistant\assets\icons\icon.ico ^
            --add-data "zymosoft_assistant\assets;zymosoft_assistant\assets" ^
            --add-data "zymosoft_assistant\templates;zymosoft_assistant\templates" ^
            --add-data "zymosoft_assistant\scripts\*.csv;zymosoft_assistant\scripts" ^
            --hidden-import=pandas ^
            --hidden-import=numpy ^
            --hidden-import=matplotlib ^
            --hidden-import=PIL ^
            --hidden-import=jinja2 ^
            --hidden-import=sklearn ^
            --hidden-import=scipy ^
            --hidden-import=cv2 ^
            --hidden-import=zymosoft_assistant.scripts.Routine_VALIDATION_ZC_18022025 ^
            --hidden-import=zymosoft_assistant.scripts.getDatasFromWellResults ^
            --hidden-import=zymosoft_assistant.scripts.processAcquisitionLog ^
            --hidden-import=zymosoft_assistant.scripts.home_made_tools_v3 ^
            --noconsole ^
            --onefile ^
            zymosoft_assistant\main.py

if %errorlevel% neq 0 (
    echo Error: Failed to build executable.
    pause
    exit /b 1
)

echo.
echo ===== Build completed successfully! =====
echo.
echo The executable has been created in the "dist" folder.
echo You can find it at: %CD%\dist\ZymDeploy.exe
echo.
pause
