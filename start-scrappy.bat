@echo off
echo ==========================================
echo        STARTING SCRAPPY APPLICATION
echo ==========================================
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org/
    pause
    exit /b 1
)

echo [1/4] Installing frontend dependencies...
cd frontend
if not exist node_modules (
    echo Installing npm packages...
    npm install
    if errorlevel 1 (
        echo ERROR: Failed to install frontend dependencies
        pause
        exit /b 1
    )
)

echo [2/4] Installing backend dependencies...
cd ..\backend
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
)

echo Activating virtual environment and installing packages...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install backend dependencies
    pause
    exit /b 1
)

echo [3/4] Starting backend server...
cd ..
start "SCRAPPY Backend" cmd /k "cd backend && venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo [4/4] Starting frontend server...
start "SCRAPPY Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ==========================================
echo     SCRAPPY IS STARTING UP...
echo ==========================================
echo.
echo Backend API:        http://localhost:8000
echo Frontend App:       http://localhost:3000
echo API Documentation:  http://localhost:8000/docs
echo.
echo Opening frontend in your default browser...
timeout /t 8 /nobreak >nul
start http://localhost:3000

echo.
echo ==========================================
echo        SCRAPPY SERVERS RUNNING!
echo ==========================================
echo.
echo Click on these links to access SCRAPPY:
echo.
echo 🌐 Frontend Application: http://localhost:3000
echo 🔧 Backend API:         http://localhost:8000
echo 📚 API Documentation:   http://localhost:8000/docs
echo.
echo To stop the servers:
echo - Close both command windows that opened
echo - Or press any key in this window to force stop
echo.
echo Press any key to stop all servers...
pause >nul

echo Stopping servers...
taskkill /f /im "node.exe" >nul 2>&1
taskkill /f /im "python.exe" >nul 2>&1
echo Servers stopped.
