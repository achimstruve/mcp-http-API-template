# MCP Demo Server

This is a demonstration of a FastMCP server that provides simple API tools and resources.

## Features

- Addition tool: Adds two numbers together
- Secret word tool: Returns a predefined secret word
- Dynamic greeting resource: Provides personalized greetings

## Getting Started

### Prerequisites

- Python 3.10+
- uv (Ultra-fast Python package installer and resolver)

### Installation

1. Install uv if you haven't already:
   ```
   pip install uv
   ```

2. Clone or create your project directory and navigate into it:
   ```
   mkdir mcp-demo-server
   cd mcp-demo-server
   ```

3. Install dependencies using uv:
   ```
   uv sync
   ```

   This will create a virtual environment and install all dependencies defined in `pyproject.toml`.

### Running the Server

To start the server directly:
```
uv run python server.py
```

To test with MCP Inspector:
```
npx @modelcontextprotocol/inspector "uv" "run" "python" "server.py"
```

### Claude Desktop Integration

For reliable Claude Desktop integration, this project uses a batch file approach:

#### Method 1: Batch File Approach (Recommended)

1. The project includes `run_mcp_server.bat` which handles all path resolution
2. Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "Demo": {
      "command": "C:\\path\\to\\your\\project\\run_mcp_server.bat"
    }
  }
}
```

**Replace** `C:\\path\\to\\your\\project\\` with your actual project directory path.

#### Method 2: Direct UV Command (Alternative)

If you prefer the direct approach:

```json
{
  "mcpServers": {
    "Demo": {
      "command": "C:\\Users\\[username]\\.local\\bin\\uv.exe",
      "args": [
        "run",
        "python",
        "server.py"
      ],
      "cwd": "C:\\path\\to\\your\\project"
    }
  }
}
```

**Note**: Replace paths with your actual paths. Find your uv path with `where.exe uv`.

### Why Batch File Approach?

The batch file approach is more reliable because:
- **Path Resolution**: Handles complex Windows paths better
- **Environment Setup**: Ensures correct working directory and environment
- **Compatibility**: Works better with Node.js process spawning in Claude Desktop
- **Debugging**: Easier to troubleshoot path and environment issues

### Troubleshooting

#### Common Issues and Solutions

**1. "spawn uv ENOENT" errors:**
- **Cause**: Claude Desktop can't find the uv executable
- **Solution**: Use the batch file approach (Method 1) or verify your uv path with `where.exe uv`

**2. "Server disconnected" errors:**
- **Cause**: Dependencies not installed or Python version mismatch
- **Solution**: Run `uv sync` in your project directory

**3. "ModuleNotFoundError: No module named 'mcp'":**
- **Cause**: Dependencies not installed in the correct environment
- **Solution**: Ensure you've run `uv sync` and the batch file is using the correct paths

**4. Server shows as "failed" in Claude Desktop:**
- **Test locally first**: Run `uv run python server.py` to verify it works
- **Check paths**: Ensure all paths in your configuration are correct
- **Use batch file**: Switch to the batch file approach for more reliability

#### Testing Your Setup

1. **Test locally:**
   ```powershell
   uv run python server.py
   ```

2. **Test batch file:**
   ```powershell
   .\run_mcp_server.bat
   ```

3. **Test with MCP Inspector:**
   ```powershell
   npx @modelcontextprotocol/inspector "uv" "run" "python" "server.py"
   ```

If all three work locally, the issue is likely in your Claude Desktop configuration.

## API Reference

### Tools

#### add(a: int, b: int) -> int

Adds two numbers together and returns the result.

Example usage:
```python
result = add(5, 7)  # Returns 12
```

#### secret_word() -> str

Returns the secret word.

Example usage:
```python
word = secret_word()  # Returns "ApplesAreRed998"
```

### Resources

#### greeting://{name}

Returns a personalized greeting for the provided name.

Example: `greeting://John` returns "Hello, John!"

## Development

To contribute to this project:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[MIT](LICENSE)
