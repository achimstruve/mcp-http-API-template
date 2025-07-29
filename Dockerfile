# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install uv package manager
RUN pip install uv

# Install dependencies directly
RUN uv pip install --system mcp anyio typing-extensions python-dotenv uvicorn[standard] starlette

# Copy the rest of the application
COPY server.py auth.py ./

# Set environment variables for web deployment
ENV MCP_TRANSPORT=sse
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8899

# Expose both HTTP and HTTPS ports
EXPOSE 8899 8443

# Run the server directly
CMD ["python", "server.py"]