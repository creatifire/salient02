# JavaScript Coding Standards

> Essential coding standards for maintainable, consistent JavaScript code

## Code Style & Formatting

### Basic Formatting
```javascript
// Use 2 spaces for indentation (standard in JS ecosystem)
function calculateTotal(items) {
  let total = 0;
  for (const item of items) {
    total += item.price;
  }
  return total;
}

// Line length: 80-100 characters (configurable)
const result = someVeryLongFunctionName(
  parameter1,
  parameter2, 
  parameter3
);

// Use trailing commas for multi-line structures
const config = {
  apiUrl: 'https://api.example.com',
  timeout: 5000,
  retries: 3, // <- trailing comma
};
```

### Semicolons & Quotes
```javascript
// Always use semicolons (or configure Prettier to add them)
const message = 'Hello, world!';
doSomething();

// Use single quotes for strings (configurable)
const singleQuote = 'preferred';
const template = `Use backticks for ${interpolation}`;

// Use double quotes only when necessary
const quotesInString = "Don't use double quotes unnecessarily";
```

## Naming Conventions

### Variables & Functions
```javascript
// Use camelCase for variables and functions
const userName = 'john_doe';
const totalCount = 42;
const isAuthenticated = true;

function calculateTaxAmount(income) {
  return income * 0.2;
}

function sendEmailNotification(recipient) {
  // Function implementation
}

// Use descriptive names
// Good
const userAccountBalance = 1500;
const isEmailValid = validateEmail(email);

// Avoid abbreviations
// Bad: usr, calc, btn, str
// Good: user, calculate, button, string
```

### Constants
```javascript
// Use UPPER_SNAKE_CASE for constants
const DEFAULT_TIMEOUT = 30000;
const MAX_RETRY_ATTEMPTS = 3;
const API_BASE_URL = 'https://api.example.com';

// Group related constants in objects
const ApiConfig = {
  BASE_URL: 'https://api.example.com',
  TIMEOUT: 5000,
  RETRY_ATTEMPTS: 3
};

// Or use Object.freeze for immutability
const HTTP_STATUS = Object.freeze({
  OK: 200,
  NOT_FOUND: 404,
  INTERNAL_ERROR: 500
});
```

### Classes & Constructors
```javascript
// Use PascalCase for classes and constructors
class UserManager {
  constructor(apiClient) {
    this.apiClient = apiClient;
    this._cache = new Map(); // Private members with underscore
  }
  
  async getUser(id) {
    if (this._cache.has(id)) {
      return this._cache.get(id);
    }
    
    const user = await this.apiClient.fetchUser(id);
    this._cache.set(id, user);
    return user;
  }
}

class DatabaseConnection {
  constructor(connectionString) {
    this.connectionString = connectionString;
    this.isConnected = false;
  }
}

// Factory functions use camelCase
function createUserManager(config) {
  return new UserManager(config.apiClient);
}
```

## Modern JavaScript Features

### ES6+ Syntax
```javascript
// Use const/let instead of var
const immutableValue = 'never changes';
let mutableValue = 'can change';

// Arrow functions for callbacks and short functions
const numbers = [1, 2, 3, 4, 5];
const doubled = numbers.map(n => n * 2);
const filtered = numbers.filter(n => n > 2);

// Use arrow functions for methods when 'this' is not needed
const utils = {
  apiUrl: 'https://api.example.com',
  
  // Regular function when 'this' is needed
  getFullUrl(path) {
    return `${this.apiUrl}${path}`;
  },
  
  // Arrow function for pure utilities
  formatDate: (date) => date.toISOString().split('T')[0]
};

// Destructuring for cleaner code
const { name, email, age } = user;
const [first, second, ...rest] = items;

// Template literals for string interpolation
const message = `Hello ${name}, you have ${count} new messages`;

// Default parameters
function greetUser(name = 'Guest', greeting = 'Hello') {
  return `${greeting}, ${name}!`;
}
```

