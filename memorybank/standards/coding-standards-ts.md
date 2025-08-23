# TypeScript Coding Standards

> Essential coding standards for type-safe, maintainable TypeScript code

## TypeScript-Specific Standards

### Type Annotations
```typescript
// Always provide explicit types for function parameters and return values
function calculateTax(income: number, rate: number): number {
  return income * rate;
}

// Use type annotations for variables when type inference isn't clear
const apiUrl: string = process.env.API_URL || 'http://localhost:3000';
const userIds: number[] = [1, 2, 3, 4, 5];

// Let TypeScript infer simple types
const message = 'Hello, world!'; // string (inferred)
const count = 42; // number (inferred)
const isActive = true; // boolean (inferred)

// Use proper typing for object parameters
interface CreateUserParams {
  name: string;
  email: string;
  age?: number; // Optional property
  metadata?: Record<string, unknown>; // Flexible object
}

function createUser(params: CreateUserParams): Promise<User> {
  // Implementation
}
```

### Interface Design
```typescript
// Use interfaces for object shapes and contracts
interface User {
  readonly id: number; // Immutable property
  name: string;
  email: string;
  createdAt: Date;
  updatedAt?: Date; // Optional for new users
}

// Extend interfaces for specialized types
interface AdminUser extends User {
  permissions: string[];
  lastLoginAt: Date;
}

// Use generic interfaces for reusable patterns
interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  errors?: string[];
}

// Example usage
const userResponse: ApiResponse<User> = await fetchUser(123);
const usersResponse: ApiResponse<User[]> = await fetchUsers();

// Use mapped types for transformations
type PartialUser = Partial<User>; // All properties optional
type UserEmail = Pick<User, 'email'>; // Only email property
type UserWithoutId = Omit<User, 'id'>; // All except id
```

### Union Types & Discriminated Unions
```typescript
// Use union types for limited value sets
type Theme = 'light' | 'dark' | 'auto';
type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';

// Discriminated unions for complex state management
interface LoadingState {
  status: 'loading';
}

interface SuccessState {
  status: 'success';
  data: User[];
}

interface ErrorState {
  status: 'error';
  error: string;
}

type AsyncState = LoadingState | SuccessState | ErrorState;

// Type guards for discriminated unions
function handleAsyncState(state: AsyncState): void {
  switch (state.status) {
    case 'loading':
      showSpinner();
      break;
    case 'success':
      displayData(state.data); // TypeScript knows data exists
      break;
    case 'error':
      showError(state.error); // TypeScript knows error exists
      break;
    default:
      // Exhaustiveness check
      const _exhaustive: never = state;
      throw new Error(`Unhandled state: ${state}`);
  }
}
```

### Generic Types & Constraints
```typescript
// Generic functions with constraints
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

// Usage with type safety
const user: User = { id: 1, name: 'John', email: 'john@example.com', createdAt: new Date() };
const userName = getProperty(user, 'name'); // string
const userId = getProperty(user, 'id'); // number

// Generic classes with constraints
class Repository<T extends { id: number }> {
  private items: T[] = [];
  
  add(item: T): void {
    this.items.push(item);
  }
  
  findById(id: number): T | undefined {
    return this.items.find(item => item.id === id);
  }
  
  getAll(): readonly T[] {
    return Object.freeze([...this.items]);
  }
}

// Usage
const userRepository = new Repository<User>();
const adminRepository = new Repository<AdminUser>();

// Conditional types for advanced patterns
type NonNullable<T> = T extends null | undefined ? never : T;
type ApiResult<T> = T extends Promise<infer U> ? ApiResponse<U> : ApiResponse<T>;
```

### Utility Types
```typescript
// Built-in utility types for common transformations
interface UserUpdate {
  name?: string;
  email?: string;
  // Don't repeat all User properties manually
}

// Better: Use utility types
type UserUpdate = Partial<Pick<User, 'name' | 'email'>>;
type UserCreateData = Omit<User, 'id' | 'createdAt' | 'updatedAt'>;
type UserDisplay = Pick<User, 'id' | 'name' | 'email'>;

// Custom utility types
type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
type WithTimestamps<T> = T & {
  createdAt: Date;
  updatedAt: Date;
};

// Usage
type UserOptionalEmail = Optional<User, 'email'>; // email becomes optional
type UserWithTimestamps = WithTimestamps<UserCreateData>;
```

