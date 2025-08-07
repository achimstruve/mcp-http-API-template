@echo off
REM Windows batch script to run MCP server in LOCAL_MODE
REM This ensures correct package versions and environment
REM All output goes to stderr to avoid interfering with MCP JSON protocol

echo Starting MCP server in LOCAL_MODE for Windows... >&2

REM Set environment variable
set LOCAL_MODE=true

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Check if we're in the right directory
if not exist "server.py" (
    echo ERROR: server.py not found in directory %SCRIPT_DIR% >&2
    echo Current directory: %CD% >&2
    exit /b 1
)

REM Try to use uv if available, otherwise fall back to python
where uv >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo Using uv... >&2
    uv sync >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo ERROR: uv sync failed >&2
        exit /b 1
    )
    uv run python server.py
) else (
    echo uv not found, using python directly... >&2
    echo Installing/upgrading required packages... >&2
    python -m pip install --upgrade pip >nul 2>&1
    python -m pip install --upgrade "mcp>=1.12.0" "anyio>=4.4.0" python-dotenv >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Package installation failed >&2
        exit /b 1
    )
    python server.py
)

if %ERRORLEVEL% neq 0 (
    echo ERROR: Server failed to start >&2
    exit /b 1
)