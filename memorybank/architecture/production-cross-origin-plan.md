# Production Cross-Origin Session Management Plan

## Architecture Overview

### Production Deployment Scenario
- **Frontend (Astro + Preact)**: `https://yourcompany.com` (Static site or SSR)
- **Backend API**: `https://api.yourcompany.com` (FastAPI server)
- **Chat Components**: Preact components embedded in Astro pages make API calls

## Cross-Origin Session Management Strategy

### 1. **Backend API Configuration**

#### CORS Headers for Production
```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourcompany.com",
        "https://www.yourcompany.com",
        # Add other allowed origins
    ],
    allow_credentials=True,  # Critical for session cookies
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

#### Session Cookie Configuration for Cross-Origin
```yaml
# backend/config/app.yaml
session:
  cookie_name: "salient_session"
  cookie_max_age: 604800  # 7 days
  cookie_secure: true     # HTTPS only in production
  cookie_httponly: true   # XSS protection
  cookie_samesite: "none" # Required for cross-origin
  cookie_domain: ".yourcompany.com"  # Share across subdomains
```

### 2. **Astro Frontend Configuration**

#### Environment Configuration
```javascript
// astro.config.mjs
export default defineConfig({
  site: 'https://yourcompany.com',
  output: 'static', // or 'server' for SSR
  build: {
    assets: '_astro'
  }
});
```

#### API Base URL Configuration
```typescript
// src/lib/config.ts
export const API_CONFIG = {
  baseUrl: import.meta.env.PUBLIC_API_BASE_URL || 'https://api.yourcompany.com',
  credentials: 'include' // Include cookies in requests
};
```

### 3. **Preact Component Implementation**

#### Chat Component with Cross-Origin API Calls
```tsx
// src/components/ChatWidget.tsx
import { useState, useEffect } from 'preact/hooks';

