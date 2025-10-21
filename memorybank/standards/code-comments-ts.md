<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# JavaScript/TypeScript Code Commenting Best Practices

> Guidelines for writing clear, maintainable comments in JavaScript and TypeScript code

## Philosophy

Good comments enhance code readability and maintainability by explaining the reasoning behind implementation decisions, not just describing what the code does. Well-written code should be self-explanatory in terms of its functionality, while comments provide context about intent, constraints, and decisions.

## General Principles

### 🎯 **Focus on "Why", Not "What"**
- Explain the reasoning behind code decisions
- Describe non-obvious implementation choices
- Document business rules and constraints
- Avoid restating what the code obviously does

### 📝 **Keep Comments Concise and Relevant**
- Use clear, direct language
- Be specific and actionable
- Avoid unnecessary jargon
- Make every comment count

### 🔄 **Maintain Currency**
- Update comments when code changes
- Remove obsolete comments immediately
- Treat comments as part of the codebase requiring maintenance
- Outdated comments are worse than no comments

### 🚫 **Avoid Redundancy**
- Don't comment self-explanatory code
- Focus on complex or non-obvious sections
- Let the code speak for itself when it's clear

## JavaScript/TypeScript Commenting Standards

### Single-Line Comments
For brief explanations and clarifications:

```javascript
// Debounce user input to avoid excessive API calls
const debouncedSearch = debounce(handleSearch, 300);

// Convert to display timezone for user's locale
const localTime = utcTime.toLocaleString(userTimezone);
```

**Guidelines:**
- Use `//` followed by a space
- Place on the line above the code being explained
- Keep lines ≤ 80 characters for readability
- Use for quick clarifications and context

### Block Comments
For longer explanations or algorithm descriptions:

```javascript
/*
 * Calculate the optimal layout for responsive grid items.
 * 
 * This algorithm considers:
 * - Available container width
 * - Minimum item width requirements  
 * - Preferred aspect ratios
 * - Screen density for crisp rendering
 * 
 * Returns layout with item dimensions and positions.
 */
function calculateGridLayout(containerWidth, items) {
    // Implementation
}
```

**Guidelines:**
- Use `/* */` for multi-line comments
- Include `*` at the start of each line for readability
- Use for algorithm explanations and complex logic
- Avoid for commenting out code (use version control instead)

### JSDoc Documentation
Standard for function and class documentation:

```typescript
/**
 * Manages user session state and authentication.
 * 
 * Handles token refresh, logout, and session persistence
 * across browser tabs using localStorage and events.
 * 
 * @example
 * ```typescript
 * const session = new SessionManager();
 * await session.login(credentials);
 * ```
 */
class SessionManager {
    /**
     * Authenticate user with email and password.
     * 
     * @param credentials - User login information
     * @param credentials.email - User's email address
     * @param credentials.password - User's password  
     * @param rememberMe - Whether to persist session across browser restarts
     * @returns Promise resolving to user profile data
     * @throws {AuthenticationError} When credentials are invalid
     * @throws {NetworkError} When API is unreachable
     */
    async login(
        credentials: { email: string; password: string },
        rememberMe: boolean = false
    ): Promise<UserProfile> {
        // Implementation
    }
}
```

**JSDoc Tags:**
- `@param` - Parameter descriptions
- `@returns` - Return value description
- `@throws` - Exceptions that may be thrown
- `@example` - Usage examples
- `@deprecated` - Mark deprecated functions
- `@since` - Version when feature was added
- `@see` - References to related functions/docs
- `@override` - Method overrides parent implementation
- `@readonly` - Read-only properties
- `@async` - Async function indicators

### TypeScript-Specific Comments
Leverage type system with strategic comments:

```typescript
interface ApiResponse<T> {
    data: T;
    status: 'success' | 'error';
    // Include message for error cases and optional success metadata
    message?: string;
}

// Type assertion needed here due to third-party library limitations
const config = (window as any).APP_CONFIG as AppConfig;

// Exhaustive switch ensures all enum values are handled
function handleUserRole(role: UserRole): string {
    switch (role) {
        case UserRole.ADMIN:
            return 'Administrator';
        case UserRole.USER:
            return 'Standard User';
        default:
            // TypeScript will error if we miss a case
            const _exhaustive: never = role;
            throw new Error(`Unhandled role: ${role}`);
    }
}
```

