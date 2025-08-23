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
```astro
---
/**
 * Astro component for embedding chat widget in static sites.
 * 
 * Hydrates on client-side for interactivity while maintaining
 * SEO benefits of server-side rendering.
 */

interface Props {
    backendUrl?: string;
    theme?: 'light' | 'dark';
}

const { backendUrl = '/api/chat', theme = 'light' } = Astro.props;
---

<div class="chat-widget" data-theme={theme}>
    <!-- Widget rendered server-side for SEO -->
    <ChatInterface client:load backend={backendUrl} />
</div>
```

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
