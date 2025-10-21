<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Cross-Origin Session Handling

This document explains session cookie behavior across different ports and origins in the Salient Sales Bot application, particularly for demo pages and development testing.

## Problem Description

The application has multiple frontend interfaces that need to share session state with the backend:

- **Backend Main Chat**: `localhost:8000/` (FastAPI server)
- **Astro Demo Pages**: `localhost:4321/demo/*` (Astro dev server)
- **Static Demo Pages**: `localhost:4321/htmx-chat.html` (served by Astro)
- **Widget Demos**: Embedded in various contexts

When demo pages running on `localhost:4321` make requests to the backend on `localhost:8000`, browser security restrictions prevent session cookies from being shared.

## Browser Security Model

### Same-Origin Policy
Browsers enforce the Same-Origin Policy where an origin is defined by:
- **Protocol**: `http://` vs `https://`
- **Host**: `localhost` vs `example.com`
- **Port**: `:8000` vs `:4321`

`localhost:8000` and `localhost:4321` are **different origins**.

### Cookie SameSite Behavior
- **`SameSite=Strict`**: Never sent cross-origin
- **`SameSite=Lax`**: Sent with top-level navigation but not AJAX/fetch
- **`SameSite=None`**: Sent cross-origin (requires `Secure=true`)
- **No SameSite**: Legacy behavior, similar to `Lax` in modern browsers

## Current Implementation

### Production Configuration (app.yaml)
```yaml
session:
  cookie_secure: false
  cookie_samesite: "lax"
  dev_relaxed_cookies: true
```

### Development Mode Detection
The middleware detects development mode when:
```python
dev_relaxed = session_config.get("dev_relaxed_cookies", False)
is_production_secure = session_config.get("cookie_secure", False)
is_dev_mode = dev_relaxed and not is_production_secure
```

### Cookie Settings by Mode

| Mode | SameSite | Secure | Behavior |
|------|----------|--------|----------|
| **Production** | `lax` | `true` | Secure cross-origin for HTTPS |
| **Development** | `None` | `false` | Relaxed for localhost testing |

## Solutions Implemented

### 1. Development Mode Relaxed Cookies
When `dev_relaxed_cookies: true` and `cookie_secure: false`:
- Sets `SameSite=None` with `Secure=false`
- Allows cross-origin session sharing between localhost ports
- **Security Note**: Only active in development mode

### 2. Session Bridging Mechanism
For demo pages that need to work with sessions:

```javascript
// Check if we're in a cross-origin context
const isCrossOrigin = window.location.origin !== CHAT_BASE;

if (isCrossOrigin) {
  // Add session information to requests manually
  const sessionId = getSessionFromStorage(); // Custom implementation
  headers['X-Session-ID'] = sessionId;
}
```

## Testing Approaches

### Option 1: Same-Origin Testing
Visit the backend directly at `http://localhost:8000/` for session-aware testing.

### Option 2: Development Mode
Enable relaxed cookies in `app.yaml`:
```yaml
session:
  dev_relaxed_cookies: true
  cookie_secure: false
```

### Option 3: API Testing
Use curl with explicit session cookies:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: salient_session=YOUR_SESSION_KEY" \
  -d '{"message": "Test message"}'
```

## Demo Page Limitations

### Current Limitations
1. **Session Isolation**: Demo pages create separate sessions from main backend
2. **Message Persistence**: Messages saved to demo page sessions, not user's main session
3. **Configuration Mismatch**: Frontend and backend may use different endpoint preferences

### Workarounds
1. **Testing**: Use backend main chat for session-aware testing
2. **Development**: Enable `dev_relaxed_cookies` for cross-origin session sharing
3. **Documentation**: Clear user guidance about demo vs production behavior

## Security Considerations

### Production Safety
- Relaxed cookie settings are **only active in development**
- Production mode maintains secure `SameSite=Lax` behavior
- Configuration-driven feature flags prevent accidental security relaxation

### Development Trade-offs
- Cross-origin session sharing enables better demo testing
- Reduced security in development environment only
- Clear configuration boundaries between dev and production

## Configuration Reference

### Enable Cross-Origin Sessions (Development Only)
```yaml
# backend/config/app.yaml
session:
  cookie_secure: false  # Must be false for dev relaxed mode
  dev_relaxed_cookies: true  # Enable cross-origin session sharing
```

### Production Security (Default)
```yaml
# backend/config/app.yaml
session:
  cookie_secure: true   # HTTPS only
  cookie_samesite: "lax"  # CSRF protection
  dev_relaxed_cookies: false  # No relaxed mode
```

## Future Enhancements

### Session API Endpoint
Create a dedicated endpoint for session information sharing:
```
GET /api/session/info
POST /api/session/bridge
```

### Widget Session Configuration
Allow widgets to specify session handling preferences:
```javascript
<script src="chat-widget.js" 
        data-session-mode="shared|isolated"
        data-backend="http://localhost:8000">
</script>
```

### Proxy-Based Solution
Use Astro's dev proxy to serve all content from the same origin during development.

## Troubleshooting

### Symptoms: "Messages not persisting in demo pages"
- **Cause**: Cross-origin session isolation
- **Solution**: Enable `dev_relaxed_cookies` or test via backend directly

### Symptoms: "Session cookies not sent with AJAX requests"
- **Cause**: `SameSite=Lax` prevents cross-origin AJAX cookie transmission
- **Solution**: Check if `dev_relaxed_cookies` is enabled and `cookie_secure: false`

### Symptoms: "Different session IDs in browser tools vs backend logs"
- **Cause**: Frontend creating separate sessions due to cookie restrictions
- **Solution**: Verify session cookie configuration and cross-origin handling