### Component Documentation (React/Astro/Vue)
Document component interfaces and usage:

```typescript
/**
 * Chat widget for customer support integration.
 * 
 * Provides floating chat interface that can be embedded
 * on any page via script tag or component import.
 * 
 * @param backendUrl - Base URL for chat API (default: same origin)
 * @param theme - Visual theme configuration
 * @param position - Widget position on screen
 * @param initialMessage - Pre-populate chat with message
 */
interface ChatWidgetProps {
    backendUrl?: string;
    theme?: 'light' | 'dark' | 'auto';
    position?: 'bottom-right' | 'bottom-left';
    initialMessage?: string;
}

export function ChatWidget({ 
    backendUrl = '', 
    theme = 'auto',
    position = 'bottom-right',
    initialMessage 
}: ChatWidgetProps) {
    // Implementation with inline comments for complex logic
}
```

### React Hooks Documentation
Document custom hooks with usage patterns:

```typescript
/**
 * Custom hook for managing chat widget state and API interactions.
 * 
 * Handles message sending, streaming responses, session management,
 * and error recovery with automatic retry logic.
 * 
 * @param config - Widget configuration options
 * @returns Chat state and control functions
 * 
 * @example
 * ```tsx
 * function ChatInterface() {
 *   const { messages, sendMessage, isLoading } = useChatWidget({
 *     backendUrl: '/api/chat'
 *   });
 *   
 *   return (
 *     <div>
 *       {messages.map(msg => <Message key={msg.id} {...msg} />)}
 *       <ChatInput onSend={sendMessage} disabled={isLoading} />
 *     </div>
 *   );
 * }
 * ```
 */
function useChatWidget(config: ChatConfig) {
    // Hook implementation
}
```

### Event Handler Comments
Document complex event handling logic:

```typescript
/**
 * Handle keyboard shortcuts in chat interface.
 * 
 * Supports:
 * - Ctrl/Cmd+Enter: Send message
 * - Escape: Close chat widget
 * - Arrow Up/Down: Navigate message history
 */
function handleKeyboard(event: KeyboardEvent) {
    const isCtrlOrCmd = event.ctrlKey || event.metaKey;
    
    if (isCtrlOrCmd && event.key === 'Enter') {
        // Submit message on Ctrl/Cmd+Enter
        event.preventDefault();
        sendMessage();
        return;
    }
    
    if (event.key === 'Escape') {
        // Close widget on Escape key
        setIsOpen(false);
        return;
    }
    
    // Navigate message history with arrow keys
    if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
        navigateHistory(event.key === 'ArrowUp' ? -1 : 1);
    }
}
```

### Async/Promise Comments
Document asynchronous operations and error handling:

```typescript
/**
 * Stream chat messages from backend with automatic reconnection.
 * 
 * Establishes EventSource connection and handles:
 * - Message chunking and accumulation
 * - Connection failures with exponential backoff
 * - Graceful degradation to polling fallback
 */
async function startMessageStream(sessionId: string): Promise<void> {
    try {
        // Attempt SSE connection with timeout
        const eventSource = new EventSource(`/events/stream?session=${sessionId}`);
        
        eventSource.onmessage = (event) => {
            // Accumulate message chunks for complete response
            const chunk = JSON.parse(event.data);
            appendMessageChunk(chunk);
        };
        
        eventSource.onerror = () => {
            // Retry connection with exponential backoff
            scheduleReconnect();
        };
        
    } catch (error) {
        // Fall back to polling if SSE unavailable
        logger.warn('SSE unavailable, falling back to polling');
        startPollingFallback(sessionId);
    }
}
```

### Security-Focused Comments
Document security considerations:

