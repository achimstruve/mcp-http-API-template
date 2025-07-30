# OAuth 2.1 Implementation Guide for MCP Server

This guide provides a step-by-step approach to transition the MCP server from API key authentication to OAuth 2.1 compliance as specified in the [MCP Authorization Specification](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization).

## Overview

The transition from API key authentication to OAuth 2.1 involves implementing the MCP server as an OAuth 2.1 resource server that validates access tokens for protected resources.

## Prerequisites

- Python 3.10+
- Understanding of OAuth 2.1 concepts
- HTTPS-enabled server (required for OAuth)
- Access to an OAuth 2.1 authorization server or ability to set one up

## Implementation Phases

### Phase 1: Infrastructure Setup

#### 1.1 Install Required Dependencies

Add the following to `pyproject.toml`:

```toml
dependencies = [
    # Existing dependencies...
    "authlib>=1.3.0",      # OAuth 2.1 client/server library
    "pyjwt>=2.8.0",        # JWT token handling
    "cryptography>=41.0.0", # Cryptographic operations
    "httpx>=0.25.0",       # Async HTTP client for token introspection
    "cachetools>=5.3.0",   # Caching for JWKS
]
```

#### 1.2 Create OAuth Module Structure

Create the following directory structure:

```
oauth/
├── __init__.py
├── config.py          # OAuth configuration management
├── token_validator.py # JWT token validation logic
├── resource_server.py # OAuth resource server implementation
├── jwks_client.py     # JWKS endpoint client
├── middleware.py      # ASGI middleware for OAuth
└── errors.py          # OAuth-specific error classes
```

### Phase 2: Core OAuth Implementation

#### 2.1 OAuth Configuration (`oauth/config.py`)

```python
from dataclasses import dataclass
from typing import Optional
import os

@dataclass
class OAuth2Config:
    """OAuth 2.1 configuration for MCP server"""
    issuer: str
    audience: str
    jwks_uri: str
    introspection_endpoint: Optional[str] = None
    required_scopes: Optional[list[str]] = None
    token_type: str = "Bearer"
    
    @classmethod
    def from_env(cls) -> 'OAuth2Config':
        """Load OAuth configuration from environment variables"""
        return cls(
            issuer=os.getenv("OAUTH_ISSUER", ""),
            audience=os.getenv("OAUTH_AUDIENCE", ""),
            jwks_uri=os.getenv("OAUTH_JWKS_URI", ""),
            introspection_endpoint=os.getenv("OAUTH_INTROSPECTION_ENDPOINT"),
            required_scopes=os.getenv("OAUTH_REQUIRED_SCOPES", "").split(",") if os.getenv("OAUTH_REQUIRED_SCOPES") else None
        )
```

#### 2.2 Token Validator Implementation

Key components to implement:

1. **JWT Validation**
   - Decode and verify JWT structure
   - Validate signature using JWKS
   - Check standard claims (iss, aud, exp, iat)
   - Verify custom claims as needed

2. **JWKS Client**
   - Fetch and cache JWKS from issuer
   - Handle key rotation
   - Implement TTL-based cache invalidation

3. **Token Introspection** (Optional)
   - Call introspection endpoint for opaque tokens
   - Cache introspection results
   - Handle introspection failures

#### 2.3 Resource Server Middleware

Replace the current `AuthWrapper` with OAuth2 middleware:

```python
class OAuth2Middleware:
    """ASGI middleware for OAuth 2.1 resource server"""
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Extract Bearer token
            # Validate token
            # Set auth context in scope
            # Handle OAuth errors with proper responses
```

### Phase 3: Security Implementation

#### 3.1 Token Security Features

1. **Audience Validation**
   - Strictly validate the `aud` claim matches server identifier
   - Reject tokens not intended for this server

2. **Token Binding**
   - Implement DPoP (Demonstrating Proof of Possession) support
   - Validate token binding to prevent token replay

3. **Scope-Based Authorization**
   - Define resource scopes (e.g., `mcp:tools:read`, `mcp:resources:write`)
   - Implement scope checking for each endpoint

#### 3.2 Error Handling

Implement proper OAuth 2.1 error responses:

```python
# 401 Unauthorized with WWW-Authenticate header
WWW-Authenticate: Bearer error="invalid_token", error_description="Token expired"

# 403 Forbidden for insufficient scopes
{
    "error": "insufficient_scope",
    "error_description": "Token lacks required scope 'mcp:tools:write'"
}
```

### Phase 4: Integration Points

#### 4.1 Update Server Startup

Modify `server.py` to:

1. Initialize OAuth configuration
2. Use OAuth2Middleware instead of AuthWrapper
3. Add OAuth health check endpoints

