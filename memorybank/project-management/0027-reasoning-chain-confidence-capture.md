# Epic 0027: Reasoning Chain & Confidence Score Capture

**Status**: PROPOSED  
**Priority**: P2 (Enhancement)  
**Created**: 2025-01-14  
**Owner**: Engineering  
**Dependencies**: Epic 0026 (Simple Admin Frontend)

---

## 📋 **Epic Summary**

Capture and display LLM reasoning chains and confidence scores in the admin UI to provide transparency into how models arrive at their responses. This enhances debugging capabilities for complex agents and helps evaluate model performance.

**Key Value**: Enable product owners and developers to see the "thinking process" behind LLM responses, improving trust and facilitating better prompt engineering.

---

## 🎯 **Goals**

1. **Capture Reasoning Chains**: Extract reasoning tokens/thinking content from models that support it (o1/o3, Claude Extended Thinking, DeepSeek R1, Gemini DeepThink)
2. **Capture Confidence Scores**: Calculate confidence metrics from available data (logprobs, token probabilities)
3. **Store in Database**: Save reasoning and confidence data in `messages.meta` field
4. **Display in Admin UI**: Leverage existing UI component (already implemented in Phase 3B) to show captured data

---

## 🏗️ **Architecture Overview**

```
┌─────────────────────┐
│   OpenRouter API    │ ← Models: o1/o3, Claude, DeepSeek, Gemini
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  OpenRouterModel    │ ← Extract reasoning/confidence from response
│  (_process_response)│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   simple_chat.py    │ ← Capture metadata from result.provider_details
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  MessageService     │ ← Store in messages.meta.reasoning_chain
│                     │   and messages.meta.confidence_score
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   session.html      │ ← Display in "✨ Response Quality" section
│   (Admin UI)        │   (ALREADY IMPLEMENTED - lines 106-122)
└─────────────────────┘
```

---

## 📊 **Data Format Specification**

### **Database Schema**

**Table**: `messages`  
**Field**: `meta` (JSONB)

**Structure**:
```json
{
  "tool_calls": [...],  // Existing
  "model": "...",       // Existing
  "input_tokens": 0,    // Existing
  "output_tokens": 0,   // Existing
  "cost": 0.0,          // Existing
  "latency_ms": 0,      // Existing
  
  // NEW: Reasoning chain data
  "reasoning_chain": "Step 1: Analyze the query...\nStep 2: Consider options...\nStep 3: Select best approach...",
  "reasoning_tokens": 1500,  // Optional: token count for reasoning (o1/o3 only)
  
  // NEW: Confidence score (0.0 - 1.0)
  "confidence_score": 0.87  // Average token probability or self-consistency score
}
```

### **Model-Specific Formats**

#### **OpenAI o1/o3 Models**
```json
{
  "reasoning_chain": "Reasoning content from model...",
  "reasoning_tokens": 1500,
  "reasoning_model": "openai/o1"
}
```

#### **Claude Extended Thinking**
```json
{
  "reasoning_chain": "Thinking process from Claude...",
  "reasoning_model": "anthropic/claude-3.7-sonnet",
  "thinking_tokens": 800
}
```

#### **DeepSeek R1**
```json
{
  "reasoning_chain": "Chain of thought from DeepSeek...",
  "reasoning_model": "deepseek/deepseek-r1"
}
```

#### **Confidence Scores (from logprobs)**
```json
{
  "confidence_score": 0.87,
  "confidence_method": "logprobs_average",
  "confidence_details": {
    "min_token_prob": 0.45,
    "max_token_prob": 0.98,
    "avg_token_prob": 0.87,
    "token_count": 120
  }
}
```

---

## 🔧 **Implementation Plan**

### **Phase 1: OpenRouter Model Enhancement** (2-3 hours)

**File**: `backend/app/agents/openrouter.py`

#### **Task 0027-001: Extract Reasoning Chain from Response**

**Location**: `OpenRouterModel._process_response()` method (lines 95-137)