### Async/Await
```javascript
// Prefer async/await over Promises for readability
async function fetchUserData(userId) {
  try {
    const response = await fetch(`/api/users/${userId}`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const userData = await response.json();
    return userData;
  } catch (error) {
    console.error('Failed to fetch user data:', error);
    throw error; // Re-throw for caller to handle
  }
}

// Parallel async operations
async function loadDashboardData(userId) {
  try {
    const [user, posts, notifications] = await Promise.all([
      fetchUser(userId),
      fetchUserPosts(userId),
      fetchNotifications(userId)
    ]);
    
    return {
      user,
      posts,
      notifications
    };
  } catch (error) {
    console.error('Failed to load dashboard:', error);
    throw error;
  }
}
```

## File Organization & Module Structure

### When to Split Files

**Split into separate files when:**
- **File exceeds 300-500 lines** (excluding tests)
- **Multiple unrelated classes/functions** in one file
- **Different concerns** can be clearly separated
- **Reusability** across multiple modules

### Module Patterns
```javascript
// ES6 Modules (preferred)
// userService.js
export class UserService {
  constructor(apiClient) {
    this.apiClient = apiClient;
  }
  
  async getUser(id) {
    // Implementation
  }
}

export const DEFAULT_CONFIG = {
  timeout: 5000,
  retries: 3
};

// Default export for main class/function
export default UserService;

// Importing
import UserService, { DEFAULT_CONFIG } from './userService.js';
import { UserService } from './userService.js'; // Named import only
```

### Directory Structure
```javascript
// Small project structure
src/
├── index.js
├── config.js
├── utils/
│   ├── validation.js
│   ├── formatting.js
│   └── api.js
├── services/
│   ├── userService.js
│   ├── authService.js
│   └── emailService.js
└── components/
    ├── ChatWidget.js
    └── MessageList.js

// Medium project with barrel exports
src/
├── index.js
├── config/
│   ├── index.js          // Barrel export
│   ├── database.js
│   └── api.js
├── services/
│   ├── index.js          // Barrel export
│   ├── UserService.js
│   └── AuthService.js
└── utils/
    ├── index.js          // Barrel export
    ├── validation.js
    └── formatting.js

// Barrel export example (services/index.js)
export { UserService } from './UserService.js';
export { AuthService } from './AuthService.js';
export { default as EmailService } from './EmailService.js';
```

### Import Organization
```javascript
// External/third-party imports first
import express from 'express';
import { EventSource } from 'eventsource';
import marked from 'marked';
import DOMPurify from 'dompurify';

// Internal imports (relative paths)
import { config } from './config.js';
import { UserService } from './services/UserService.js';
import { validateInput } from './utils/validation.js';

// Group imports logically
import {
  createUser,
  updateUser,
  deleteUser
} from './services/userService.js';
```

## Error Handling

### Error Patterns
```javascript
// Custom error classes
class ValidationError extends Error {
  constructor(message, field) {
    super(message);
    this.name = 'ValidationError';
    this.field = field;
  }
}

class ApiError extends Error {
  constructor(message, status, response) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.response = response;
  }
}

// Error handling with specific catches
async function processUserRequest(userData) {
  try {
    // Validate input
    if (!userData.email) {
      throw new ValidationError('Email is required', 'email');
    }
    
    // Process data
    const user = await createUser(userData);
    return user;
    
  } catch (error) {
    if (error instanceof ValidationError) {
      // Handle validation errors
      console.warn(`Validation failed: ${error.message}`);
      throw error; // Re-throw for UI to handle
    }
    
    if (error instanceof ApiError) {
      // Handle API errors
      console.error(`API error: ${error.status} - ${error.message}`);
      throw new Error('Unable to process request');
    }
    
    // Handle unexpected errors
    console.error('Unexpected error:', error);
    throw new Error('Internal error occurred');
  }
}

// Promise error handling
function fetchWithRetry(url, maxRetries = 3) {
  return fetch(url)
    .then(response => {
      if (!response.ok) {
        throw new ApiError(`HTTP ${response.status}`, response.status, response);
      }
      return response.json();
    })
    .catch(error => {
      if (maxRetries > 0 && error instanceof ApiError && error.status >= 500) {
        console.log(`Retrying... (${maxRetries} attempts left)`);
        return fetchWithRetry(url, maxRetries - 1);
      }
      throw error;
    });
}
```