### Type Guards & Assertion Functions
```typescript
// Type guards for runtime type checking
function isString(value: unknown): value is string {
  return typeof value === 'string';
}

function isUser(obj: unknown): obj is User {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'id' in obj &&
    'name' in obj &&
    'email' in obj &&
    typeof (obj as User).id === 'number' &&
    typeof (obj as User).name === 'string' &&
    typeof (obj as User).email === 'string'
  );
}

// Assertion functions for validation
function assertIsNumber(value: unknown): asserts value is number {
  if (typeof value !== 'number') {
    throw new Error(`Expected number, got ${typeof value}`);
  }
}

function assertIsUser(obj: unknown): asserts obj is User {
  if (!isUser(obj)) {
    throw new Error('Invalid user object');
  }
}

// Usage
function processUserData(data: unknown): void {
  assertIsUser(data);
  // TypeScript now knows data is User
  console.log(`Processing user: ${data.name}`);
}
```

## Advanced TypeScript Patterns

### Module Declaration & Ambient Types
```typescript
// Declare types for external libraries
declare module 'external-library' {
  export interface LibraryConfig {
    apiKey: string;
    timeout: number;
  }
  
  export function initialize(config: LibraryConfig): void;
}

// Augment existing module types
declare module 'express-session' {
  interface SessionData {
    userId?: number;
    theme?: Theme;
  }
}

// Global type augmentation
declare global {
  interface Window {
    __APP_CONFIG__: {
      apiUrl: string;
      debug: boolean;
    };
  }
}
```

### Branded Types for Type Safety
```typescript
// Branded types prevent mixing similar primitive types
type UserId = number & { readonly brand: unique symbol };
type ProductId = number & { readonly brand: unique symbol };

function createUserId(id: number): UserId {
  return id as UserId;
}

function createProductId(id: number): ProductId {
  return id as ProductId;
}

function getUser(id: UserId): Promise<User> {
  // Implementation
}

function getProduct(id: ProductId): Promise<Product> {
  // Implementation
}

// Type safety in action
const userId = createUserId(123);
const productId = createProductId(456);

getUser(userId); // ✓ Correct
getProduct(productId); // ✓ Correct
// getUser(productId); // ✗ TypeScript error
// getProduct(userId); // ✗ TypeScript error
```

### Template Literal Types
```typescript
// Template literal types for string patterns
type HttpRoute = `/${string}`;
type ApiVersion = `v${number}`;
type FullApiRoute = `${ApiVersion}${HttpRoute}`;

// Examples
const validRoute: FullApiRoute = 'v1/users'; // ✓
const validRoute2: FullApiRoute = 'v2/products/123'; // ✓
// const invalidRoute: FullApiRoute = 'users'; // ✗ TypeScript error

// Dynamic property names
type EventType = 'click' | 'hover' | 'focus';
type EventHandlers = {
  [K in EventType as `on${Capitalize<K>}`]: (event: Event) => void;
};

// Results in:
// {
//   onClick: (event: Event) => void;
//   onHover: (event: Event) => void;
//   onFocus: (event: Event) => void;
// }
```

## React/Framework Integration

### React Component Typing
```typescript
import React, { useState, useEffect, ReactNode } from 'react';

// Props interface with proper typing
interface ChatWidgetProps {
  backendUrl?: string;
  theme?: Theme;
  onMessageSent?: (message: string) => void;
  onError?: (error: Error) => void;
  children?: ReactNode; // For composition
  className?: string;
}

// Component with default props
const ChatWidget: React.FC<ChatWidgetProps> = ({
  backendUrl = window.location.origin,
  theme = 'auto',
  onMessageSent,
  onError,
  className = ''
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  
  // Event handlers with proper typing
  const handleSendMessage = async (content: string): Promise<void> => {
    try {
      setIsLoading(true);
      const response = await sendMessage(content);
      setMessages(prev => [...prev, response]);
      onMessageSent?.(content); // Optional callback
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className={`chat-widget ${className}`}>
      {/* Component JSX */}
    </div>
  );
};

// Hook typing
function useChatWidget(config: ChatConfig) {
  const [state, setState] = useState<AsyncState>({ status: 'loading' });
  
  useEffect(() => {
    // Effect with proper cleanup typing
    const controller = new AbortController();
    
    const loadData = async (): Promise<void> => {
      try {
        const data = await fetchChatData(config, controller.signal);
        setState({ status: 'success', data });
      } catch (error) {
        if (!controller.signal.aborted) {
          setState({ status: 'error', error: (error as Error).message });
        }
      }
    };
    
    loadData();
    
    return () => {
      controller.abort();
    };
  }, [config]);
  
  return state;
}
```

