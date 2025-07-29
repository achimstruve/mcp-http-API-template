#!/usr/bin/env python3
"""
Simple test script for MCP server
"""
import requests
import json

SERVER_URL = "https://mcptemplate.agenovation.ai:8443"

def test_sse_endpoint():
    """Test basic SSE endpoint connectivity"""
    print("Testing SSE endpoint...")
    try:
        response = requests.get(f"{SERVER_URL}/sse", stream=True, timeout=5)
        print(f"Status: {response.status_code}")
        
        # Read first few lines
        lines = []
        for line in response.iter_lines():
            if line:
                lines.append(line.decode('utf-8'))
            if len(lines) >= 2:
                break
        
        for line in lines:
            print(f"  {line}")
        
        print("✅ SSE endpoint is working!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_with_auth():
    """Test with authentication"""
    print("\nTesting with authentication...")
    headers = {"Authorization": "Bearer secret123"}
    try:
        response = requests.get(f"{SERVER_URL}/sse", headers=headers, stream=True, timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Authentication working!")
        else:
            print(f"❌ Authentication failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=== MCP Server Test ===")
    print(f"Server: {SERVER_URL}")
    print()
    
    if test_sse_endpoint():
        test_with_auth()