```typescript
/**
 * Initialize chat widget with security considerations.
 * 
 * Same-origin policy enforced by default to prevent CSRF.
 * Cross-origin requests require explicit configuration.
 */
function initializeWidget(config: WidgetConfig): void {
    // Validate backend URL to prevent injection attacks
    const backendUrl = sanitizeUrl(config.backendUrl || window.location.origin);
    
    // Use fetch with credentials for session cookie support
    const fetchOptions: RequestInit = {
        credentials: 'same-origin',  // Include session cookies
        headers: {
            'Content-Type': 'application/json',
            // CSRF protection via custom header
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
}
```

## Comment Anti-Patterns

### ❌ **Don't Do This**
```typescript
// Bad: Obvious and redundant
let count = 0; // Initialize count to zero

// Bad: Outdated information
// TODO: Add TypeScript types (already done)

// Bad: Explaining what instead of why
// Get user input
const input = document.getElementById('user-input');
// Check if input exists
if (input) {
    // Get the value
    const value = input.value;
}
```

### ✅ **Do This Instead**
```typescript
// Good: Explains business context
let retryCount = 0; // Track API retry attempts for exponential backoff

// Good: Current and actionable
// TODO: Add input validation for XSS prevention (Issue #789)

// Good: Explains why and provides context
// Ensure input exists before processing to prevent null reference errors
// in dynamically generated forms where elements may not be rendered yet
const input = document.getElementById('user-input');
if (input) {
    const value = sanitizeInput(input.value); // Prevent XSS attacks
}
```

## Framework-Specific Guidelines

### React/Next.js Comments
```tsx
/**
 * Server component for chat interface with streaming support.
 * 
 * This component runs on the server and streams chat responses
 * to avoid client-side API key exposure and improve performance.
 */
export default async function ChatPage({ params }: { params: { id: string } }) {
    // Pre-fetch session data on server for better UX
    const session = await getSession(params.id);
    
    return (
        <Suspense fallback={<ChatSkeleton />}>
            <StreamingChat sessionId={params.id} initialData={session} />
        </Suspense>
    );
}
```

### Astro Components
Document Astro-specific patterns including frontmatter, props, and hydration:

```astro
---
/**
 * Astro layout component with conditional widget loading.
 * 
 * Features:
 * - Server-side rendering for SEO benefits
 * - Conditional client-side hydration based on environment
 * - Semantic HTML structure with accessibility considerations
 * - Integration with Preact components via client:load directive
 * 
 * @param title - Page title for SEO
 * @param description - Meta description for search engines
 */

export interface Props {
    title: string;
    description?: string;
}

const { title, description } = Astro.props;

// Environment-based widget loading for security
const enableWidget = import.meta.env.PUBLIC_ENABLE_WIDGET === 'true';
const isDevelopment = import.meta.env.DEV;
---

<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width" />
    <title>{title}</title>
    {description && <meta name="description" content={description} />}
  </head>
  <body>
    <!-- Skip link for accessibility -->
    <a href="#main" class="skip-link">Skip to content</a>
    
    <header role="banner">
      <nav><!-- Navigation --></nav>
    </header>
    
    <main id="main" role="main">
      <slot />
    </main>
    
    <!-- Conditional widget loading with security considerations -->
    {enableWidget && (
      <script 
        src="/widget/chat-widget.js" 
        is:inline 
        data-chat-path="/chat"
        data-backend={isDevelopment ? 'http://localhost:8000' : ''}
      ></script>
    )}
  </body>
</html>

<style>
  /* Accessibility: Hidden skip link that appears on focus */
  .skip-link {
    position: absolute;
    left: -9999px;
    top: auto;
    width: 1px;
    height: 1px;
    overflow: hidden;
  }
  
  .skip-link:focus {
    left: 1rem;
    top: 1rem;
    width: auto;
    height: auto;
    background: #fff;
    padding: 0.5rem 0.75rem;
    border: 1px solid #ccc;
    border-radius: 0.375rem;
    z-index: 9999;
  }
</style>
```

**Astro-Specific Commenting Guidelines:**
- **Frontmatter comments**: Use JSDoc in the `---` section for component documentation
- **Props interface**: Always document component props with descriptions
- **Environment variables**: Comment security implications of public env vars
- **Hydration directives**: Explain why `client:load`, `client:visible`, etc. are chosen
- **Slot usage**: Document expected content and structure for slots
- **CSS scope**: Comment on scoped vs global styles

