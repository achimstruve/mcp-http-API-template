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
        const requestId = jsonRequest.id !== undefined ? jsonRequest.id : 0;
        
        const req = httpModule.request(requestOptions, (res) => {
            let responseData = '';
            let sseBuffer = '';
            
            // Handle different response types
            if (res.headers['content-type']?.includes('text/event-stream')) {
                // SSE response - parse event stream
                res.on('data', (chunk) => {
                    sseBuffer += chunk.toString();
                    const lines = sseBuffer.split('\n');
                    sseBuffer = lines.pop(); // Keep incomplete line in buffer
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.substring(6));
                                
                                // Ensure proper JSON-RPC format
                                if (data.jsonrpc && (data.result !== undefined || data.error !== undefined)) {
                                    // Make sure ID is properly set
                                    if (data.id === null || data.id === undefined) {
                                        data.id = requestId;
                                    }
                                    console.log(JSON.stringify(data));
                                    resolve();
                                    return;
                                }
                            } catch (parseError) {
                                // Ignore invalid JSON in SSE stream
                                console.error(`Failed to parse SSE line: ${line}`, parseError);
                            }
                        }
                    }
                });
                
                res.on('end', () => {
                    // If we get here without a proper response, send timeout
                    const timeoutResponse = {
                        jsonrpc: '2.0',
                        error: {
                            code: -32603,
                            message: 'No valid response received from server'
                        },
                        id: requestId
                    };
                    console.log(JSON.stringify(timeoutResponse));
                    resolve();
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
                            // Ensure proper ID
                            if (jsonResponse.id === null || jsonResponse.id === undefined) {
                                jsonResponse.id = requestId;
                            }
                            console.log(JSON.stringify(jsonResponse));
                        } else {
                            // Empty response
                            const emptyResponse = {
                                jsonrpc: '2.0',
                                error: {
                                    code: -32603,
                                    message: 'Empty response from server'
                                },
                                id: requestId
                            };
                            console.log(JSON.stringify(emptyResponse));
                        }
                        resolve();
                    } catch (parseError) {
                        const errorResponse = {
                            jsonrpc: '2.0',
                            error: {
                                code: -32700,
                                message: `Failed to parse response: ${parseError.message}`
                            },
                            id: requestId
                        };
                        console.log(JSON.stringify(errorResponse));
                        resolve();
                    }
                });
            }
            
            res.on('error', (error) => {
                const errorResponse = {
                    jsonrpc: '2.0',
                    error: {
                        code: -32603,
                        message: `Response error: ${error.message}`
                    },
                    id: requestId
                };
                console.log(JSON.stringify(errorResponse));
                resolve();
            });
        });
        
        req.on('error', (error) => {
            // Send error response in MCP format with proper ID
            const errorResponse = {
                jsonrpc: '2.0',
                error: {
                    code: -32603,
                    message: `Connection error: ${error.message}`
                },
                id: requestId
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
                id: requestId
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
    if (!line.trim()) return; // Skip empty lines
    
    try {
        const request = JSON.parse(line.trim());
        await sendToServer(request);
    } catch (error) {
        // Send error response for invalid JSON with ID 0 (fallback)
        const errorResponse = {
            jsonrpc: '2.0',
            error: {
                code: -32700,
                message: `Parse error: ${error.message}`
            },
            id: 0
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