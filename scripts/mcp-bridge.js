#!/usr/bin/env node
/**
 * Simple MCP stdio-to-SSE bridge for Claude Desktop
 * Supports Bearer token authentication
 */

const https = require('https');
const readline = require('readline');

// Configuration from environment or command line
const SERVER_URL = process.argv[2] || process.env.MCP_SERVER_URL;
const API_KEY = process.env.MCP_API_KEY;

if (!SERVER_URL) {
  console.error('Usage: node mcp-bridge.js <server_url>');
  console.error('Or set MCP_SERVER_URL environment variable');
  process.exit(1);
}

// Parse URL
const url = new URL(SERVER_URL);
const options = {
  hostname: url.hostname,
  port: url.port || 443,
  path: url.pathname,
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream'
  }
};

// Add authorization header if API key provided
if (API_KEY) {
  options.headers['Authorization'] = `Bearer ${API_KEY}`;
}

// Setup readline for stdio
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

// Handle stdio input
rl.on('line', (line) => {
  try {
    const request = JSON.parse(line);
    
    // Send request to SSE endpoint
    const req = https.request(options, (res) => {
      let buffer = '';
      
      res.on('data', (chunk) => {
        buffer += chunk.toString();
        
        // Process SSE lines
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep incomplete line in buffer
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              
              // Forward response to stdout
              if (data.result || data.error) {
                console.log(JSON.stringify(data));
              }
            } catch (e) {
              // Ignore parse errors
            }
          }
        }
      });
      
      res.on('error', (err) => {
        console.log(JSON.stringify({
          jsonrpc: '2.0',
          error: {
            code: -32603,
            message: `Connection error: ${err.message}`
          },
          id: request.id
        }));
      });
    });
    
    req.on('error', (err) => {
      console.log(JSON.stringify({
        jsonrpc: '2.0',
        error: {
          code: -32603,
          message: `Request error: ${err.message}`
        },
        id: request.id
      }));
    });
    
    // Send request
    req.write(JSON.stringify(request));
    req.end();
    
  } catch (e) {
    console.error(`Parse error: ${e.message}`, e);
  }
});

// Handle errors
process.on('uncaughtException', (err) => {
  console.error('Uncaught exception:', err);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled rejection:', reason);
});