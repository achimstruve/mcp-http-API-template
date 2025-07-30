#!/usr/bin/env node
/**
 * MCP Bridge for Claude Desktop - Converts stdio to HTTPS/SSE
 * This bridge allows Claude Desktop to connect to remote HTTPS MCP servers
 * 
 * Usage: node claude-desktop-bridge.js [server_url] [api_key]
 * Environment variables: MCP_SERVER_URL, MCP_API_KEY
 */

const https = require('https');
const http = require('http');
const readline = require('readline');
const { URL } = require('url');

// Configuration
const SERVER_URL = process.argv[2] || process.env.MCP_SERVER_URL || 'https://mcptemplate.agenovation.ai:8443/sse';
const API_KEY = process.argv[3] || process.env.MCP_API_KEY;

// Validate configuration
if (!SERVER_URL) {
    console.error('Error: Server URL is required');
    console.error('Usage: node claude-desktop-bridge.js <server_url> [api_key]');
    console.error('Or set MCP_SERVER_URL and MCP_API_KEY environment variables');
    process.exit(1);
}

// Parse server URL
let serverUrl;
try {
    serverUrl = new URL(SERVER_URL);
} catch (error) {
    console.error(`Error: Invalid server URL: ${SERVER_URL}`);
    process.exit(1);
}

// Determine HTTP module to use
const httpModule = serverUrl.protocol === 'https:' ? https : http;

// Build request options
const requestOptions = {
    hostname: serverUrl.hostname,
    port: serverUrl.port || (serverUrl.protocol === 'https:' ? 443 : 80),
    path: serverUrl.pathname,
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        'User-Agent': 'Claude-Desktop-Bridge/1.0'
    }
};

// Add authorization header if API key is provided
if (API_KEY) {
    requestOptions.headers['Authorization'] = `Bearer ${API_KEY}`;
}

// Setup stdio interface
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
});

// Function to send request to SSE server
function sendToServer(jsonRequest) {
    return new Promise((resolve, reject) => {
        const req = httpModule.request(requestOptions, (res) => {
            let responseData = '';
            
            // Handle different response types
            if (res.headers['content-type']?.includes('text/event-stream')) {
                // SSE response - parse event stream
                res.on('data', (chunk) => {
                    const lines = chunk.toString().split('\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.substring(6));
                                // Send response immediately for each SSE event
                                console.log(JSON.stringify(data));
                                
                                // If this looks like a final response, resolve
                                if (data.result !== undefined || data.error !== undefined) {
                                    resolve();
                                    return;
                                }
                            } catch (parseError) {
                                // Ignore invalid JSON in SSE stream
                            }
                        }
                    }
                });
            } else {
                // Regular JSON response
                res.on('data', (chunk) => {
                    responseData += chunk.toString();
                });
                
                res.on('end', () => {
                    try {
                        if (responseData.trim()) {
                            const jsonResponse = JSON.parse(responseData);
                            console.log(JSON.stringify(jsonResponse));
                        }
                        resolve();
                    } catch (parseError) {
                        reject(new Error(`Failed to parse response: ${parseError.message}`));
                    }
                });
            }
            
            res.on('error', (error) => {
                reject(new Error(`Response error: ${error.message}`));
            });
        });
        
        req.on('error', (error) => {
            // Send error response in MCP format
            const errorResponse = {
                jsonrpc: '2.0',
                error: {
                    code: -32603,
                    message: `Connection error: ${error.message}`
                },
                id: jsonRequest.id || null
            };
            console.log(JSON.stringify(errorResponse));
            resolve(); // Don't reject, as we've sent an error response
        });
        
        req.on('timeout', () => {
            req.destroy();
            const timeoutResponse = {
                jsonrpc: '2.0',
                error: {
                    code: -32603,
                    message: 'Request timeout'
                },
                id: jsonRequest.id || null
            };
            console.log(JSON.stringify(timeoutResponse));
            resolve();
        });
        
        // Set timeout
        req.setTimeout(30000);
        
        // Send the request
        req.write(JSON.stringify(jsonRequest));
        req.end();
    });
}

// Handle stdio input from Claude Desktop
rl.on('line', async (line) => {
    try {
        const request = JSON.parse(line.trim());
        await sendToServer(request);
    } catch (error) {
        // Send error response for invalid JSON
        const errorResponse = {
            jsonrpc: '2.0',
            error: {
                code: -32700,
                message: `Parse error: ${error.message}`
            },
            id: null
        };
        console.log(JSON.stringify(errorResponse));
    }
});

// Handle process termination
process.on('SIGINT', () => {
    process.exit(0);
});

process.on('SIGTERM', () => {
    process.exit(0);
});

// Log startup (to stderr so it doesn't interfere with MCP protocol)
console.error(`MCP Bridge started: ${SERVER_URL}`);
if (API_KEY) {
    console.error('Authentication: Enabled');
} else {
    console.error('Authentication: Disabled');
}