@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\" (
  echo IrisFlow demo startup
  echo.
  echo Missing .venv folder.
  echo Create and install the Python environment first:
  echo   python -m venv .venv
  echo   .venv\Scripts\activate
  echo   python -m pip install -e .
  echo.
  pause
  exit /b 1
)

if not exist "frontend\node_modules\" (
  echo IrisFlow demo startup
  echo.
  echo Missing frontend\node_modules folder.
  echo Install frontend dependencies first:
  echo   cd frontend
  echo   npm install
  echo.
  pause
  exit /b 1
)

echo Starting IrisFlow backend and frontend...
echo Backend:  http://127.0.0.1:8765
echo Frontend: http://localhost:5173
echo.

start "IrisFlow Backend" cmd /k "cd /d ""%~dp0"" && call .venv\Scripts\activate && python -m irisflow.api.main"
start "IrisFlow Frontend" cmd /k "cd /d ""%~dp0frontend"" && npm run dev"

echo Demo servers are starting in separate windows.
pause