### Preact Components (Astro Integration)
Document Preact components for Astro with proper TypeScript integration:

```typescript
/**
 * Preact chat widget component with streaming support.
 * 
 * Designed for Astro integration with client-side hydration.
 * Handles real-time chat streaming, message history, and error recovery.
 * 
 * Features:
 * - SSE streaming with fallback to polling
 * - Markdown rendering with XSS protection
 * - Keyboard shortcuts (Ctrl+Enter to send)
 * - Copy-to-clipboard functionality
 * - Responsive design with accessibility
 * 
 * @param backendUrl - Chat API base URL (defaults to same origin)
 * @param theme - Visual theme ('light' | 'dark' | 'auto')
 * @param initialMessage - Pre-populate input with message
 */

import { useState, useEffect, useRef } from 'preact/hooks';
import type { ComponentChildren } from 'preact';

interface ChatMessage {
  id: string;
  content: string;
  role: 'human' | 'assistant' | 'system';
  timestamp: string;
  metadata?: Record<string, any>;
}

interface ChatWidgetProps {
  backendUrl?: string;
  theme?: 'light' | 'dark' | 'auto';
  initialMessage?: string;
  maxMessages?: number;
}

export function PreactChatWidget({
  backendUrl = '',
  theme = 'auto',
  initialMessage = '',
  maxMessages = 100
}: ChatWidgetProps) {
  // State management with proper typing
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState(initialMessage);
  const [isStreaming, setIsStreaming] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'error'>('disconnected');
  
  // Refs for DOM manipulation and cleanup
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  /**
   * Send message with optimistic updates and error handling.
   * 
   * Implements streaming pattern:
   * 1. Add user message immediately for responsive UX
   * 2. Start SSE stream for assistant response
   * 3. Accumulate response chunks with live updates
   * 4. Handle connection errors with graceful fallback
   */
  const sendMessage = async (content: string) => {
    if (!content.trim() || isStreaming) return;

    // Optimistic user message update
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      content: content.trim(),
      role: 'human',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev.slice(-maxMessages + 1), userMessage]);
    setInputValue('');
    setIsStreaming(true);

    try {
      // Stream assistant response with abort signal for cleanup
      await streamAssistantResponse(content, abortControllerRef.current?.signal);
    } catch (error) {
      // Error handling with user feedback
      console.error('Chat error:', error);
      addErrorMessage('Sorry, there was a problem sending your message. Please try again.');
    } finally {
      setIsStreaming(false);
    }
  };

  // Keyboard shortcut handler with accessibility considerations
  const handleKeyDown = (event: KeyboardEvent) => {
    const isCtrlOrCmd = event.ctrlKey || event.metaKey;
    
    if (isCtrlOrCmd && event.key === 'Enter') {
      // Submit on Ctrl/Cmd+Enter (common UX pattern)
      event.preventDefault();
      sendMessage(inputValue);
    } else if (event.key === 'Escape') {
      // Clear input on Escape (another common pattern)
      setInputValue('');
    }
  };

  // Auto-scroll to latest message for better UX
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Cleanup streams on unmount to prevent memory leaks
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  return (
    <div className={`chat-widget theme-${theme}`} role="application" aria-label="Chat interface">
      {/* Message history with semantic markup */}
      <div className="messages" role="log" aria-live="polite" aria-label="Chat messages">
        {messages.map((message) => (
          <ChatMessageComponent 
            key={message.id} 
            message={message}
            onCopy={() => copyToClipboard(message.content)}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area with accessibility and keyboard support */}
      <div className="input-area">
        <textarea
          value={inputValue}
          onChange={(e) => setInputValue((e.target as HTMLTextAreaElement).value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          disabled={isStreaming}
          rows={2}
          aria-label="Type your message"
          aria-describedby="send-instructions"
        />
        
        <div id="send-instructions" className="sr-only">
          Press Ctrl+Enter to send message, Escape to clear
        </div>

        <button
          onClick={() => sendMessage(inputValue)}
          disabled={!inputValue.trim() || isStreaming}
          aria-label={isStreaming ? 'Sending message...' : 'Send message'}
        >
          {isStreaming ? 'Sending...' : 'Send'}
        </button>
      </div>

      {/* Connection status indicator for debugging */}
      <div className="status-indicator" aria-live="polite">
        <span className={`status-dot ${connectionStatus}`} />
        <span className="sr-only">Connection status: {connectionStatus}</span>
      </div>
    </div>
  );
}
```

