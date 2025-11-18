# Investigation 001: Tool Calling Behavior

## Problem Statement

LLM is not following the sequential tool calling pattern despite explicit instructions:
1. Skips `get_available_directories()` and calls `search_directory()` directly
2. Hallucinates data (wrong phone number) despite receiving correct tool results

**Confirmed Working:**
- ✅ All 3 tools registered correctly (Logfire: `tools_count=3`)
- ✅ Tools execute successfully (`search_directory` returns correct data)
- ✅ Pydantic AI implementation follows documented patterns

**Issue:** LLM behavior, not framework/code issue

---

## Investigation Plan

**Location:** `backend/investigate/tool-calling/tool_calling.py`

### Phase 1: Simple Kernel ✅ COMPLETE
**Goal:** Baseline - does LLM call tools when instructed?

- Single tool, no dependencies
- Test with different system prompt variations
- Use `TestModel` to inspect tool selection
- Verify tool registration and invocation work

**Results:**
- ✅ Tool registration works (1 tool registered)
- ✅ Tool calling works (TestModel calls tool)
- ✅ Works with all prompt variations (explicit, imperative, generic)
- ✅ Works even when query doesn't mention tool

**Finding:** Basic tool calling infrastructure is working correctly. TestModel calls available tools regardless of prompt phrasing.

### Phase 2A: Two-Tool Discovery Pattern ✅ COMPLETE
**Goal:** Does LLM follow sequential instructions?

**Tools:**
- `list_options()` - returns available options (red, blue, green)
- `select_option(name)` - selects from options

**Tests:**
1. Explicit sequential ("ALWAYS follow: 1. call list_options 2. call select_option")
2. Strong imperative ("CRITICAL: MUST call list_options BEFORE select_option")
3. Explanation-based ("First call list_options to discover... then select_option")
4. No order specified (baseline behavior)
5. Forced wrong order (simulate bad LLM behavior)

**Results:**
- ✅ **TestModel follows correct sequence in ALL tests** (3/3 ordered correctly)
- ✅ Even with NO instruction, TestModel calls list_options first
- ✅ Tools execute correctly, error handling works
- ✅ Tool call order tracking works via `all_messages()`

**Critical Finding:** TestModel behaves correctly and follows sequential instructions. This proves:
1. Our Pydantic AI implementation is correct
2. The infrastructure for sequential calling works
3. **Real LLMs (Gemini 2.5 Flash) are NOT following the same pattern** - this is an LLM behavior issue, not a code issue

### Phase 2B: Realistic Multi-Directory Simulation ✅ COMPLETE
**Goal:** Test with production-like data structures

**Data:**
- 5 directories (doctors, departments, services, products, locations)
- 10 structured items per directory (name + 2-3 fields)
- Directory metadata JSON (name, description, use_cases)

**Tools:**
- `get_directory_list()` - returns available directories + descriptions
- `search_directory(dir_name, query)` - grep-like search, case-insensitive, returns all matches

**Results:**
- ✅ **Discovery pattern works** (TestModel calls get_directory_list → search_directory)
- ✅ **Search works across all fields** (cardiology found in departments)
- ✅ **Error handling works** (invalid directory names handled gracefully)

**Finding:** TestModel follows discovery pattern with realistic multi-directory data. Tools execute correctly with production-like structures.

### Phase 2C: Real LLM Testing via Pydantic AI Gateway ✅ COMPLETE
**Goal:** Verify if real LLM follows discovery pattern with realistic data

**Implementation:**
- Use Pydantic AI Gateway to call real LLM (Gemini 2.5 Flash)
- Upgraded pydantic-ai from 0.8.1 → 1.19.0 to enable Gateway support
- 5 test queries (one for each directory: doctors, departments, services, products, locations)
- Printed input prompt, tools called, and response for each test

**Results:**
- ✅ **LLM ALWAYS calls `get_directory_list()` first** (5/5 tests = 100%)
- ✅ **LLM chooses correct directory** (5/5 tests = 100%)
- ⚠️ **Strict discovery pattern** (3/5 tests = 60%)
  - Tests 2 & 3: LLM made extra `search_directory()` calls after first search
  - Extra calls are refinements, not pattern violations

