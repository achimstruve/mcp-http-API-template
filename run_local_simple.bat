@echo off
REM Simple Windows batch script for MCP server in LOCAL_MODE
REM Assumes packages are already installed
REM All diagnostic output goes to stderr to avoid interfering with MCP JSON protocol

REM Set environment variable
set LOCAL_MODE=true

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Check if we're in the right directory
if not exist "server.py" (
    echo ERROR: server.py not found in directory %SCRIPT_DIR% >&2
    echo Current directory: %CD% >&2
    dir /b *.py >&2
    exit /b 1
)

REM Run with Python directly (assumes correct packages already installed)
python server.py

REM If Python fails, try with uv
if %ERRORLEVEL% neq 0 (
    echo Python failed, trying uv... >&2
    uv run python server.py
)

REM Exit with the same code as the server
exit /b %ERRORLEVEL%