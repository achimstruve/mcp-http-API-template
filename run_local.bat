@echo off
REM Windows batch script to run MCP server in LOCAL_MODE
REM This ensures correct package versions and environment

echo Starting MCP server in LOCAL_MODE for Windows...

REM Set environment variable
set LOCAL_MODE=true

REM Check if we're in the right directory
if not exist "server.py" (
    echo ERROR: server.py not found in current directory
    echo Please run this script from the project root directory
    pause
    exit /b 1
)

REM Try to use uv if available, otherwise fall back to python
where uv >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo Using uv...
    uv sync
    if %ERRORLEVEL% neq 0 (
        echo ERROR: uv sync failed
        pause
        exit /b 1
    )
    uv run python server.py
) else (
    echo uv not found, using python directly...
    echo Installing/upgrading required packages...
    python -m pip install --upgrade pip
    python -m pip install --upgrade "mcp>=1.12.0" "anyio>=4.4.0" python-dotenv
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Package installation failed
        pause
        exit /b 1
    )
    python server.py
)

if %ERRORLEVEL% neq 0 (
    echo ERROR: Server failed to start
    pause
    exit /b 1
)

pause