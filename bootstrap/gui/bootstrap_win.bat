@echo off
setlocal

echo *************************************************************
echo Welcome to the w3stringsx GUI bootstrapper
echo This script will check and install all required dependencies
echo *************************************************************
echo.
pause

echo.
echo Step 1: Checking python installation...
where python >nul 2>nul
if errorlevel 1 (
    echo Python not found. Installing Python 3.11 via winget...
    winget install -e --id Python.Python.3.11
    if errorlevel 1 (
        echo Failed to install Python. Please install manually from https://www.python.org/downloads/.
        pause
        exit /b 1
    )
) else (
    for /f "delims=" %%v in ('python -c "import sys; print(','.join([str(i) for i in sys.version_info[:3]]))"') do set pyver=%%v
    for /f "tokens=1,2,3 delims=, " %%a in ("%pyver%") do (
        set major=%%a
        set minor=%%b
    )
    if %major% LSS 3 (
        echo Python version too old. Installing Python 3.11 via winget...
        winget install -e --id Python.Python.3.11
    ) else if %major% EQU 3 if %minor% LSS 11 (
        echo Python version is less than 3.11. Installing Python 3.11 via winget...
        winget install -e --id Python.Python.3.11
    ) else (
        echo Found suitable Python version: %major%.%minor%
    )
)

echo.
echo Step 2: Ensuring pip installation...
python -m ensurepip --upgrade

echo.
echo Step 3: Installing/upgrading dependencies...
python -m pip install -r requirements.txt

echo.
echo Setup complete!
echo You can now run your application by double-clicking w3stringsx_gui.pyzw or running: python w3stringsx_gui.pyzw
pause