### Event Handling Types
```typescript
// DOM event handlers with proper typing
function handleInputChange(event: React.ChangeEvent<HTMLInputElement>): void {
  const value = event.target.value;
  // Handle input change
}

function handleFormSubmit(event: React.FormEvent<HTMLFormElement>): void {
  event.preventDefault();
  // Handle form submission
}

function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>): void {
  if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
    event.preventDefault();
    // Handle Ctrl+Enter
  }
}

// Custom event types for application events
interface CustomEventMap {
  'user-login': { userId: number; timestamp: Date };
  'message-sent': { messageId: string; content: string };
  'theme-changed': { theme: Theme };
}

type CustomEventType = keyof CustomEventMap;

class EventEmitter<T extends Record<string, unknown>> {
  private listeners: Partial<{
    [K in keyof T]: Array<(data: T[K]) => void>;
  }> = {};
  
  on<K extends keyof T>(event: K, callback: (data: T[K]) => void): void {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event]!.push(callback);
  }
  
  emit<K extends keyof T>(event: K, data: T[K]): void {
    const callbacks = this.listeners[event];
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }
  }
}

// Usage
const appEvents = new EventEmitter<CustomEventMap>();
appEvents.on('user-login', (data) => {
  // data is typed as { userId: number; timestamp: Date }
  console.log(`User ${data.userId} logged in at ${data.timestamp}`);
});
```

## File Organization for TypeScript

### Project Structure
```typescript
// Large TypeScript project structure
src/
├── types/
│   ├── index.ts          // Main type exports
│   ├── api.ts            // API-related types
│   ├── user.ts           // User-related types
│   └── events.ts         // Event types
├── interfaces/
│   ├── IUserService.ts   // Service contracts
│   ├── IApiClient.ts     // API client interface
│   └── IEventEmitter.ts  // Event emitter interface
├── models/
│   ├── User.ts           // User class/model
│   ├── Session.ts        // Session model
│   └── Message.ts        // Message model
├── services/
│   ├── UserService.ts    // User service implementation
│   ├── ApiClient.ts      // API client implementation
│   └── EventEmitter.ts   // Event emitter implementation
├── utils/
│   ├── typeGuards.ts     // Type guard functions
│   ├── validators.ts     // Validation utilities
│   └── formatters.ts     // Formatting utilities
└── components/
    ├── ChatWidget.tsx    // React components
    └── MessageList.tsx
```

### Type-Only Imports
```typescript
// Use type-only imports when only importing types
import type { User, UserCreateData } from './types/user.js';
import type { ApiResponse } from './types/api.js';

// Regular imports for values
import { validateUser, formatUserName } from './utils/userUtils.js';
import { UserService } from './services/UserService.js';

// Mixed imports
import { type Theme, getDefaultTheme } from './types/theme.js';
```

### Declaration Files
```typescript
// types/globals.d.ts - Global type declarations
declare global {
  namespace NodeJS {
    interface ProcessEnv {
      NODE_ENV: 'development' | 'production' | 'test';
      API_URL: string;
      DATABASE_URL: string;
      SECRET_KEY: string;
    }
  }
  
  interface Window {
    gtag?: (...args: unknown[]) => void;
    dataLayer?: unknown[];
  }
}

export {}; // Make this a module

// types/api.d.ts - API type declarations
export interface ApiEndpoints {
  users: {
    GET: { response: User[] };
    POST: { body: UserCreateData; response: User };
  };
  'users/:id': {
    GET: { params: { id: string }; response: User };
    PUT: { params: { id: string }; body: UserUpdate; response: User };
    DELETE: { params: { id: string }; response: void };
  };
}
```

## Configuration & Tooling