**Changes**:
```python
def _process_response(self, response: ChatCompletion | str) -> ModelResponse:
    model_response = super()._process_response(response)
    
    if isinstance(response, ChatCompletion) and response.usage:
        openrouter_data = {}
        
        # ... existing cost extraction ...
        
        # NEW: Extract reasoning tokens (o1/o3 models)
        if hasattr(response.usage, 'completion_tokens_details'):
            details = response.usage.completion_tokens_details
            if hasattr(details, 'reasoning_tokens') and details.reasoning_tokens:
                openrouter_data['reasoning_tokens'] = details.reasoning_tokens
        
        # NEW: Extract reasoning content (if provided)
        if hasattr(response, 'choices') and response.choices:
            choice = response.choices[0]
            
            # Check for reasoning in message content
            if hasattr(choice, 'message') and hasattr(choice.message, 'reasoning_content'):
                openrouter_data['reasoning_content'] = choice.message.reasoning_content
            
            # Check for thinking blocks (Claude extended thinking)
            if hasattr(choice.message, 'content') and isinstance(choice.message.content, list):
                for content_block in choice.message.content:
                    if hasattr(content_block, 'type') and content_block.type == 'thinking':
                        openrouter_data['reasoning_content'] = content_block.text
                        break
        
        # Store in provider_details
        if openrouter_data:
            if model_response.provider_details is None:
                model_response.provider_details = openrouter_data
            else:
                model_response.provider_details.update(openrouter_data)
    
    return model_response
```

**Verification**:
- [ ] Reasoning tokens captured for o1/o3 models
- [ ] Reasoning content captured for Claude extended thinking
- [ ] Data stored in `provider_details` dict

---

#### **Task 0027-002: Extract Confidence Scores from Logprobs**

**Location**: `OpenRouterModel._process_response()` method

**Prerequisites**:
- Update `create_openrouter_provider_with_cost_tracking()` to request logprobs

**Step 1**: Modify provider creation (`openrouter.py` lines 67-75):
```python
async def create_with_usage(**kwargs):
    # Always include usage tracking
    extra_body = kwargs.get('extra_body') or {}
    if not isinstance(extra_body, dict):
        extra_body = {}
    extra_body.setdefault('usage', {})['include'] = True
    kwargs['extra_body'] = extra_body
    
    # NEW: Request logprobs for confidence estimation (OpenAI models only)
    # Note: Only supported by some models (GPT-4, GPT-3.5, o1, etc.)
    if 'logprobs' not in kwargs:
        kwargs['logprobs'] = True
        kwargs['top_logprobs'] = 1  # Just need the top probability
    
    return await original_create(**kwargs)
```

**Step 2**: Extract confidence in `_process_response()`:
```python
# NEW: Calculate confidence from logprobs
if hasattr(response, 'choices') and response.choices:
    choice = response.choices[0]
    if hasattr(choice, 'logprobs') and choice.logprobs and choice.logprobs.content:
        import math
        
        token_probs = []
        for token_data in choice.logprobs.content:
            if token_data and hasattr(token_data, 'logprob'):
                # Convert log probability to probability: P = e^(logprob)
                prob = math.exp(token_data.logprob)
                token_probs.append(prob)
        
        if token_probs:
            avg_confidence = sum(token_probs) / len(token_probs)
            openrouter_data['confidence_score'] = round(avg_confidence, 3)
            openrouter_data['confidence_method'] = 'logprobs_average'
            openrouter_data['confidence_details'] = {
                'min_token_prob': round(min(token_probs), 3),
                'max_token_prob': round(max(token_probs), 3),
                'token_count': len(token_probs)
            }
```

**Verification**:
- [ ] Logprobs requested in API call
- [ ] Confidence score calculated (0.0 - 1.0)
- [ ] Confidence method and details stored

**Note**: Logprobs are only supported by OpenAI models (GPT-4, GPT-3.5, o1). Other models will simply not have this data.

---

### **Phase 2: Simple Chat Agent Integration** (1-2 hours)

**File**: `backend/app/agents/simple_chat.py`

#### **Task 0027-003: Capture Reasoning Data from Result**

