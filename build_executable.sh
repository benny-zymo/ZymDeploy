#!/bin/bash
echo "===== ZymDeploy Executable Builder (Linux/macOS) ====="
echo ""
echo "This script will create an executable for the ZymDeploy application."
echo ""

# Check if Python is installed
if ! command -v python &> /dev/null
then
    echo "Error: Python is not installed or not in PATH."
    echo "Please install Python 3.8 or later and try again."
    exit 1
fi

# Create a virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment."
        exit 1
    fi
fi

echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment."
    exit 1
fi

echo "Installing dependencies..."
# Install required packages
python -m pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies."
    exit 1
fi

# Install PyInstaller if not already installed
pip install pyinstaller
if [ $? -ne 0 ]; then
    echo "Error: Failed to install PyInstaller."
    exit 1
fi

echo "Building executable..."
# Run PyInstaller to create the executable
pyinstaller --name ZymDeploy \
            --paths . \
            --add-data "zymosoft_assistant/templates:zymosoft_assistant/templates" \
            --hidden-import=pandas \
            --hidden-import=numpy \
            --hidden-import=matplotlib \
            --hidden-import=PIL \
            --hidden-import=jinja2 \
            --hidden-import=sklearn \
            --hidden-import=scipy \
            --hidden-import=cv2 \
            --hidden-import=zymosoft_assistant.scripts.Routine_VALIDATION_ZC_18022025 \
            --hidden-import=zymosoft_assistant.scripts.getDatasFromWellResults \
            --hidden-import=zymosoft_assistant.scripts.processAcquisitionLog \
            --hidden-import=zymosoft_assistant.scripts.home_made_tools_v3 \
            --noconsole \
            --onefile \
            zymosoft_assistant/main.py

if [ $? -ne 0 ]; then
    echo "Error: Failed to build executable."
    exit 1
fi

echo ""
echo "===== Build completed successfully! ====="
echo ""
echo "The executable has been created in the 'dist' folder."
echo "You can find it at: $(pwd)/dist/ZymDeploy"
echo ""