export default function ChatWidget() {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);

  // Initialize session on component mount
  useEffect(() => {
    initializeSession();
  }, []);

  const initializeSession = async () => {
    try {
      const response = await fetch(`${API_CONFIG.baseUrl}/api/session`, {
        method: 'GET',
        credentials: 'include', // Include cookies for session
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        const sessionData = await response.json();
        setSessionId(sessionData.session_id);
        loadChatHistory(sessionData.session_id);
      }
    } catch (error) {
      console.error('Session initialization failed:', error);
    }
  };

  const loadChatHistory = async (sessionId) => {
    try {
      const response = await fetch(`${API_CONFIG.baseUrl}/api/chat/history`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        const history = await response.json();
        setMessages(history.messages || []);
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  };

  const sendMessage = async (content) => {
    try {
      const response = await fetch(`${API_CONFIG.baseUrl}/chat`, {
        method: 'POST',
        credentials: 'include', // Critical for session cookies
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: content })
      });
      
      if (response.ok) {
        const result = await response.text();
        // Update local state
        setMessages(prev => [
          ...prev,
          { role: 'human', content },
          { role: 'assistant', content: result }
        ]);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  return (
    <div class="chat-widget">
      <div class="messages">
        {messages.map((msg, i) => (
          <div key={i} class={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
      </div>
      <ChatInput onSend={sendMessage} />
    </div>
  );
}
```

### 4. **Backend API Enhancements**

#### Session Management API
```python
# backend/app/main.py

@app.get("/api/session")
async def get_session_info(request: Request):
    """Get current session information for frontend initialization."""
    session = get_current_session(request)
    if not session:
        # Create new session for new users
        return PlainTextResponse("No session", status_code=401)
    
    return {
        "session_id": str(session.id),
        "session_key": session.session_key[:8] + "...",  # Partial for security
        "created_at": session.created_at.isoformat(),
        "is_anonymous": session.is_anonymous
    }

@app.get("/api/chat/history")
async def get_chat_history(request: Request):
    """Get chat history for current session."""
    session = get_current_session(request)
    if not session:
        return PlainTextResponse("Unauthorized", status_code=401)
    
    chat_history = await _load_chat_history_for_session(session.id)
    return {"messages": chat_history}
```

### 5. **Environment Variables**

#### Frontend (.env)
```bash
PUBLIC_API_BASE_URL=https://api.yourcompany.com
```

#### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@db.yourcompany.com/salient

# API Keys
OPENROUTER_API_KEY=your_key_here

# CORS Origins (comma-separated)
ALLOWED_ORIGINS=https://yourcompany.com,https://www.yourcompany.com
```

## Deployment Architecture

### 1. **CDN/Edge Configuration**
```nginx
# nginx.conf or similar
server {
    listen 443 ssl;
    server_name yourcompany.com;
    
    # Static Astro site
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API proxy (optional - alternative to CORS)
    location /api/ {
        proxy_pass https://api.yourcompany.com/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_pass_header Set-Cookie;
    }
}
```

### 2. **Docker Deployment**
```dockerfile
# Dockerfile.frontend
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

```dockerfile
# Dockerfile.backend  
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Render backend + CDN-hosted frontend (Cloudflare/Netlify/Vercel)

This setup runs the FastAPI backend on Render and serves the Astro site via a CDN provider. Cross-origin requests must send and receive cookies (sessions) securely.

- Backend (Render): `https://api.yourcompany.com` (or Render-provided domain)
- Frontend (CDN): `https://yourcompany.com` or `https://yourcompany-frontend.app`

Backend requirements:
- Configure CORS allowlist to include all frontend origins (production and preview):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourcompany.com",
        "https://www.yourcompany.com",
        "https://yourcompany-frontend.app",
        "https://*.vercel.app",
        "https://*.netlify.app",
        "https://*.pages.dev"  # Cloudflare Pages
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)
```

- Session cookie settings for cross-origin:
```yaml
session:
  cookie_name: "salient_session"
  cookie_max_age: 604800
  cookie_secure: true       # HTTPS on Render
  cookie_httponly: true
  cookie_samesite: "none"  # Required for cross-origin cookies
  # cookie_domain optional; set if using subdomains like .yourcompany.com
```

Frontend requirements:
- Use `credentials: 'include'` on all fetches to backend endpoints so cookies flow:
```ts
await fetch(`${API_CONFIG.baseUrl}/chat`, {
  method: 'POST',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message })
});
```

- Provide `PUBLIC_API_BASE_URL` at build time (Astro) and ensure preview environments are allowed in CORS.

Operations on Render:
- Set env vars for `ALLOWED_ORIGINS` to the comma-separated list of frontend origins.
- Ensure TLS is enabled so `cookie_secure: true` is valid end-to-end.
- Consider Render autoscaling and background workers for long-running jobs. See Render’s product overview for capabilities like autoscaling, private networking, and managed Postgres. [Render](https://render.com/)

Security:
- Avoid wildcards in production allowlists where possible; prefer exact origins.
- Maintain separate staging domains and include them explicitly.


## Security Considerations

### 1. **Cookie Security**
- `Secure=true` for HTTPS-only transmission
- `HttpOnly=true` to prevent XSS attacks
- `SameSite=None` for cross-origin functionality
- `Domain=.yourcompany.com` for subdomain sharing

### 2. **CORS Configuration**
- Explicit origin allowlist (no wildcards in production)
- `credentials: true` for cookie transmission
- Restrict HTTP methods to necessary ones

### 3. **API Security**
- Rate limiting on endpoints
- Input validation and sanitization
- Session timeout handling
- HTTPS enforcement

## Testing Strategy

### 1. **Local Testing**
```bash
# Start backend
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000

# Start frontend (different terminal)
cd web && npm run dev -- --host 0.0.0.0 --port 4321

# Test cross-origin: http://localhost:4321 → http://localhost:8000
```

### 2. **Staging Environment**
- Deploy to staging.yourcompany.com
- Test with staging-api.yourcompany.com
- Verify cookie behavior across domains

### 3. **Production Validation**
- Monitor CORS errors in browser console
- Check session persistence across page reloads
- Verify chat history loading

## Implementation Steps

1. **Backend Updates**
   - [ ] Configure CORS middleware
   - [ ] Update session cookie settings
   - [ ] Add session API endpoints
   - [ ] Test cross-origin requests

2. **Frontend Updates**
   - [ ] Create production API configuration
   - [ ] Update Preact components for cross-origin
   - [ ] Implement proper error handling
   - [ ] Add session initialization logic

3. **Deployment**
   - [ ] Set up production domains
   - [ ] Configure SSL certificates
   - [ ] Deploy backend with proper CORS
   - [ ] Deploy frontend with API configuration

4. **Testing & Monitoring**
   - [ ] End-to-end testing
   - [ ] Performance monitoring
   - [ ] Error tracking setup
   - [ ] User session analytics

This architecture ensures proper cross-origin session management while maintaining security and performance in production.
