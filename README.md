# MCP Demo Server

This is a demonstration of a FastMCP server that provides simple API tools and resources.

## Features

- Addition tool: Adds two numbers together
- Secret word tool: Returns a predefined secret word
- Dynamic greeting resource: Provides personalized greetings

## Getting Started

### Prerequisites

- Python 3.6+
- pip (Python package installer)

### Installation

1. Create a new directory for your project and navigate into it:
   ```
   mkdir mcp-demo-server
   cd mcp-demo-server
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```
   pip install mcp
   ```

### Running the Server

To start the server directly:
```
python server.py
```

To test with MCP Inspector:
```
npx @modelcontextprotocol/inspector "venv/Scripts/python.exe" "server.py"
```

To use with Claude Desktop, add this to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "Demo": {
      "command": "C:/Users/user/path/to/your/project/venv/Scripts/python.exe",
      "args": [
        "C:\\Users\\user\\path\\to\\your\\project\\server.py"
      ],
      "env": {
        "PYTHONPATH": "C:/Users/user/path/to/your/project"
      }
    }
  }
}
```

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
