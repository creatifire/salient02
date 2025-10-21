<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Agent Conversation Loading Tests - TASK 0017-003-005

> Automated test suite for agent conversation loading functionality with cross-endpoint continuity

## Test Coverage Overview

### CHUNK 0017-003-005-01 - Agent Session Service
**File**: `unit/test_agent_session.py`
- **`TestLoadAgentConversation`**:
  - `test_load_agent_conversation_empty_session()` - Empty session handling
  - `test_load_agent_conversation_message_conversion()` - DB to Pydantic AI format conversion
  - `test_load_agent_conversation_user_role_mapping()` - Role mapping (human/user → ModelRequest)
  - `test_load_agent_conversation_invalid_session_id()` - Error handling for invalid UUIDs

- **`TestGetSessionStats`**:
  - `test_get_session_stats_empty_session()` - Empty session analytics
  - `test_get_session_stats_with_conversation()` - Multi-source conversation analytics
  - `test_get_session_stats_unbalanced_conversation()` - Uneven human/assistant ratios
  - `test_get_session_stats_no_metadata_sources()` - Messages without source metadata

### CHUNK 0017-003-005-02 - Simple Chat Integration
**File**: `unit/test_simple_chat_agent.py`
- **`TestSimpleChatAgentIntegration`**:
  - `test_simple_chat_auto_load_history()` - Automatic history loading when `message_history=None`
  - `test_simple_chat_with_provided_history()` - No auto-loading when history explicitly provided
  - `test_simple_chat_empty_history_handling()` - Graceful handling of empty conversation history
  - `test_simple_chat_session_bridging_logging()` - Analytics logging verification
  - `test_simple_chat_cost_tracking_preserved()` - Cost tracking functionality preservation
  - `test_simple_chat_conversation_loading_error_handling()` - Error scenario handling

### CHUNK 0017-003-005-03 - Session Analytics & Monitoring
**Covered in**: `unit/test_agent_session.py` (`TestGetSessionStats`) and integration tests

### Feature-Level Integration Tests
**File**: `integration/test_agent_conversation_loading.py`
- **`TestAgentConversationLoadingIntegration`**:
  - `test_load_agent_conversation_with_db()` - Full database workflow with real messages
  - `test_simple_chat_cross_endpoint_continuity()` - Cross-endpoint conversation flow
  - `test_session_analytics_end_to_end()` - Multi-source conversation analytics
  - `test_agent_conversation_loading_workflow()` - Complete feature workflow
  - `test_conversation_loading_performance()` - Performance impact testing
  - `test_conversation_loading_edge_cases()` - Error handling and edge cases

## Running the Tests

### Quick Unit Tests (Fast)
```bash
# From backend directory
python run_agent_conversation_tests.py --quick
```

### Complete Test Suite
```bash
python run_agent_conversation_tests.py
```

### Individual Test Files
```bash
# Unit tests only
pytest tests/unit/test_agent_session.py -v
pytest tests/unit/test_simple_chat_agent.py -v

# Integration tests only
pytest tests/integration/test_agent_conversation_loading.py -v -m integration

# With coverage
pytest tests/unit/test_agent_session.py tests/unit/test_simple_chat_agent.py --cov=app.services.agent_session --cov=app.agents.simple_chat --cov-report=term-missing
```

## Test Dependencies

### Unit Tests
- **No external dependencies** - All external services mocked
- **Fast execution** - Typically < 1 second per test
- **Isolated testing** - Each test can run independently

### Integration Tests
- **Real database connection** - Uses test database isolation
- **Requires initialized database** - `await initialize_database()` called in fixtures
- **Slower execution** - Involves actual database operations

## Test Data Patterns

### Mock Message Format
```python
Message(
    id=uuid.uuid4(),
    session_id=session_id,
    role="human" | "assistant" | "system",
    content="Message content",
    created_at=datetime.now(timezone.utc),
    meta={"source": "test_source", "test": "metadata"}
)
```

### Expected Pydantic AI Conversion
```python
# human/user → ModelRequest
ModelRequest(parts=[UserPromptPart(
    content="User message",
    timestamp=datetime
)])

# assistant → ModelResponse  
ModelResponse(
    parts=[TextPart(content="Assistant response")],
    usage=None,
    model_name="agent-session",
    timestamp=datetime
)
```

## Assertions Patterns

### Conversation Loading
```python
# Basic loading
assert len(conversation) == expected_count
assert isinstance(conversation[0], ModelRequest)
assert isinstance(conversation[1], ModelResponse)

# Content preservation
assert conversation[0].parts[0].content == "Expected content"
```

### Session Analytics
```python
# Basic stats
assert stats['total_messages'] == expected_count
assert stats['cross_endpoint_continuity'] == True/False

# Message breakdown
assert stats['message_breakdown']['human'] == expected_human_count
assert stats['message_breakdown']['assistant'] == expected_assistant_count

# Cross-endpoint detection
assert stats['recent_activity']['cross_endpoint_evidence'] == True
assert 'source1' in stats['recent_activity']['sources_detected']
```

## Coverage Goals

### Unit Tests (Target: 90%+ coverage)
- **Core Functions**: `load_agent_conversation()`, `get_session_stats()`
- **Integration Logic**: Simple chat history loading
- **Edge Cases**: Invalid inputs, empty sessions, error scenarios

### Integration Tests (Target: Key workflows covered)
- **Cross-endpoint continuity**: Legacy → Agent endpoint conversation flow
- **Database operations**: Real message storage and retrieval
- **Performance**: History loading impact on response times
- **Error handling**: Database failures, malformed data

## Test Maintenance

### When to Update Tests
- **Function signature changes**: Update mocks and assertions
- **New functionality**: Add corresponding test cases
- **Bug fixes**: Add regression tests
- **Performance changes**: Update performance thresholds

### Test Data Management
- **Use fixtures** for reusable test data
- **Mock external services** in unit tests
- **Isolate test data** in integration tests
- **Clean up** after integration tests (handled by database isolation)

## Debugging Failed Tests

### Common Issues
1. **Mock configuration**: Ensure all external dependencies are properly mocked
2. **Async handling**: Verify `AsyncMock` used for async functions
3. **Database state**: Check test isolation in integration tests
4. **Import paths**: Verify correct module imports in patches

### Debug Commands
```bash
# Verbose output with full tracebacks
pytest tests/unit/test_agent_session.py::TestLoadAgentConversation::test_load_agent_conversation_message_conversion -vvv --tb=long

# Run single test with debugging
pytest tests/unit/test_agent_session.py::test_specific_test -s --pdb
```

This test suite provides comprehensive coverage of the agent conversation loading functionality while maintaining fast feedback cycles through isolated unit tests and thorough integration validation.