## DOM Manipulation Best Practices

### Modern DOM APIs
```javascript
// Use modern query methods
const button = document.querySelector('#submit-button');
const items = document.querySelectorAll('.list-item');

// Event delegation for dynamic content
document.addEventListener('click', (event) => {
  if (event.target.matches('.delete-button')) {
    handleDelete(event.target.dataset.id);
  }
});

// Use classList for class manipulation
element.classList.add('active');
element.classList.remove('hidden');
element.classList.toggle('expanded');

// Use dataset for data attributes
// HTML: <div data-user-id="123" data-role="admin">
const userId = element.dataset.userId;
const role = element.dataset.role;
```

### Widget/Component Patterns
```javascript
// Self-contained widget pattern (for embedding)
(function() {
  'use strict';
  
  // Prevent multiple initialization
  if (window.__ChatWidgetLoaded) return;
  window.__ChatWidgetLoaded = true;
  
  class ChatWidget {
    constructor(container, options = {}) {
      this.container = container;
      this.options = {
        apiUrl: '',
        theme: 'light',
        ...options
      };
      
      this.init();
    }
    
    init() {
      this.render();
      this.attachEventListeners();
    }
    
    render() {
      this.container.innerHTML = `
        <div class="chat-widget theme-${this.options.theme}">
          <div class="chat-messages" id="messages"></div>
          <div class="chat-input">
            <textarea placeholder="Type your message..."></textarea>
            <button>Send</button>
          </div>
        </div>
      `;
    }
    
    attachEventListeners() {
      const textarea = this.container.querySelector('textarea');
      const button = this.container.querySelector('button');
      
      button.addEventListener('click', () => this.sendMessage());
      
      textarea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
          e.preventDefault();
          this.sendMessage();
        }
      });
    }
    
    async sendMessage() {
      const textarea = this.container.querySelector('textarea');
      const message = textarea.value.trim();
      
      if (!message) return;
      
      try {
        this.addMessage('user', message);
        textarea.value = '';
        
        await this.streamResponse(message);
      } catch (error) {
        console.error('Failed to send message:', error);
        this.addMessage('error', 'Failed to send message. Please try again.');
      }
    }
    
    addMessage(type, content) {
      const messagesContainer = this.container.querySelector('#messages');
      const messageElement = document.createElement('div');
      messageElement.className = `message message-${type}`;
      messageElement.textContent = content;
      messagesContainer.appendChild(messageElement);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    async streamResponse(message) {
      // SSE implementation
      const eventSource = new EventSource(`${this.options.apiUrl}/stream?message=${encodeURIComponent(message)}`);
      
      eventSource.onmessage = (event) => {
        // Handle streaming response
      };
      
      eventSource.onerror = () => {
        eventSource.close();
        this.addMessage('error', 'Connection lost. Please try again.');
      };
    }
  }
  
  // Auto-initialize widgets
  function initializeWidgets() {
    const containers = document.querySelectorAll('[data-chat-widget]');
    containers.forEach(container => {
      if (!container.__chatWidget) {
        const options = {
          apiUrl: container.dataset.apiUrl,
          theme: container.dataset.theme || 'light'
        };
        container.__chatWidget = new ChatWidget(container, options);
      }
    });
  }
  
  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeWidgets);
  } else {
    initializeWidgets();
  }
})();
```

## Performance Best Practices

### Efficient Code Patterns
```javascript
// Use efficient array methods
const activeUsers = users.filter(user => user.isActive);
const userNames = users.map(user => user.name);
const totalAmount = items.reduce((sum, item) => sum + item.price, 0);

// Avoid unnecessary iterations
// Bad: Multiple iterations
const activeUsers = users.filter(user => user.isActive);
const activeUserNames = activeUsers.map(user => user.name);
const activeUserCount = activeUsers.length;

// Good: Single iteration
const activeUserData = users.reduce((acc, user) => {
  if (user.isActive) {
    acc.names.push(user.name);
    acc.count++;
  }
  return acc;
}, { names: [], count: 0 });

// Debounce expensive operations
function debounce(func, delay) {
  let timeoutId;
  return function(...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
}

const debouncedSearch = debounce(performSearch, 300);

// Use requestAnimationFrame for animations
function animateElement(element, targetPosition) {
  let currentPosition = element.offsetLeft;
  
  function animate() {
    if (Math.abs(currentPosition - targetPosition) > 1) {
      currentPosition += (targetPosition - currentPosition) * 0.1;
      element.style.left = `${currentPosition}px`;
      requestAnimationFrame(animate);
    }
  }
  
  requestAnimationFrame(animate);
}
```

