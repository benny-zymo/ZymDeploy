@echo off
echo ===== ZymDeploy Executable Builder (Windows) =====
echo.
echo This script will create an executable for the ZymDeploy application.
echo.

REM Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.8 or later and try again.
    exit /b 1
)

REM Create a virtual environment
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo Error: Failed to create virtual environment.
        exit /b 1
    )
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to activate virtual environment.
    exit /b 1
)

echo Installing dependencies...
REM Install required packages
python -m pip install --upgrade pip
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to install dependencies.
    exit /b 1
)

REM Install PyInstaller if not already installed
pip install pyinstaller
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to install PyInstaller.
    exit /b 1
)

echo Building executable...
REM Run PyInstaller to create the executable
pyinstaller --name ZymDeploy ^
            --paths . ^
--add-data "zymosoft_assistant\templates;zymosoft_assistant\templates" ^
--add-data "zymosoft_assistant\assets\icons\icon.png;zymosoft_assistant\assets\icons" ^
--add-data "zymosoft_assistant\assets\icons\icon.ico;zymosoft_assistant\assets\icons" ^
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
            --icon=zymosoft_assistant\assets\icons\icon.ico ^
            zymosoft_assistant\main.py

if %ERRORLEVEL% neq 0 (
    echo Error: Failed to build executable.
    exit /b 1
)

echo.
echo ===== Build completed successfully! =====
echo.
echo The executable has been created in the 'dist' folder.
echo You can find it at: %CD%\dist\ZymDeploy.exe
echo.
