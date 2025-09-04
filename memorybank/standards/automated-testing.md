# Automated Testing Standards

> Barebones minimal automated testing strategy for reliable development and deployment

## Test Categories & Priorities

### **🔴 Critical (Must Have)**
- **Unit Tests**: Core business logic, agent tools, vector operations
- **Integration Tests**: Database operations, API endpoints, agent workflows  
- **Health Checks**: Service availability, external dependencies

### **🟡 Important (Should Have)**
- **End-to-End Tests**: Complete user workflows, chat functionality
- **Performance Tests**: Response times, concurrent load testing
- **Configuration Tests**: Environment setup, agent config loading

### **🟢 Nice to Have**
- **Visual Regression**: Frontend component consistency
- **Load Tests**: High-volume stress testing
- **Security Tests**: Authentication, input validation

## Test Framework Stack

```yaml
Backend (Python):
  unit: pytest + pytest-asyncio
  integration: pytest + testcontainers
  mocking: pytest-mock
  coverage: coverage.py

Frontend (JavaScript):
  unit: Vitest (Astro compatible)
  e2e: Playwright
  visual: Playwright screenshots

CI/CD:
  runner: GitHub Actions
  coverage: Codecov integration
```

## Essential Test Structure

### **Backend Test Organization**
```
backend/tests/
├── unit/
│   ├── test_agents_base.py
│   ├── test_vector_service.py
│   └── test_config_loader.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_database_ops.py
│   └── test_agent_workflows.py
├── fixtures/
│   ├── sample_data.py
│   └── test_configs.py
└── conftest.py
```

### **Frontend Test Organization**
```
web/tests/
├── unit/
│   └── components/
├── integration/
│   └── pages/
└── e2e/
    ├── chat-flow.spec.ts
    └── widget-embed.spec.ts
```

## Critical Test Cases

### **Backend - Core Functions**
```python
# Unit Tests (Fast, No Dependencies)
def test_agent_config_loading():
    """Agent YAML configs load correctly"""
    
def test_vector_search_tool():
    """Vector search returns relevant results"""
    
def test_session_management():
    """Session creation and retrieval"""

# Integration Tests (Real Dependencies)
@pytest.mark.integration
def test_pinecone_connection():
    """Pinecone API connectivity"""
    
@pytest.mark.integration 
def test_chat_endpoint_with_agent():
    """Complete chat workflow with agent response"""
```

### **Frontend - User Flows**
```typescript
// E2E Tests (Complete Workflows)
test('chat conversation works', async ({ page }) => {
  await page.goto('/');
  await page.fill('[data-testid="chat-input"]', 'Hello');
  await page.click('[data-testid="send-button"]');
  await expect(page.locator('[data-testid="chat-response"]')).toBeVisible();
});

test('widget embeds correctly', async ({ page }) => {
  await page.goto('/demo/widget-test');
  await expect(page.locator('#chat-widget')).toBeVisible();
});
```

## Test Data Strategy

### **Test Fixtures**
```python
# backend/tests/fixtures/sample_data.py
@pytest.fixture
def sample_chat_session():
    return {
        "session_id": "test-session-123",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
    }

@pytest.fixture
def mock_vector_results():
    return [
        {"id": "doc-1", "score": 0.9, "text": "Sample relevant content"},
        {"id": "doc-2", "score": 0.8, "text": "Related information"}
    ]
```

### **Environment Isolation**
```yaml
# Test environments
test:
  database: postgresql://test_db
  pinecone: test-index-namespace
  redis: test-session-store
  
integration:  
  database: dockerized postgres
  pinecone: dedicated test index
  external_apis: mock servers
```

## Minimal CI/CD Pipeline

### **GitHub Actions Workflow**
```yaml
# .github/workflows/test.yml
name: Automated Tests
on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt pytest
      - name: Run unit tests
        run: pytest backend/tests/unit/ -v
      - name: Run integration tests
        run: pytest backend/tests/integration/ -v
        
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: cd web && npm install
      - name: Run tests
        run: cd web && npm test
```

## Test Coverage Targets

### **Minimal Coverage Goals**
- **Unit Tests**: 70% code coverage
- **Integration Tests**: All critical API endpoints
- **E2E Tests**: Primary user workflows (chat, widget)
- **Performance**: Response times < 2s for chat endpoints

### **Coverage Exclusions**
- Third-party library code
- Configuration files
- Test fixtures and utilities
- Development-only scripts

## Testing Commands

### **Development Workflow**
```bash
# Backend testing
cd backend
pytest tests/unit/              # Fast unit tests
pytest tests/integration/       # Slower integration tests  
pytest --cov=app tests/         # With coverage report

# Frontend testing
cd web
npm test                        # Unit tests
npm run test:e2e               # End-to-end tests
npm run test:coverage          # Coverage report

# Full test suite
./scripts/run-all-tests.sh     # Complete test run
```

## Quality Gates

### **Pre-Commit Requirements**
- All unit tests passing
- No linting errors (black, ruff, eslint)
- Type checking passes (mypy, tsc)

### **Pre-Deployment Requirements**
- Full test suite passing
- Integration tests with real services
- Performance benchmarks met
- Security scan completed

## Monitoring & Alerts

### **Test Health Monitoring**
- **Test Success Rate**: >95% pass rate
- **Build Time**: <10 minutes total
- **Flaky Test Detection**: <2% flake rate
- **Coverage Trends**: No significant drops

### **Alert Triggers**
- Test suite failure in main branch
- Coverage drops below threshold
- Performance regression detected
- Integration test failures

---

**Philosophy**: Start small, test critical paths first, expand coverage incrementally based on real-world failures and user feedback.