## Testing Standards

### Test Structure
```javascript
// tests/userService.test.js
import { jest } from '@jest/globals';
import { UserService } from '../src/services/UserService.js';

describe('UserService', () => {
  let userService;
  let mockApiClient;
  
  beforeEach(() => {
    mockApiClient = {
      fetchUser: jest.fn(),
      createUser: jest.fn()
    };
    userService = new UserService(mockApiClient);
  });
  
  describe('getUser', () => {
    it('should return user data when user exists', async () => {
      // Arrange
      const userId = 123;
      const userData = { id: 123, name: 'John Doe' };
      mockApiClient.fetchUser.mockResolvedValue(userData);
      
      // Act
      const result = await userService.getUser(userId);
      
      // Assert
      expect(result).toEqual(userData);
      expect(mockApiClient.fetchUser).toHaveBeenCalledWith(userId);
    });
    
    it('should throw error when user not found', async () => {
      // Arrange
      const userId = 999;
      mockApiClient.fetchUser.mockRejectedValue(new Error('User not found'));
      
      // Act & Assert
      await expect(userService.getUser(userId)).rejects.toThrow('User not found');
    });
  });
  
  describe('createUser', () => {
    it('should validate required fields', async () => {
      // Arrange
      const invalidUserData = { name: 'John' }; // Missing email
      
      // Act & Assert
      await expect(userService.createUser(invalidUserData))
        .rejects.toThrow('Email is required');
    });
  });
});
```

## Code Quality Tools

### Required Tools Configuration
```json
// package.json
{
  "devDependencies": {
    "eslint": "^8.0.0",
    "prettier": "^3.0.0",
    "@eslint/js": "^9.0.0",
    "eslint-config-prettier": "^9.0.0",
    "eslint-plugin-import": "^2.29.0",
    "jest": "^29.0.0",
    "husky": "^8.0.0",
    "lint-staged": "^15.0.0"
  },
  "scripts": {
    "lint": "eslint src/",
    "lint:fix": "eslint src/ --fix",
    "format": "prettier --write src/",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage"
  }
}

// .eslintrc.js
module.exports = {
  env: {
    browser: true,
    es2022: true,
    node: true
  },
  extends: [
    'eslint:recommended',
    'prettier' // Must be last
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module'
  },
  rules: {
    'no-console': 'warn',
    'no-unused-vars': 'error',
    'prefer-const': 'error',
    'no-var': 'error',
    'prefer-arrow-callback': 'error',
    'prefer-template': 'error'
  }
};

// .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false
}
```

## Project-Specific Standards

### For Salient Chat Widget
```javascript
// Widget configuration patterns
const WidgetConfig = {
  DEFAULT_BACKEND_URL: window.location.origin,
  DEFAULT_THEME: 'auto',
  SSE_ENABLED: true,
  COPY_ICON_URL: '/widget/chat-copy.svg'
};

// Security patterns for embedded widgets
function sanitizeUrl(url) {
  try {
    const parsed = new URL(url, window.location.origin);
    return parsed.toString();
  } catch {
    return window.location.origin;
  }
}

// Error boundaries for widget isolation
function createSafeWidget(container, options) {
  try {
    return new ChatWidget(container, options);
  } catch (error) {
    console.error('Widget initialization failed:', error);
    container.innerHTML = '<div class="widget-error">Chat temporarily unavailable</div>';
    return null;
  }
}
```

## References

- [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- [MDN JavaScript Guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide)
- [ESLint Rules Reference](https://eslint.org/docs/rules/)
- [Prettier Configuration](https://prettier.io/docs/en/configuration.html)
- [Jest Testing Framework](https://jestjs.io/docs/getting-started)