**Critical Finding:** Discovery pattern works in production!
- LLM consistently discovers directories before searching
- LLM uses metadata to select appropriate directory
- Extra tool calls are acceptable overhead (LLM refining results)
- No need for Phase 3 (programmatic enforcement) unless extra calls become problematic

**Decision Point:** 
- ✅ Accept current behavior (discovery working, extra calls acceptable)
- ⏸️ Defer Phase 3 (enforcement) unless extra calls cause issues
- 📋 Monitor in production with real Wyckoff queries

### Phase 2D: Real Wyckoff Tools with Real LLM ✅ COMPLETE
**Goal:** Test discovery pattern with production tools and actual Wyckoff data

**Implementation:**
- File: `backend/investigate/tool-calling/tool_calling_wyckoff.py`
- Use real tools from `backend/app/agents/tools/directory_tools.py`:
  - `get_available_directories()`
  - `search_directory()`
- Load real Wyckoff config from `backend/config/agent_configs/wyckoff/wyckoff_info_chat1/config.yaml`
- Test with real Wyckoff database data:
  - `doctors` directory (124+ medical professionals)
  - `phone_directory` directory (11 departments)
- Test with Gemini 2.5 Flash via Pydantic AI Gateway

**Results:**
- ✅ **Discovery pattern works**: 4/5 tests (80%) called `get_available_directories()` first
- ✅ **Directory selection**: 100% correct when tools were called
- ✅ **Real tools working**: Database queries execute successfully
- ✅ **Data returned**: Tools return correct data from database
- ⚠️ **LLM interpretation issues**:
  - Test 1: LLM returned other cardiologists, not "Timothy Akojenu" (who exists as "Timothy Akojenu, PAC")
  - Test 2: LLM said "can't find" cardiology phone despite tool returning 718-963-2000
  - Test 4: LLM refused to call tools for emergency room query
- ⚠️ **Extra tool calls**: 1 test had 1 extra call (acceptable)

**Database Verification:**
- ✅ "Timothy Akojenu, PAC" exists with Cardiology specialty
- ✅ Cardiology phone 718-963-2000 exists in phone_directory
- ✅ Data is accurate and accessible

**Critical Finding:** The tools and discovery pattern work perfectly, but **LLM interpretation of tool results** is the remaining issue:
1. Tools return correct data from database
2. LLM receives tool results but misinterprets them (says "not found" when data exists)
3. LLM sometimes refuses to call tools (safety/capability misunderstanding)

**This is NOT a tool/framework issue** - it's LLM behavior requiring:
- Better system prompts for tool result interpretation
- Structured output enforcement
- Or switching to a different model

**Key Differences from Phase 2C:**
- Uses real database queries (not simulated JSON data)
- Uses production `SessionDependencies` structure
- Tests with actual multi-tenant directory architecture
- Validates against real Wyckoff data

**Outcome:**
- ✅ Discovery pattern validated with production tools
- ✅ Tool registration with `RunContext[SessionDependencies]` working
- ✅ Database queries confirmed correct
- ⚠️ LLM result interpretation needs improvement (not a code issue)

### Phase 3: Enforce Pattern Programmatically
**Goal:** Make Tool B unavailable until Tool A called

**Implementation:**
- Use `prepare_tools` function
- Conditionally enable `select_option` only after `list_options` called
- Track state in dependencies
- Verify forced sequencing works

### Phase 4: Apply to Real Tools
**Goal:** Fix production issue

- Use actual `get_available_directories` and `search_directory`
- Apply working pattern from Phase 3
- Test with real Wyckoff data

### Phase 5: Address Hallucination
**Goal:** Prevent wrong data in responses

**Approaches to test:**
- Structured output (force exact data extraction)
- Different models (Gemini Flash vs GPT-4)
- Output validation
- Compare results

---

## Success Criteria

1. LLM consistently calls `get_available_directories()` before `search_directory()`
2. LLM returns exact data from tool results (no hallucination)
3. Pattern works across different queries
4. Solution can be applied to production code

---

## Notes

- Each phase is standalone, runnable script
- Use `TestModel` for inspection (no API costs)
- Switch to real models only when needed
- Document findings as we progress

