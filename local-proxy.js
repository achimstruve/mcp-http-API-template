#!/usr/bin/env node

const { EventSource } = require('eventsource');
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');

const REMOTE_SERVER = 'https://34.145.94.60:8443';
const LOCAL_PORT = 3000;

const app = express();

// Proxy configuration that ignores SSL certificate issues
const proxyOptions = {
  target: REMOTE_SERVER,
  changeOrigin: true,
  secure: false, // This allows self-signed certificates
  ws: true,
  onError: (err, req, res) => {
    console.error('Proxy error:', err);
    res.status(500).send('Proxy error');
  }
};

// Create proxy middleware
app.use('/sse', createProxyMiddleware(proxyOptions));

// Start local server
app.listen(LOCAL_PORT, () => {
  console.log(`Local proxy server running at http://localhost:${LOCAL_PORT}/sse`);
  console.log(`Proxying to: ${REMOTE_SERVER}/sse`);
  console.log('\nTo add to Claude Code:');
  console.log(`claude mcp add demo-server --transport sse http://localhost:${LOCAL_PORT}/sse`);
});