**Location**: Lines 510-537 (after cost extraction)

**Changes**:
```python
# Get the latest message response with OpenRouter metadata
new_messages = result.new_messages()
if new_messages:
    latest_message = new_messages[-1]  # Last message (assistant response)
    
    reasoning_data = {}
    
    if hasattr(latest_message, 'provider_details') and latest_message.provider_details:
        # ... existing cost extraction ...
        
        # NEW: Extract reasoning chain
        if 'reasoning_content' in latest_message.provider_details:
            reasoning_data['reasoning_chain'] = latest_message.provider_details['reasoning_content']
        
        # NEW: Extract reasoning tokens count (o1/o3 models)
        if 'reasoning_tokens' in latest_message.provider_details:
            reasoning_data['reasoning_tokens'] = latest_message.provider_details['reasoning_tokens']
        
        # NEW: Extract confidence score
        if 'confidence_score' in latest_message.provider_details:
            reasoning_data['confidence_score'] = latest_message.provider_details['confidence_score']
            reasoning_data['confidence_method'] = latest_message.provider_details.get('confidence_method', 'unknown')
        
        # Store for later use in message metadata
        if reasoning_data:
            logfire.info(
                'agent.reasoning_captured',
                session_id=session_id,
                has_reasoning_chain=bool(reasoning_data.get('reasoning_chain')),
                has_confidence_score=bool(reasoning_data.get('confidence_score')),
                reasoning_tokens=reasoning_data.get('reasoning_tokens', 0),
                model=requested_model
            )
```

**Verification**:
- [ ] Reasoning data extracted from `provider_details`
- [ ] Data logged for monitoring
- [ ] Ready to pass to message service

---

#### **Task 0027-004: Store Reasoning Data in Messages**

**Location**: Lines 697-705 (message saving)

**Changes**:
```python
# Extract tool calls from result for admin debugging
tool_calls_meta = []
if result.all_messages():
    from pydantic_ai.messages import ToolCallPart, ToolReturnPart
    for msg in result.all_messages():
        if hasattr(msg, 'parts'):
            for part in msg.parts:
                if isinstance(part, ToolCallPart):
                    tool_calls_meta.append({
                        "tool_name": part.tool_name,
                        "args": part.args
                    })

# NEW: Build complete metadata (tool calls + reasoning data)
assistant_metadata = {}
if tool_calls_meta:
    assistant_metadata['tool_calls'] = tool_calls_meta

# NEW: Add reasoning data if captured
if reasoning_data:
    assistant_metadata.update(reasoning_data)

# Save assistant response with complete metadata
await message_service.save_message(
    session_id=UUID(session_id),
    agent_instance_id=agent_instance_id,
    llm_request_id=llm_request_id,
    role="assistant",
    content=response_text,
    metadata=assistant_metadata if assistant_metadata else None  # NEW: Complete metadata
)
```

**Verification**:
- [ ] Reasoning chain stored in `messages.meta.reasoning_chain`
- [ ] Confidence score stored in `messages.meta.confidence_score`
- [ ] Tool calls preserved in same metadata
- [ ] Database query confirms data storage

---

#### **Task 0027-005: Update Streaming Implementation**

**File**: `backend/app/agents/simple_chat.py`  
**Location**: `simple_chat_stream()` function (lines 1190-1211)

**Changes**: Apply same reasoning data capture logic to streaming responses.

