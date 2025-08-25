# Production Deployment Configuration

## Environment Variables for Cross-Origin Production

### Required Environment Variables

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://username:password@your-db-host.com:5432/salient_production

# OpenRouter API Configuration  
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Cross-Origin Session Configuration for Production
PRODUCTION_CROSS_ORIGIN=true
COOKIE_SECURE=true
COOKIE_DOMAIN=.yourcompany.com

# CORS Origins (comma-separated)
ALLOWED_ORIGINS=https://yourcompany.com,https://www.yourcompany.com
```

### Optional Environment Variables

```bash
# Redis for Session Storage (recommended for production)
REDIS_URL=redis://your-redis-host.com:6379/0

# Application Settings Override
APP_NAME=Salient Sales Bot Production
LOG_LEVEL=INFO

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Development Settings (set to false in production)
FRONTEND_DEBUG=false
EXPOSE_BACKEND_LOGS=false
```

## Astro Frontend Configuration

### Environment Variables (.env)

```bash
# Backend API URL
PUBLIC_API_BASE_URL=https://api.yourcompany.com

# Optional: Enable debug logging
PUBLIC_DEBUG=false
```

### astro.config.mjs

```javascript
import { defineConfig } from 'astro/config';
import preact from '@astrojs/preact';

export default defineConfig({
  site: 'https://yourcompany.com',
  output: 'static', // or 'server' for SSR
  integrations: [
    preact({
      compat: true // For React compatibility
    })
  ],
  build: {
    assets: '_astro'
  },
  // Optional: Custom headers for production
  server: {
    headers: {
      'Access-Control-Allow-Credentials': 'true'
    }
  }
});
```

## Backend CORS Configuration

Add CORS middleware to your FastAPI application:

```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware
import os

# Get allowed origins from environment
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]

if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,  # Critical for session cookies
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Set-Cookie"]
    )
```

## Docker Deployment Configuration

### Backend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

```dockerfile
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# Serve the built application
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - PRODUCTION_CROSS_ORIGIN=true
      - COOKIE_SECURE=true
      - COOKIE_DOMAIN=.yourcompany.com
      - ALLOWED_ORIGINS=https://yourcompany.com,https://www.yourcompany.com
    depends_on:
      - postgres

  frontend:
    build: ./web
    ports:
      - "3000:3000"
    environment:
      - PUBLIC_API_BASE_URL=https://api.yourcompany.com

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=salient_production
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Nginx Reverse Proxy Configuration

```nginx
# /etc/nginx/sites-available/yourcompany.com
server {
    listen 443 ssl http2;
    server_name yourcompany.com www.yourcompany.com;

    # SSL configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;

    # Frontend (Astro static site)
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 443 ssl http2;
    server_name api.yourcompany.com;

    # SSL configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;

    # Backend API
    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Important for session cookies
        proxy_pass_header Set-Cookie;
        proxy_cookie_domain localhost $host;
        proxy_cookie_path / /;
    }
}
```

## Production Deployment Checklist

### Backend Deployment
- [ ] Set all required environment variables
- [ ] Configure CORS with explicit allowed origins
- [ ] Enable HTTPS and secure cookies
- [ ] Set appropriate cookie domain for cross-origin sharing
- [ ] Configure production database
- [ ] Set up Redis for session storage (optional but recommended)
- [ ] Configure logging and monitoring
- [ ] Test cross-origin API calls

### Frontend Deployment
- [ ] Configure PUBLIC_API_BASE_URL
- [ ] Build and deploy static assets
- [ ] Configure CDN if needed
- [ ] Test cross-origin requests with credentials
- [ ] Verify session persistence across page reloads
- [ ] Test chat functionality end-to-end

### Domain Configuration
- [ ] Set up SSL certificates for both domains
- [ ] Configure DNS records
- [ ] Test cookie sharing across subdomains
- [ ] Verify CORS preflight requests work correctly

### Monitoring & Testing
- [ ] Set up health checks for both services
- [ ] Monitor CORS errors in browser console
- [ ] Track session creation and persistence metrics
- [ ] Test with different browsers and devices
- [ ] Verify mobile device compatibility