**Preact-Specific Guidelines:**
- **Hook documentation**: Document useState/useEffect patterns and cleanup
- **Props interface**: Always provide complete TypeScript interfaces
- **Accessibility**: Include ARIA attributes and semantic HTML
- **Performance**: Comment on optimization patterns (useCallback, useMemo)
- **Error boundaries**: Document error handling and fallback states
- **Astro integration**: Comment on hydration directives and SSR considerations

### Vanilla JavaScript (Widget/Utilities)
Document standalone JavaScript for widgets and utilities:

```javascript
/**
 * Standalone chat widget with Shadow DOM isolation.
 * 
 * Self-contained widget that can be embedded on any website without
 * framework dependencies. Uses Shadow DOM for style isolation and
 * provides fallback patterns for older browsers.
 * 
 * Security Considerations:
 * - Same-origin policy enforced by default
 * - Cross-origin requests require explicit data-allow-cross="1"
 * - Input sanitization via DOMPurify for markdown rendering
 * - CSP-friendly: no inline event handlers or eval()
 * 
 * Browser Support:
 * - Modern browsers: Full Shadow DOM support
 * - Legacy browsers: Graceful degradation without Shadow DOM
 * - Mobile: Touch-friendly interface with proper viewport handling
 */
(function() {
  'use strict';
  
  // Prevent multiple widget instances
  if (typeof window === 'undefined' || window.__salientWidgetLoaded) return;
  window.__salientWidgetLoaded = true;

  /**
   * Extract configuration from script tag data attributes.
   * 
   * Supports:
   * - data-backend: Custom backend URL (security: same-origin preferred)
   * - data-chat-path: Chat endpoint path (default: /chat)
   * - data-allow-cross: Enable cross-origin requests (security risk)
   * - data-sse: Enable/disable SSE streaming (default: enabled)
   * - data-copy-icon: Custom copy icon URL
   */
  const script = getCurrentScript();
  const config = {
    backend: getDataAttribute(script, 'data-backend', window.location.origin),
    chatPath: getDataAttribute(script, 'data-chat-path', '/chat'),
    allowCross: getDataAttribute(script, 'data-allow-cross') === '1',
    sseEnabled: getDataAttribute(script, 'data-sse', '1') !== '0',
    copyIcon: getDataAttribute(script, 'data-copy-icon', '/widget/chat-copy.svg')
  };

  /**
   * Safely get current script element with fallback.
   * 
   * Handles edge cases:
   * - document.currentScript not supported (IE)
   * - Script loaded asynchronously
   * - Multiple scripts with same name
   */
  function getCurrentScript() {
    if (document.currentScript) {
      return document.currentScript;
    }
    
    // Fallback: find script by filename
    const scripts = document.querySelectorAll('script');
    for (let i = scripts.length - 1; i >= 0; i--) {
      const src = scripts[i].src || '';
      if (src.includes('chat-widget.js')) {
        return scripts[i];
      }
    }
    return null;
  }

  /**
   * Create Shadow DOM widget with style isolation.
   * 
   * Benefits:
   * - Complete CSS isolation from host page
   * - Prevents host styles from breaking widget
   * - Prevents widget styles from affecting host
   * - Better encapsulation and maintainability
   */
  function createShadowWidget() {
    const container = document.createElement('div');
    container.id = 'salient-chat-widget';
    
    // Create Shadow DOM with style isolation
    const shadow = container.attachShadow({ mode: 'closed' });
    
    // Inject widget styles (scoped to shadow root)
    const styles = createWidgetStyles();
    shadow.appendChild(styles);
    
    // Create widget DOM structure
    const widgetHTML = createWidgetDOM();
    shadow.appendChild(widgetHTML);
    
    // Position widget and add to page
    Object.assign(container.style, {
      position: 'fixed',
      bottom: '20px',
      right: '20px',
      zIndex: '2147483647', // Maximum z-index for top layer
      pointerEvents: 'none'   // Allow clicks through container
    });
    
    document.body.appendChild(container);
    
    // Initialize event handlers within shadow context
    initializeWidgetEvents(shadow);
    
    return { container, shadow };
  }

  // Initialize widget when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createShadowWidget);
  } else {
    createShadowWidget();
  }
})();
```