```python
# Extract tool calls AND reasoning data from result for admin debugging
tool_calls_meta = []
reasoning_data = {}

if result.all_messages():
    from pydantic_ai.messages import ToolCallPart
    
    # Get latest message for reasoning data
    latest_message = result.all_messages()[-1]
    
    # Extract tool calls
    for msg in result.all_messages():
        if hasattr(msg, 'parts'):
            for part in msg.parts:
                if isinstance(part, ToolCallPart):
                    tool_calls_meta.append({
                        "tool_name": part.tool_name,
                        "args": part.args
                    })
    
    # NEW: Extract reasoning data
    if hasattr(latest_message, 'provider_details') and latest_message.provider_details:
        if 'reasoning_content' in latest_message.provider_details:
            reasoning_data['reasoning_chain'] = latest_message.provider_details['reasoning_content']
        if 'reasoning_tokens' in latest_message.provider_details:
            reasoning_data['reasoning_tokens'] = latest_message.provider_details['reasoning_tokens']
        if 'confidence_score' in latest_message.provider_details:
            reasoning_data['confidence_score'] = latest_message.provider_details['confidence_score']

# Build complete metadata
assistant_metadata = {}
if tool_calls_meta:
    assistant_metadata['tool_calls'] = tool_calls_meta
if reasoning_data:
    assistant_metadata.update(reasoning_data)

# Save assistant response with complete metadata
await message_service.save_message(
    session_id=UUID(session_id),
    agent_instance_id=agent_instance_id,
    llm_request_id=llm_request_id,
    role="assistant",
    content=response_text,
    metadata=assistant_metadata if assistant_metadata else None
)
```

**Verification**:
- [ ] Streaming responses include reasoning data
- [ ] Same metadata structure as non-streaming

---

### **Phase 3: Model Configuration** (1 hour)

#### **Task 0027-006: Enable Reasoning Mode for Supported Models**

**File**: `backend/app/agents/simple_chat.py`  
**Location**: Agent creation logic (around lines 350-375)

**Goal**: Automatically enable reasoning features when using compatible models.

**Changes**:
```python
# Determine if model supports reasoning features
model_supports_reasoning = any([
    'o1' in requested_model.lower(),
    'o3' in requested_model.lower(),
    'deepseek-r1' in requested_model.lower()
])

model_supports_extended_thinking = 'claude' in requested_model.lower()

# Build model initialization parameters
model_params = {}

if model_supports_reasoning:
    # OpenAI o1/o3 or DeepSeek R1
    model_params['reasoning_effort'] = 'high'  # 'low', 'medium', 'high'
    model_params['reasoning_enabled'] = True
    logfire.info(
        'agent.model.reasoning_enabled',
        model=requested_model,
        reasoning_effort='high'
    )

if model_supports_extended_thinking:
    # Claude extended thinking mode
    model_params['thinking_budget'] = 10000  # tokens allocated for thinking
    logfire.info(
        'agent.model.extended_thinking_enabled',
        model=requested_model,
        thinking_budget=10000
    )

# Create OpenRouter provider with reasoning parameters
# Note: These parameters should be passed to the model via extra_body
# Update create_openrouter_provider_with_cost_tracking() if needed
```

**Configuration Options** (for future `app.yaml` or instance configs):
```yaml
model_settings:
  model: "openai/o1"
  reasoning:
    enabled: true
    effort: "high"  # low, medium, high
    max_tokens: 5000  # max reasoning tokens
  
  # OR for Claude
  extended_thinking:
    enabled: true
    budget: 10000  # thinking budget in tokens
```

**Verification**:
- [ ] Reasoning mode auto-enabled for o1/o3/DeepSeek
- [ ] Extended thinking enabled for Claude
- [ ] Parameters logged for monitoring
- [ ] Future: Configuration file support

---

### **Phase 4: UI Integration** (Already Complete ✅)

#### **Current Status**: UI Ready

**File**: `web/public/admin/session.html` (lines 106-122)

**Existing Implementation**:
```javascript
${!isUser && msg.meta && (msg.meta.confidence_score || msg.meta.reasoning_chain) ? `
    <div class="mt-3 p-3 bg-green-50 rounded border border-green-200">
        <p class="text-xs font-semibold text-green-800 mb-2">✨ Response Quality:</p>
        <div class="space-y-2 text-xs">
            ${msg.meta.confidence_score ? `
                <div><span class="font-medium text-green-700">Confidence:</span> 
                <span class="text-gray-700">${(msg.meta.confidence_score * 100).toFixed(1)}%</span></div>
            ` : ''}
            ${msg.meta.reasoning_chain ? `
                <div class="mt-2">
                    <span class="font-medium text-green-700">Reasoning Chain:</span>
                    <pre class="mt-1 text-xs text-gray-700 overflow-x-auto whitespace-pre-wrap">${JSON.stringify(msg.meta.reasoning_chain, null, 2)}</pre>
                </div>
            ` : ''}
        </div>
    </div>
