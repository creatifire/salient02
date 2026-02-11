<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# API Access Patterns for Different Frameworks and Platforms

> **Last Updated**: December 31, 2025  
> **Status**: Architecture Design  
> **Related**: [multi-tenant-security.md](multi-tenant-security.md), [endpoints.md](endpoints.md)

## Overview

This document outlines secure API access patterns for integrating Salient chat capabilities across different web frameworks, static site generators, and hosting platforms. It addresses the challenge of securely accessing Salient APIs from various architectures while maintaining security best practices.

**Core Principle**: Never expose API keys in client-side code. Always proxy requests through a backend layer.

---

## Table of Contents

1. [Framework-Specific Patterns](#framework-specific-patterns)
2. [Static Site Generator Compatibility Matrix](#static-site-generator-compatibility-matrix)
3. [API Key Security Model](#api-key-security-model)
4. [Headless CMS Integration Architecture](#headless-cms-integration-architecture)
5. [Implementation Examples](#implementation-examples)
6. [Best Practices](#best-practices)

---

## Framework-Specific Patterns

### Pattern A: Traditional Backend Frameworks

**Frameworks**: WordPress (PHP), Django (Python), Ruby on Rails, Laravel, NestJS, Express.js

**Architecture**:
```
[Browser] → [Customer Backend] → [Salient API]
            (stores API key)     (authenticated)
```

**Key Characteristics**:
- ✅ Full backend with persistent server processes
- ✅ API key stored in environment variables or secure configuration
- ✅ Server-side session management
- ✅ Complete control over request/response flow

**Implementation Approach**:
- Store Salient API key in server environment
- Create backend endpoint that proxies to Salient
- Add authentication/authorization if needed
- Handle CORS, rate limiting, logging server-side

**Security Level**: 🟢 **Highest** - API key never exposed to client

---

### Pattern B: Modern Server-Side Rendering (SSR) Frameworks

**Frameworks**: Next.js, Nuxt.js, SvelteKit, Remix, Astro (SSR mode), SolidStart

**Architecture**:
```
[Browser] → [SSR Framework API Route] → [Salient API]
            (serverless/server)          (authenticated)
```

**Key Characteristics**:
- ✅ Hybrid rendering (static + server)
- ✅ Built-in API routes or server endpoints
- ✅ API key in environment variables
- ✅ Can use server-side data fetching

**Implementation Approach**:
- Use framework's API route/endpoint feature
- Store API key in `.env.local` (server-only)
- Client fetches from same-origin API route
- API route proxies to Salient with authentication

**Security Level**: 🟢 **Highest** - API key stays on server

---

#### Next.js Implementation

**API Route** (`pages/api/chat.ts` or `app/api/chat/route.ts`):
```typescript
// Next.js App Router (Next.js 13+)
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { message, sessionId } = await request.json();
    
    const response = await fetch(
      `${process.env.SALIENT_API_URL}/accounts/${process.env.SALIENT_ACCOUNT}/agents/${process.env.SALIENT_AGENT}/chat`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Account-API-Key': process.env.SALIENT_API_KEY!, // Secret!
        },
        body: JSON.stringify({ message, session_id: sessionId }),
      }
    );
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to send message' },
      { status: 500 }
    );
  }
}
```

**Client Component** (`components/Chat.tsx`):
```typescript
'use client';

export function ChatWidget() {
  const sendMessage = async (message: string) => {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, sessionId }),
    });
    return response.json();
  };
  
  // ... rest of component
}
```

**Environment Variables** (`.env.local`):
```env
SALIENT_API_URL=https://api.salient.ai
SALIENT_ACCOUNT=acme
SALIENT_AGENT=chat1
SALIENT_API_KEY=sk_acme_secret_abc123...
```

---

#### Nuxt.js Implementation

**Server Route** (`server/api/chat.post.ts`):
```typescript
export default defineEventHandler(async (event) => {
  const { message, sessionId } = await readBody(event);
  const config = useRuntimeConfig();
  
  try {
    const response = await $fetch(
      `${config.salientApiUrl}/accounts/${config.salientAccount}/agents/${config.salientAgent}/chat`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Account-API-Key': config.salientApiKey,
        },
        body: { message, session_id: sessionId },
      }
    );
    
    return response;
  } catch (error) {
    throw createError({
      statusCode: 500,
      message: 'Failed to send message',
    });
  }
});
```

**Client Component** (`components/Chat.vue`):
```vue
<script setup lang="ts">
const sendMessage = async (message: string) => {
  const response = await $fetch('/api/chat', {
    method: 'POST',
    body: { message, sessionId: sessionId.value },
  });
  return response;
};
</script>
```

**Configuration** (`nuxt.config.ts`):
```typescript
export default defineNuxtConfig({
  runtimeConfig: {
    // Server-only variables (never sent to client)
    salientApiUrl: process.env.SALIENT_API_URL,
    salientAccount: process.env.SALIENT_ACCOUNT,
    salientAgent: process.env.SALIENT_AGENT,
    salientApiKey: process.env.SALIENT_API_KEY,
  },
});
```

---

#### SvelteKit Implementation

**Server Endpoint** (`src/routes/api/chat/+server.ts`):
```typescript
import { json } from '@sveltejs/kit';
import { SALIENT_API_KEY, SALIENT_API_URL, SALIENT_ACCOUNT, SALIENT_AGENT } from '$env/static/private';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ request }) => {
  const { message, sessionId } = await request.json();
  
  try {
    const response = await fetch(
      `${SALIENT_API_URL}/accounts/${SALIENT_ACCOUNT}/agents/${SALIENT_AGENT}/chat`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Account-API-Key': SALIENT_API_KEY,
        },
        body: JSON.stringify({ message, session_id: sessionId }),
      }
    );
    
    const data = await response.json();
    return json(data);
  } catch (error) {
    return json({ error: 'Failed to send message' }, { status: 500 });
  }
};
```

**Client Component** (`src/routes/+page.svelte`):
```svelte
<script lang="ts">
  const sendMessage = async (message: string) => {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, sessionId }),
    });
    return response.json();
  };
</script>
```

**Environment Variables** (`.env`):
```env
SALIENT_API_URL=https://api.salient.ai
SALIENT_ACCOUNT=acme
SALIENT_AGENT=chat1
SALIENT_API_KEY=sk_acme_secret_abc123...
```

---

#### Astro SSR Implementation

**API Endpoint** (`src/pages/api/chat.ts`):
```typescript
import type { APIRoute } from 'astro';

export const POST: APIRoute = async ({ request }) => {
  const { message, sessionId } = await request.json();
  
  try {
    const response = await fetch(
      `${import.meta.env.SALIENT_API_URL}/accounts/${import.meta.env.SALIENT_ACCOUNT}/agents/${import.meta.env.SALIENT_AGENT}/chat`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Account-API-Key': import.meta.env.SALIENT_API_KEY,
        },
        body: JSON.stringify({ message, session_id: sessionId }),
      }
    );
    
    const data = await response.json();
    return new Response(JSON.stringify(data), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to send message' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
};
```

**Configuration** (`astro.config.mjs`):
```javascript
export default defineConfig({
  output: 'server', // Enable SSR
  adapter: node(), // or vercel(), netlify(), cloudflare()
});
```

---

#### Astro: SSR vs Static + Serverless Functions

**Important**: Astro supports BOTH approaches. Choose based on your needs:

**Option 1: Astro SSR Mode (Shown Above)**
- Uses `output: 'server'` or `output: 'hybrid'` configuration
- API routes in `src/pages/api/` become server endpoints
- Entire site deployed as server application
- Pages can be dynamically rendered or prerendered
- **Deployment**: Node.js server, Vercel Functions, Netlify Functions, Cloudflare Workers
- **Use when**: You need dynamic pages OR prefer unified Astro API experience

**Option 2: Static Astro + Separate Serverless Functions (Pattern C Below)**
- Uses `output: 'static'` (default Astro configuration)
- Separate function files outside `src/` (e.g., `netlify/functions/`, `api/`)
- Static HTML served from global CDN (maximum performance)
- Platform-specific function syntax (not Astro API)
- **Deployment**: CDN for static files + serverless platform for functions
- **Use when**: Site is mostly/entirely static OR you want maximum performance and lowest cost

**Deployment & Performance Comparison**:

| Aspect | SSR Mode (Option 1) | Static + Functions (Option 2) |
|--------|---------------------|-------------------------------|
| **Build Output** | Server application | Static HTML + separate functions |
| **Hosting** | Single deployment target | Two-part (CDN + functions) |
| **Page Load Speed** | Server-rendered on-demand | CDN-cached (faster) |
| **Cold Start Impact** | Affects page loads | Only affects API calls |
| **Cost** | Higher (always running) | Lower (static = cheap/free) |
| **API Route Path** | `/api/chat` (Astro routing) | `/.netlify/functions/chat` (platform-specific) |
| **Complexity** | Simpler (unified codebase) | Two file structures to manage |

**Example Project Structures**:

```bash
# Option 1: SSR Mode
my-astro-site/
├── src/
│   ├── pages/
│   │   ├── index.astro         # Can be static or dynamic
│   │   └── api/
│   │       └── chat.ts          # Astro API endpoint
│   └── components/
└── astro.config.mjs             # output: 'server'

# Option 2: Static + Functions
my-astro-site/
├── src/
│   ├── pages/
│   │   └── index.astro          # Always static
│   └── components/
├── netlify/
│   └── functions/
│       └── chat.js               # Separate serverless function
└── astro.config.mjs              # output: 'static' (default)
```

**Recommendation**: 
- **Marketing/blog sites with chat**: Use **Static + Functions** (Pattern C) for maximum performance
- **Web apps with user dashboards**: Use **SSR mode** (Pattern B) for dynamic content
- **Hybrid sites**: Use `output: 'hybrid'` with `prerender` directive for best of both worlds

---

### Pattern C: Static Sites with Serverless Functions

**Generators**: Astro (static), Hugo, Jekyll, Eleventy, Gatsby, VuePress, Hexo, Docusaurus

**Architecture**:
```
[Browser] → [Serverless Function] → [Salient API]
   (CDN)    (same domain/host)      (authenticated)
```

**Key Characteristics**:
- ✅ Static HTML/JS served from CDN
- ✅ Serverless functions for API calls
- ✅ Environment variables in hosting platform
- ⚠️ Cold start latency on first request
- ⚠️ Platform-specific function syntax

**Implementation Approach**:
- Deploy static site to hosting platform
- Add serverless function for API proxy
- Configure environment variables in host dashboard
- Client calls same-origin function endpoint

**Security Level**: 🟢 **High** - API key in serverless environment (not in client bundle)

---

### Pattern D: WordPress Plugin

**Architecture**:
```
[WordPress Admin] → [PHP Backend] → [Salient API]
    (config UI)     (stores API key)  (authenticated)
         ↓
[WordPress Frontend] → [PHP Endpoint] → [Salient API]
    (chat widget)       (authenticated)
```

**Key Characteristics**:
- ✅ Traditional PHP backend with database
- ✅ Plugin stores API key in WordPress options
- ✅ Admin UI for configuration
- ✅ Shortcode or block for embedding chat

**Implementation Approach**:
- Create WordPress plugin with admin settings page
- Store API key in `wp_options` table (encrypted)
- Register REST API endpoint for chat
- Provide shortcode/block for frontend embedding

**Plugin Structure**:
```
salient-chat/
├── salient-chat.php          # Main plugin file
├── admin/
│   ├── settings-page.php     # Admin UI
│   └── api-key-storage.php   # Encrypted storage
├── includes/
│   ├── class-salient-api.php # API client
│   └── rest-endpoints.php    # WordPress REST API
└── public/
    ├── js/chat-widget.js     # Frontend widget
    └── css/chat-widget.css   # Widget styles
```

**Security Level**: 🟢 **Highest** - API key stored in database, never exposed

---

## Static Site Generator Compatibility Matrix

### Top 10 Static Site Generators + Serverless Functions Support

| Static Site Generator | Vercel | Netlify | Cloudflare Pages | AWS Amplify | Render | GitHub Pages | Language | Notes |
|----------------------|--------|---------|------------------|-------------|--------|--------------|----------|-------|
| **Next.js** | ✅ Native | ✅ Full SSR | ✅ Edge Runtime | ✅ Full | ✅ Full | ❌ Static only | TypeScript/JS | Best with Vercel (creators) |
| **Astro** | ✅ Adapters | ✅ Adapters | ✅ Adapters | ✅ Adapters | ✅ Adapters | ⚠️ Static only | TypeScript/JS | Use SSR mode + adapter |
| **Hugo** | ✅ Functions | ✅ Functions | ✅ Workers | ✅ Lambda | ✅ Functions | ❌ No functions | Go | Need separate function files |
| **Jekyll** | ✅ Functions | ✅ Functions | ✅ Workers | ✅ Lambda | ✅ Functions | ❌ No functions | Ruby | Need separate function files |
| **Gatsby** | ✅ Functions | ✅ Functions | ✅ SSR/Workers | ✅ Full | ✅ Functions | ❌ Static only | JavaScript/React | Gatsby v4+ has SSR support |
| **Eleventy** | ✅ Functions | ✅ Functions | ✅ Workers | ✅ Lambda | ✅ Functions | ❌ No functions | JavaScript | Need separate function files |
| **VuePress** | ✅ Functions | ✅ Functions | ✅ Workers | ✅ Lambda | ✅ Functions | ❌ No functions | Vue.js | Need separate function files |
| **Docusaurus** | ✅ Functions | ✅ Functions | ✅ Workers | ✅ Lambda | ✅ Functions | ❌ Static only | React | Need separate function files |
| **Hexo** | ✅ Functions | ✅ Functions | ✅ Workers | ✅ Lambda | ✅ Functions | ❌ No functions | JavaScript | Need separate function files |
| **Pelican** | ✅ Functions | ✅ Functions | ✅ Workers | ✅ Lambda | ✅ Functions | ❌ No functions | Python | Need separate function files |

**Legend**:
- ✅ **Native/Full**: Framework has built-in support or tight integration
- ✅ **Adapters**: Official adapters available for SSR/serverless
- ✅ **Functions/Workers**: Requires separate function directory
- ⚠️ **Static only**: Can deploy static but no serverless support
- ❌ **No functions**: Platform doesn't support serverless functions

---

### Serverless Function Implementation by Host

#### **Vercel Functions**

**Directory**: `api/` or `/app/api/` (Next.js)

```typescript
// api/chat.ts
import type { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  const { message, sessionId } = req.body;
  
  try {
    const response = await fetch(
      `${process.env.SALIENT_API_URL}/accounts/${process.env.SALIENT_ACCOUNT}/agents/${process.env.SALIENT_AGENT}/chat`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Account-API-Key': process.env.SALIENT_API_KEY!,
        },
        body: JSON.stringify({ message, session_id: sessionId }),
      }
    );
    
    const data = await response.json();
    return res.status(200).json(data);
  } catch (error) {
    return res.status(500).json({ error: 'Failed to send message' });
  }
}
```

**Configuration**: Environment variables in Vercel dashboard or `vercel.json`

**Pros**: 
- ✅ Fast cold starts (~50-100ms)
- ✅ Automatic TypeScript support
- ✅ Great Next.js integration

---

#### **Netlify Functions**

**Directory**: `netlify/functions/`

```javascript
// netlify/functions/chat.js
exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: JSON.stringify({ error: 'Method not allowed' }) };
  }
  
  const { message, sessionId } = JSON.parse(event.body);
  
  try {
    const response = await fetch(
      `${process.env.SALIENT_API_URL}/accounts/${process.env.SALIENT_ACCOUNT}/agents/${process.env.SALIENT_AGENT}/chat`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Account-API-Key': process.env.SALIENT_API_KEY,
        },
        body: JSON.stringify({ message, session_id: sessionId }),
      }
    );
    
    const data = await response.json();
    return {
      statusCode: 200,
      body: JSON.stringify(data),
    };
  } catch (error) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Failed to send message' }),
    };
  }
};
```

**Configuration**: `netlify.toml` + environment variables in Netlify UI

```toml
[build]
  functions = "netlify/functions"

[functions]
  node_bundler = "esbuild"
```

**Pros**:
- ✅ Simple AWS Lambda wrapper
- ✅ Good Hugo/Jekyll integration
- ✅ Generous free tier

---

#### **Cloudflare Workers**

**Directory**: `functions/` (Cloudflare Pages) or standalone worker

```typescript
// functions/api/chat.ts
export const onRequestPost: PagesFunction = async (context) => {
  const { message, sessionId } = await context.request.json();
  
  try {
    const response = await fetch(
      `${context.env.SALIENT_API_URL}/accounts/${context.env.SALIENT_ACCOUNT}/agents/${context.env.SALIENT_AGENT}/chat`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Account-API-Key': context.env.SALIENT_API_KEY,
        },
        body: JSON.stringify({ message, session_id: sessionId }),
      }
    );
    
    const data = await response.json();
    return Response.json(data);
  } catch (error) {
    return Response.json({ error: 'Failed to send message' }, { status: 500 });
  }
};
```

**Pros**:
- ✅ Extremely fast (edge runtime, ~0ms cold start)
- ✅ Global distribution
- ✅ Low cost

**Cons**:
- ⚠️ V8 isolate limitations (no Node.js APIs)
- ⚠️ Different programming model

---

#### **AWS Amplify (Lambda)**

**Directory**: `amplify/backend/function/chatapi/`

```javascript
// amplify/backend/function/chatapi/src/index.js
exports.handler = async (event) => {
  const { message, sessionId } = JSON.parse(event.body);
  
  try {
    const response = await fetch(
      `${process.env.SALIENT_API_URL}/accounts/${process.env.SALIENT_ACCOUNT}/agents/${process.env.SALIENT_AGENT}/chat`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Account-API-Key': process.env.SALIENT_API_KEY,
        },
        body: JSON.stringify({ message, session_id: sessionId }),
      }
    );
    
    const data = await response.json();
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    };
  } catch (error) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Failed to send message' }),
    };
  }
};
```

**Configuration**: Amplify CLI + IAM permissions

**Pros**:
- ✅ Full AWS ecosystem integration
- ✅ Mature Lambda platform

**Cons**:
- ⚠️ More complex setup
- ⚠️ Slower cold starts (~200-500ms)

---

## API Key Security Model

### Two-Tier Key System (Recommended)

#### **Secret Keys** (Server-Side Only)
```
Format: sk_{account}_{random}
Example: sk_acme_abc123def456...
Usage: Backend servers, serverless functions, plugins
Permissions: Full API access, unlimited rate limits
Storage: Environment variables, encrypted database
```

**Use for**:
- WordPress plugins
- Next.js/Nuxt/SvelteKit API routes
- Serverless functions
- Any server-side integration

#### **Public Keys** (Client-Side - Future)
```
Format: pk_{account}_{random}
Example: pk_acme_public_xyz789...
Usage: Browser-based applications (with caution)
Permissions: Limited API access, strict rate limits
Restrictions: Domain whitelist, basic features only
```

**Use for**:
- Pure static sites without serverless functions
- Embedded widgets on third-party sites
- Mobile apps (with additional security)

**Rate Limits**:
```yaml
public_key_limits:
  requests_per_minute: 60
  requests_per_day: 1000
  max_message_length: 1000
  features:
    - chat_basic
    - conversation_history
  disabled_features:
    - admin_api
    - bulk_operations
    - agent_configuration
```

---

### Key Storage Best Practices

#### ✅ **DO**:
- Store keys in environment variables
- Use platform secret management (Vercel/Netlify env vars)
- Encrypt keys in WordPress database
- Rotate keys periodically
- Use separate keys for dev/staging/production

#### ❌ **DON'T**:
- Hardcode keys in source code
- Commit keys to version control
- Expose keys in client-side bundles
- Share keys between environments
- Log keys in error messages

---

## Headless CMS Integration Architecture

### Overview

Salient can be part of a larger suite that includes a **headless CMS**, where both the chat API and CMS API are accessed through the same serverless function pattern.

### Architecture: Unified API Gateway

```
┌─────────────────────────────────────────────────────────────────┐
│                    Customer's Frontend                          │
│              (Next.js, Nuxt, Astro, Static Site)               │
└───────────────┬─────────────────────────────────┬───────────────┘
                │                                 │
                ▼                                 ▼
┌───────────────────────────┐    ┌───────────────────────────────┐
│   Serverless Function A   │    │   Serverless Function B       │
│   (Chat API Proxy)        │    │   (CMS API Proxy)             │
│                           │    │                               │
│ - Auth: SALIENT_CHAT_KEY  │    │ - Auth: SALIENT_CMS_KEY       │
│ - Route: /api/chat        │    │ - Route: /api/cms             │
└───────────────┬───────────┘    └───────────────┬───────────────┘
                │                                 │
                ▼                                 ▼
┌───────────────────────────┐    ┌───────────────────────────────┐
│   Salient Chat API        │    │   Salient CMS API             │
│   (Multi-tenant)          │    │   (Multi-tenant)              │
└───────────────────────────┘    └───────────────────────────────┘
```

### Use Cases

#### **1. Content + Conversational AI**
- Blog posts stored in headless CMS
- Chat widget helps users find content
- Vector search indexes CMS content
- Unified customer experience

#### **2. E-commerce + Support Chat**
- Product catalog in CMS
- Chat agent recommends products
- Order management through CMS
- Customer support through chat

#### **3. Documentation + Interactive Help**
- Docs stored in CMS
- Chat agent answers questions
- Real-time doc search
- Feedback collected via chat

---

### Unified Serverless Function Example

**Next.js API Route** (`app/api/salient/[...path]/route.ts`):

```typescript
import { NextRequest, NextResponse } from 'next/server';

// Unified proxy for all Salient services
export async function POST(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const path = params.path.join('/');
  const body = await request.json();
  
  // Determine which Salient service to call
  const serviceConfig = getServiceConfig(path);
  
  try {
    const response = await fetch(
      `${serviceConfig.baseUrl}/${path}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Account-API-Key': serviceConfig.apiKey,
        },
        body: JSON.stringify(body),
      }
    );
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: 'Service request failed' },
      { status: 500 }
    );
  }
}