**Vanilla JavaScript Guidelines:**
- **IIFE pattern**: Wrap in immediately invoked function for scope isolation
- **Feature detection**: Check for browser support before using features
- **Progressive enhancement**: Provide fallbacks for older browsers
- **Security comments**: Document same-origin policy and XSS prevention
- **Error handling**: Graceful degradation when APIs are unavailable
- **Performance**: Comment on DOM manipulation and event delegation patterns

### Vue.js Components
```vue
<script setup lang="ts">
/**
 * Vue composition API chat component with reactive state.
 * 
 * Uses composables for state management and provides
 * reactive chat interface with TypeScript support.
 */

interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
}

// Reactive chat state with proper typing
const messages = ref<ChatMessage[]>([]);
const isLoading = ref(false);

// Send message with optimistic updates
const sendMessage = async (content: string) => {
  // Add user message immediately for better UX
  const userMessage: ChatMessage = {
    id: crypto.randomUUID(),
    content,
    role: 'user'
  };
  messages.value.push(userMessage);
  
  // Stream response from backend
  await streamResponse(content);
};
</script>
```

## Tools and Automation

### JavaScript/TypeScript Tools
- **Linting**: ESLint rules for comment quality and JSDoc validation
- **Documentation**: TypeDoc for automatic API documentation
- **Type Checking**: TypeScript reduces need for type-related comments
- **JSDoc validation**: eslint-plugin-jsdoc for consistent documentation

### IDE Integration
- **VS Code**: Better Comments, TSDoc, Auto Comment Blocks extensions
- **WebStorm**: Built-in JSDoc generation and validation
- **Vim/Neovim**: coc-tsserver for TypeScript integration

### Build Tools Integration
```javascript
// webpack.config.js
module.exports = {
  plugins: [
    new TypedocWebpackPlugin({
      // Generate docs from JSDoc comments
      out: './docs',
      exclude: ['**/*.test.ts', '**/*.spec.ts']
    })
  ]
};
```

### ESLint Configuration
```json
{
  "extends": ["@typescript-eslint/recommended"],
  "plugins": ["jsdoc"],
  "rules": {
    "jsdoc/check-alignment": "error",
    "jsdoc/check-param-names": "error",
    "jsdoc/check-return-type": "error",
    "jsdoc/require-description": "warn",
    "jsdoc/require-param": "error",
    "jsdoc/require-param-description": "warn",
    "jsdoc/require-returns": "error"
  }
}
```

## Project Integration

### Pre-commit Hooks
```yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.0.0
    hooks:
      - id: eslint
        files: \.(js|ts|jsx|tsx)$
        args: [--fix]
  - repo: local
    hooks:
      - id: tsdoc
        name: Generate TypeScript docs
        entry: npm run docs:generate
        language: node
        files: \.(ts|tsx)$
```

### Documentation Generation
```json
{
  "scripts": {
    "docs:generate": "typedoc --out docs src/",
    "docs:serve": "serve docs/",
    "docs:check": "typedoc --validation"
  }
}
```

## References

- [JSDoc Documentation](https://jsdoc.app/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [TSDoc Standard](https://tsdoc.org/)
- [ESLint JSDoc Plugin](https://github.com/gajus/eslint-plugin-jsdoc)
- [TypeDoc Documentation](https://typedoc.org/)
- [Clean Code by Robert Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