` : ''}
```

**Display Format**:
- **Confidence Score**: Displayed as percentage (e.g., "87.5%")
- **Reasoning Chain**: Displayed as preformatted text (preserves line breaks)
- **Color Coding**: Green background to distinguish from other metadata
- **Conditional Display**: Only shows when data is available

**No Changes Needed** - UI will automatically display data once backend captures it.

---

## 🧪 **Testing Plan**

### **Manual Tests**

#### **Test 0027-001: o1 Model Reasoning Capture**
1. Configure agent to use `openai/o1` model
2. Send a complex query requiring reasoning
3. Check admin UI for reasoning chain display
4. Verify database: `SELECT meta->'reasoning_chain' FROM messages WHERE ...`

**Expected Result**:
- Reasoning chain visible in green "Response Quality" box
- Token count shown in metadata

---

#### **Test 0027-002: Claude Extended Thinking**
1. Configure agent to use `anthropic/claude-3.7-sonnet`
2. Enable extended thinking mode
3. Send a query requiring deep analysis
4. Check admin UI for thinking content

**Expected Result**:
- Thinking process visible as reasoning chain
- Clearly formatted with line breaks

---

#### **Test 0027-003: Confidence Scores (GPT-4)**
1. Configure agent to use `openai/gpt-4`
2. Send multiple queries
3. Observe confidence scores in admin UI

**Expected Result**:
- Confidence displayed as percentage (e.g., "92.3%")
- Varies by query complexity
- Higher confidence for simple queries

---

#### **Test 0027-004: Unsupported Models**
1. Configure agent to use model without reasoning support
2. Send queries
3. Verify no reasoning data displayed

**Expected Result**:
- No "Response Quality" section shown
- No errors in logs
- Other metadata (tool calls, LLM metadata) still displayed

---

### **Automated Tests**

```python
# tests/test_reasoning_capture.py

async def test_reasoning_chain_extracted_from_o1_response():
    """Test that reasoning chain is extracted from o1 model response."""
    # Mock OpenRouter response with reasoning tokens
    mock_response = create_mock_chat_completion(
        reasoning_content="Step 1: Analyze...\nStep 2: Consider...",
        reasoning_tokens=1500
    )
    
    model = OpenRouterModel()
    result = model._process_response(mock_response)
    
    assert result.provider_details['reasoning_content'] == "Step 1: Analyze...\nStep 2: Consider..."
    assert result.provider_details['reasoning_tokens'] == 1500


async def test_confidence_score_calculated_from_logprobs():
    """Test that confidence score is calculated from token logprobs."""
    # Mock response with logprobs
    mock_response = create_mock_chat_completion_with_logprobs([
        -0.1,  # High confidence token
        -0.5,  # Medium confidence
        -0.2   # High confidence
    ])
    
    model = OpenRouterModel()
    result = model._process_response(mock_response)
    
    assert 'confidence_score' in result.provider_details
    assert 0.0 <= result.provider_details['confidence_score'] <= 1.0
    assert result.provider_details['confidence_method'] == 'logprobs_average'


async def test_reasoning_data_stored_in_message_metadata():
    """Test that reasoning data is stored in message.meta field."""
    # Create agent and run with mock reasoning response
    session_id = uuid4()
    result = await simple_chat(
        message="Complex query requiring reasoning",
        session_id=str(session_id),
        account_id=test_account_id,
        agent_instance_id=test_agent_id
    )
    
    # Verify message metadata in database
    message = await get_latest_assistant_message(session_id)
    assert message.meta is not None
    assert 'reasoning_chain' in message.meta or 'confidence_score' in message.meta
```

---

## 📝 **Documentation Updates**

### **Files to Update**

1. **`backend/README.md`**:
   - Add section on reasoning chain capture
   - Document supported models
   - Configuration examples

