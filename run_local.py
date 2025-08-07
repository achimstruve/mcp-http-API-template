#!/usr/bin/env python3
"""
Local runner script for Claude Desktop that ensures correct package versions.
This script works around Windows package installation issues.
"""

import sys
import subprocess
import os

# Set LOCAL_MODE environment variable
os.environ['LOCAL_MODE'] = 'true'

def check_and_install_packages():
    """Check and install required packages with correct versions."""
    try:
        import mcp
        import anyio
        
        # Check versions
        mcp_version = getattr(mcp, '__version__', '0.0.0')
        anyio_version = getattr(anyio, '__version__', '0.0.0')
        
        # Parse versions
        mcp_major, mcp_minor = map(int, mcp_version.split('.')[:2])
        anyio_major, anyio_minor = map(int, anyio_version.split('.')[:2])
        
        # Check if versions are adequate
        if mcp_major < 1 or (mcp_major == 1 and mcp_minor < 12):
            print(f"mcp version {mcp_version} is too old, need >= 1.12.0", file=sys.stderr)
            return False
            
        if anyio_major < 4 or (anyio_major == 4 and anyio_minor < 4):
            print(f"anyio version {anyio_version} is too old, need >= 4.4.0", file=sys.stderr)
            return False
            
        return True
        
    except ImportError:
        print("Required packages not found", file=sys.stderr)
        return False

def main():
    """Main entry point."""
    # Check if packages are correct
    if not check_and_install_packages():
        print("ERROR: Package versions are incompatible!", file=sys.stderr)
        print("Please run: pip install --upgrade 'mcp>=1.12.0' 'anyio>=4.4.0'", file=sys.stderr)
        sys.exit(1)
    
    # Import and run the server
    try:
        # Import here after checking versions
        from server import mcp
        
        print("Starting MCP server in LOCAL MODE", file=sys.stderr)
        print("Transport: stdio (for Claude Desktop)", file=sys.stderr)
        print("Authentication: DISABLED", file=sys.stderr)
        print("HTTPS: DISABLED", file=sys.stderr)
        
        # Run the server
        mcp.run()
        
    except Exception as e:
        print(f"Error running server: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()