#### 4.2 Well-Known Endpoints

Implement discovery endpoints:

- `/.well-known/oauth-authorization-server` - OAuth metadata
- `/.well-known/resource-server` - Resource server metadata

### Phase 5: Migration Strategy

#### 5.1 Dual Authentication Support

Implement a transition period supporting both authentication methods:

```python
AUTH_MODE = os.getenv("AUTH_MODE", "oauth")  # oauth, api_key, both

if AUTH_MODE in ["both", "api_key"]:
    # Support legacy API key authentication
if AUTH_MODE in ["both", "oauth"]:
    # Support OAuth 2.1 authentication
```

#### 5.2 Client Migration Path

1. **Week 1-2**: Deploy OAuth support alongside API keys
2. **Week 3-4**: Provide migration tools and documentation
3. **Week 5-6**: Monitor OAuth adoption metrics
4. **Week 7-8**: Deprecate API key support with warnings
5. **Week 9+**: Remove API key support entirely

### Phase 6: Testing & Validation

#### 6.1 Unit Tests

Create comprehensive test suite:

```
tests/oauth/
├── test_token_validator.py
├── test_jwks_client.py
├── test_middleware.py
└── test_integration.py
```

#### 6.2 Security Testing

- Test token expiration handling
- Verify audience validation
- Test scope enforcement
- Validate error responses
- Test JWKS rotation handling

### Phase 7: Documentation

#### 7.1 Update CLAUDE.md

Add OAuth configuration section:

```markdown
## OAuth Configuration

Set the following environment variables:

- `OAUTH_ISSUER`: OAuth 2.1 issuer URL
- `OAUTH_AUDIENCE`: Expected audience for tokens
- `OAUTH_JWKS_URI`: JWKS endpoint URL
- `AUTH_MODE`: Authentication mode (oauth/api_key/both)
```

#### 7.2 Client Documentation

Create examples for:

- Obtaining access tokens
- Making authenticated requests
- Handling token refresh
- Error handling

### Phase 8: Monitoring & Observability

#### 8.1 Metrics to Track

- Authentication success/failure rates
- Token validation latency
- JWKS cache hit rates
- Token expiration patterns
- Client migration progress

#### 8.2 Logging

Implement structured logging for:

- Authentication attempts
- Token validation failures
- Security events
- Performance metrics

## Environment Variables

### Required for OAuth

```bash
# OAuth 2.1 Configuration
OAUTH_ISSUER=https://auth.example.com
OAUTH_AUDIENCE=https://mcp-server.example.com
OAUTH_JWKS_URI=https://auth.example.com/.well-known/jwks.json

# Optional
OAUTH_INTROSPECTION_ENDPOINT=https://auth.example.com/introspect
OAUTH_REQUIRED_SCOPES=mcp:read,mcp:write
AUTH_MODE=oauth  # oauth, api_key, both
```

### Migration Period

```bash
# Support both authentication methods
AUTH_MODE=both
API_KEY_DEPRECATION_WARNING=true
```

## Security Considerations

1. **Always use HTTPS** - OAuth 2.1 requires TLS
2. **Validate token audience** - Prevent token confusion attacks
3. **Implement rate limiting** - Protect against brute force
4. **Use short-lived tokens** - Minimize exposure window
5. **Monitor for anomalies** - Detect suspicious patterns

## Common Pitfalls

1. **Not validating audience** - Accepting tokens meant for other services
2. **Caching tokens too long** - Missing revocation events
3. **Ignoring token expiration** - Security vulnerability
4. **Poor error messages** - Makes debugging difficult
5. **No graceful degradation** - Service unavailable during auth issues

## Resources

- [OAuth 2.1 Specification](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1)
- [MCP Authorization Spec](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [OAuth 2.0 Security Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)

## Implementation Checklist

- [ ] Install OAuth dependencies
- [ ] Create OAuth module structure
- [ ] Implement token validator
- [ ] Create JWKS client with caching
- [ ] Implement OAuth middleware
- [ ] Add audience validation
- [ ] Implement scope checking
- [ ] Create proper error responses
- [ ] Add well-known endpoints
- [ ] Implement dual auth support
- [ ] Create comprehensive tests
- [ ] Update documentation
- [ ] Set up monitoring
- [ ] Plan client migration
- [ ] Deploy to staging
- [ ] Monitor adoption metrics
- [ ] Deprecate API keys
- [ ] Remove legacy auth code

## Next Steps

1. Review this implementation guide with your team
2. Set up an OAuth 2.1 authorization server (e.g., Auth0, Keycloak, or custom)
3. Start with Phase 1 infrastructure setup
4. Implement incrementally with thorough testing
5. Plan client migration strategy based on your user base