2. **`memorybank/architecture/llm-integration.md`** (if exists):
   - Architecture diagram update
   - Data flow for reasoning capture

3. **`memorybank/project-management/0026-simple-admin-frontend.md`**:
   - Add reference to Epic 0027
   - Note that Phase 3B UI supports reasoning display

---

## 🚀 **Deployment Notes**

### **Rollout Strategy**

**Phase 1**: Backend Implementation (1 week)
- Deploy Tasks 0027-001 through 0027-005
- Monitor logfire for reasoning data capture
- Verify database storage

**Phase 2**: Model Configuration (3 days)
- Enable reasoning mode for test accounts
- A/B test with/without reasoning
- Gather performance metrics

**Phase 3**: Production Rollout (ongoing)
- Gradually enable for all accounts
- Monitor costs (reasoning tokens increase usage)
- User feedback collection

### **Monitoring**

**Key Metrics**:
- `agent.reasoning_captured` - How often reasoning data is captured
- `openrouter_provider_details_debug` - Raw provider metadata
- Token usage increase (reasoning tokens count toward total)

**Alerts**:
- No reasoning captured for o1/o3 models (configuration issue)
- Confidence scores always < 0.5 (prompt quality issue)

---

## 💰 **Cost Considerations**

### **Reasoning Tokens Cost More**

**OpenAI o1 Pricing** (as of 2025-01):
- Input tokens: ~$15 per 1M tokens
- Output tokens: ~$60 per 1M tokens
- **Reasoning tokens**: Count as output tokens

**Example**:
- Query: 100 input tokens
- Reasoning: 1,500 tokens
- Response: 500 tokens
- **Total cost**: (100 × $0.000015) + (2,000 × $0.00006) = **$0.1215**

**Recommendation**:
- Use reasoning models selectively (complex queries only)
- Set `reasoning_effort: medium` for cost balance
- Monitor per-account usage via `llm_requests` cost tracking

---

## 🔮 **Future Enhancements**

### **Self-Consistency Confidence Scores** (Epic 0028)
- Generate multiple responses for same query
- Compare similarity (semantic embeddings)
- Higher similarity = higher confidence
- More expensive but more reliable than logprobs

### **Reasoning Chain Visualization** (Epic 0029)
- Parse structured reasoning steps
- Display as expandable tree
- Highlight decision points
- Show alternative paths considered

### **Reasoning Quality Metrics** (Epic 0030)
- Evaluate reasoning chain coherence
- Detect logical fallacies
- Score reasoning depth
- Compare against human-annotated examples

---

## ✅ **Acceptance Criteria**

- [ ] Reasoning chains captured from o1/o3 models
- [ ] Reasoning chains captured from Claude extended thinking
- [ ] Confidence scores calculated from logprobs (OpenAI models)
- [ ] Data stored in `messages.meta` with correct structure
- [ ] Admin UI displays reasoning chains (preformatted text)
- [ ] Admin UI displays confidence scores (percentage)
- [ ] No errors when models don't support reasoning
- [ ] Logfire monitoring shows capture success rate
- [ ] Documentation updated with model compatibility matrix
- [ ] Streaming responses include reasoning data

---

## 📚 **References**

- **OpenRouter Documentation**: https://openrouter.ai/docs
- **OpenAI o1 Reasoning Guide**: https://platform.openai.com/docs/guides/reasoning
- **Anthropic Extended Thinking**: https://docs.anthropic.com/claude/docs/extended-thinking
- **Pydantic AI Provider Details**: https://ai.pydantic.dev/models/
- **Epic 0026**: Simple Admin Frontend (UI foundation)

---

## 📞 **Support & Questions**

For implementation questions or issues:
1. Check `logfire` for `agent.reasoning_captured` events
2. Query database: `SELECT meta FROM messages WHERE meta ? 'reasoning_chain'`
3. Review OpenRouter response in `openrouter_provider_details_debug` logs
4. Consult model-specific documentation for reasoning parameters

---

**Last Updated**: 2025-01-14  
**Next Review**: After Task 0027-003 completion