function getServiceConfig(path: string) {
  if (path.startsWith('chat/')) {
    return {
      baseUrl: process.env.SALIENT_CHAT_URL,
      apiKey: process.env.SALIENT_CHAT_KEY,
    };
  }
  
  if (path.startsWith('cms/')) {
    return {
      baseUrl: process.env.SALIENT_CMS_URL,
      apiKey: process.env.SALIENT_CMS_KEY,
    };
  }
  
  throw new Error('Unknown service path');
}
```

**Client Usage**:
```typescript
// Chat API call
const chatResponse = await fetch('/api/salient/chat/accounts/acme/agents/chat1/chat', {
  method: 'POST',
  body: JSON.stringify({ message: 'Hello' }),
});

// CMS API call
const cmsResponse = await fetch('/api/salient/cms/accounts/acme/content/posts', {
  method: 'POST',
  body: JSON.stringify({ title: 'New Post' }),
});
```

---

### Benefits of Unified Approach

#### **1. Consistent Security Model**
- ✅ Single API key management pattern
- ✅ Unified authentication flow
- ✅ Centralized rate limiting

#### **2. Developer Experience**
- ✅ One integration pattern to learn
- ✅ Consistent error handling
- ✅ Shared TypeScript types

#### **3. Cost Efficiency**
- ✅ Shared serverless function infrastructure
- ✅ Connection pooling benefits
- ✅ Reduced cold starts (warm functions)

#### **4. Monitoring & Observability**
- ✅ Single logging pipeline
- ✅ Unified metrics dashboard
- ✅ Consistent error tracking

---

### Headless CMS Options

If Salient provides a headless CMS, consider these popular architectures:

| CMS Type | Example | Integration Pattern |
|----------|---------|---------------------|
| **API-First** | Strapi, Directus | REST/GraphQL API proxy |
| **Git-Based** | Forestry, Tina CMS | Build-time + runtime API |
| **Database-Driven** | Payload CMS, KeystoneJS | Database + API layer |
| **Hybrid** | Sanity, Contentful | CDN + real-time API |

**Recommended**: API-first with REST/GraphQL for maximum flexibility

---

## Best Practices

### Security

1. **Never Expose Secret Keys**
   - Always use serverless functions or backend
   - Never include keys in client-side bundles
   - Use environment variables for all keys

2. **Validate Origins**
   - Check `Referer` or `Origin` headers
   - Whitelist allowed domains per account
   - Implement CORS properly

3. **Rate Limiting**
   - Implement per-account limits
   - Track by session and IP
   - Add backoff for repeated failures

4. **Input Validation**
   - Validate all request parameters
   - Sanitize user input
   - Limit message lengths

### Performance

1. **Minimize Cold Starts**
   - Keep functions warm with scheduled pings
   - Use edge functions when possible (Cloudflare)
   - Optimize bundle size

2. **Connection Pooling**
   - Reuse HTTP connections
   - Consider connection limits
   - Handle timeouts gracefully

3. **Caching**
   - Cache session data where appropriate
   - Use CDN for static assets
   - Implement response caching for repeated queries

### Monitoring

1. **Logging**
   - Log all API requests
   - Track response times
   - Monitor error rates

2. **Alerting**
   - Alert on high error rates
   - Monitor rate limit hits
   - Track unusual usage patterns

3. **Analytics**
   - Track usage by account
   - Monitor popular features
   - Identify optimization opportunities

---

## Implementation Checklist

### For Framework Developers

- [ ] Choose appropriate pattern (A, B, C, or D)
- [ ] Set up environment variables
- [ ] Create API proxy endpoint/function
- [ ] Test with Salient API credentials
- [ ] Implement error handling
- [ ] Add rate limiting (if needed)
- [ ] Set up monitoring/logging
- [ ] Document for end users

### For Salient (Internal)

- [ ] Generate API key pairs (secret + public)
- [ ] Document API endpoints for each service
- [ ] Provide SDK/client libraries
- [ ] Create example implementations
- [ ] Set up rate limiting per account
- [ ] Implement CORS configuration
- [ ] Create onboarding documentation
- [ ] Build API key management dashboard

---

## Related Documentation

- [Multi-Tenant Security](multi-tenant-security.md) - Security architecture and API authentication
- [API Endpoints](endpoints.md) - Complete API endpoint documentation
- [Configuration Reference](configuration-reference.md) - Configuration options

---

## Frequently Asked Questions

### Can I use direct API calls from the browser?

**For static sites without serverless functions**: Not recommended for secret keys, but public keys (future) could allow this with strict rate limits and domain whitelisting.

### What about mobile apps?

Use the same patterns:
- **Native apps**: Store API key in secure storage, call Salient API directly
- **Hybrid apps**: Use same serverless function approach as web

### Do I need separate keys for chat and CMS?

**Recommended**: Use separate keys for security and tracking purposes. Allows independent rate limiting and revocation.

### What if my hosting platform doesn't support serverless functions?

Options:
1. Use a different host (migrate to Vercel/Netlify)
2. Set up your own backend proxy server
3. Use Salient's hosted widget (iframe approach)

### Can I white-label the integration?

Yes - use your own domain for serverless functions, so requests appear to come from `yourdomain.com/api/chat` rather than exposing Salient endpoints.

---

**Last Updated**: December 31, 2025  
**Maintained By**: Architecture Team