### TypeScript Configuration
```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "emitDeclarationOnly": true,
    "sourceMap": true,
    "outDir": "./dist",
    "removeComments": false,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "allowUnreachableCode": false,
    "allowUnusedLabels": false,
    "exactOptionalPropertyTypes": true,
    "skipLibCheck": true
  },
  "include": [
    "src/**/*",
    "types/**/*"
  ],
  "exclude": [
    "node_modules",
    "dist",
    "**/*.test.ts",
    "**/*.spec.ts"
  ]
}
```

### ESLint Configuration for TypeScript
```json
// .eslintrc.json
{
  "extends": [
    "eslint:recommended",
    "@typescript-eslint/recommended",
    "@typescript-eslint/recommended-requiring-type-checking"
  ],
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "project": "./tsconfig.json"
  },
  "plugins": ["@typescript-eslint"],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/no-explicit-any": "warn",
    "@typescript-eslint/explicit-function-return-type": "error",
    "@typescript-eslint/no-unsafe-assignment": "error",
    "@typescript-eslint/no-unsafe-member-access": "error",
    "@typescript-eslint/no-unsafe-call": "error",
    "@typescript-eslint/no-unsafe-return": "error",
    "@typescript-eslint/prefer-as-const": "error",
    "@typescript-eslint/prefer-nullish-coalescing": "error",
    "@typescript-eslint/prefer-optional-chain": "error",
    "@typescript-eslint/strict-boolean-expressions": "error"
  }
}
```

## Testing with TypeScript

### Jest Configuration
```typescript
// jest.config.ts
import type { Config } from '@jest/types';

const config: Config.InitialOptions = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src'],
  testMatch: ['**/__tests__/**/*.ts', '**/?(*.)+(spec|test).ts'],
  transform: {
    '^.+\\.ts$': 'ts-jest',
  },
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/**/*.test.ts',
    '!src/**/*.spec.ts',
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
};

export default config;
```

### Type-Safe Testing
```typescript
// __tests__/userService.test.ts
import { jest } from '@jest/globals';
import type { MockedFunction } from 'jest-mock';
import { UserService } from '../services/UserService';
import type { User, UserCreateData } from '../types/user';

// Mock with proper typing
const mockApiClient = {
  fetchUser: jest.fn() as MockedFunction<(id: number) => Promise<User>>,
  createUser: jest.fn() as MockedFunction<(data: UserCreateData) => Promise<User>>,
};

describe('UserService', () => {
  let userService: UserService;
  
  beforeEach(() => {
    userService = new UserService(mockApiClient);
    jest.clearAllMocks();
  });
  
  describe('getUser', () => {
    it('should return user when found', async () => {
      // Arrange
      const expectedUser: User = {
        id: 1,
        name: 'John Doe',
        email: 'john@example.com',
        createdAt: new Date(),
      };
      mockApiClient.fetchUser.mockResolvedValue(expectedUser);
      
      // Act
      const result = await userService.getUser(1);
      
      // Assert
      expect(result).toEqual(expectedUser);
      expect(mockApiClient.fetchUser).toHaveBeenCalledWith(1);
    });
    
    it('should handle user not found', async () => {
      // Arrange
      mockApiClient.fetchUser.mockRejectedValue(new Error('User not found'));
      
      // Act & Assert
      await expect(userService.getUser(999)).rejects.toThrow('User not found');
    });
  });
});
```

## Project-Specific Standards

### For Astro + Preact Projects
```typescript
// astro-env.d.ts
/// <reference types="astro/client" />

interface ImportMetaEnv {
  readonly PUBLIC_API_URL: string;
  readonly PUBLIC_ENABLE_WIDGET: string;
  readonly DATABASE_URL: string;
  readonly SECRET_KEY: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// Component props for Astro integration
interface AstroComponentProps {
  class?: string;
  'data-testid'?: string;
}

interface ChatWidgetAstroProps extends AstroComponentProps {
  backendUrl?: string;
  theme?: Theme;
  'client:load'?: boolean;
  'client:visible'?: boolean;
}
```

## References

- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [TypeScript ESLint Rules](https://typescript-eslint.io/rules/)
- [Utility Types Reference](https://www.typescriptlang.org/docs/handbook/utility-types.html)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [Jest TypeScript Setup](https://jestjs.io/docs/getting-started#using-typescript)
