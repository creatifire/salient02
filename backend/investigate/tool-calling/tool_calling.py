"""
Investigation 001 - Tool Calling Behavior
Phase 1: Simple Kernel - Baseline tool calling verification
Phase 2A: Two-Tool Discovery Pattern - Sequential calling test
Phase 2B: Realistic Multi-Directory Simulation - Production-like data
Phase 2C: Real LLM Testing - Test with Gemini 2.5 Flash via Pydantic AI Gateway
"""
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from pydantic_ai.messages import ToolCallPart
import json
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# ==============================================================================
# PHASE 1: SIMPLE KERNEL
# ==============================================================================

def simple_tool() -> str:
    """A simple test tool that returns a greeting."""
    return "Hello from the tool!"


def phase1_test1_basic():
    """Test 1: Basic tool registration and calling."""
    print("\n" + "="*70)
    print("PHASE 1 - TEST 1: Basic Tool Calling")
    print("="*70)
    
    test_model = TestModel()
    agent = Agent(
        test_model,
        tools=[simple_tool],
        system_prompt="You are a helpful assistant."
    )
    
    result = agent.run_sync("Please use the simple_tool")
    
    # Inspect what happened
    params = test_model.last_model_request_parameters
    tools = params.function_tools if params else []
    
    print(f"\n📊 Results:")
    print(f"   Tools registered: {len(tools)}")
    print(f"   Tool names: {[t.name for t in tools]}")
    print(f"   Output: {result.output}")
    
    return len(tools) > 0


def phase1_test2_explicit_instruction():
    """Test 2: Explicit instruction to call tool."""
    print("\n" + "="*70)
    print("PHASE 1 - TEST 2: Explicit Instruction")
    print("="*70)
    
    test_model = TestModel()
    agent = Agent(
        test_model,
        tools=[simple_tool],
        system_prompt="When the user asks, call the simple_tool function."
    )
    
    result = agent.run_sync("Call the tool")
    
    # Inspect
    params = test_model.last_model_request_parameters
    tools = params.function_tools if params else []
    
    print(f"\n📊 Results:")
    print(f"   Tools registered: {len(tools)}")
    print(f"   System prompt: 'When the user asks, call the simple_tool function.'")
    print(f"   Output: {result.output}")
    
    return len(tools) > 0


def phase1_test3_imperative_instruction():
    """Test 3: Strong imperative instruction."""
    print("\n" + "="*70)
    print("PHASE 1 - TEST 3: Imperative Instruction")
    print("="*70)
    
    test_model = TestModel()
    agent = Agent(
        test_model,
        tools=[simple_tool],
        system_prompt=(
            "CRITICAL: You MUST call the simple_tool function "
            "for every request. Do NOT respond without calling it."
        )
    )
    
    result = agent.run_sync("What is 2+2?")
    
    # Inspect
    params = test_model.last_model_request_parameters
    tools = params.function_tools if params else []
    
    print(f"\n📊 Results:")
    print(f"   Tools registered: {len(tools)}")
    print(f"   System prompt: 'CRITICAL: You MUST call simple_tool...'")
    print(f"   Output: {result.output}")
    
    return len(tools) > 0


def phase1_test4_no_instruction():
    """Test 4: No instruction - baseline LLM behavior."""
    print("\n" + "="*70)
    print("PHASE 1 - TEST 4: No Instruction (Baseline)")
    print("="*70)
    
    test_model = TestModel()
    agent = Agent(
        test_model,
        tools=[simple_tool],
        system_prompt="You are a helpful assistant."
    )
    
    result = agent.run_sync("What is the capital of France?")
    
    # Inspect
    params = test_model.last_model_request_parameters
    tools = params.function_tools if params else []
    
    print(f"\n📊 Results:")
    print(f"   Tools registered: {len(tools)}")
    print(f"   System prompt: Generic 'helpful assistant'")
    print(f"   Query: 'What is the capital of France?' (no tool mention)")
    print(f"   Output: {result.output}")
    
    return len(tools) > 0


def run_phase1():
    """Run all Phase 1 tests."""
    print("\n" + "="*70)
    print("PHASE 1: SIMPLE KERNEL - BASELINE TOOL CALLING")
    print("="*70)
    print("\nGoal: Verify basic tool registration and calling behavior")
    print("Tool: simple_tool() - returns greeting")
    
    results = {
        "Test 1 (Basic)": phase1_test1_basic(),
        "Test 2 (Explicit)": phase1_test2_explicit_instruction(),
        "Test 3 (Imperative)": phase1_test3_imperative_instruction(),
        "Test 4 (No instruction)": phase1_test4_no_instruction(),
    }
    
    print("\n" + "="*70)
    print("PHASE 1 SUMMARY")
    print("="*70)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    print(f"\n{'✅ All tests passed!' if all_passed else '❌ Some tests failed'}")
    
    return all_passed


# ==============================================================================
# PHASE 2: TWO-TOOL DISCOVERY PATTERN
# ==============================================================================

# Available options (simulating directory metadata)
AVAILABLE_OPTIONS = ["red", "blue", "green"]


def list_options() -> str:
    """List all available options. Call this FIRST to see what's available."""
    return f"Available options: {', '.join(AVAILABLE_OPTIONS)}"


def select_option(name: str) -> str:
    """Select an option by name. Call list_options() FIRST to see available options."""
    if name.lower() in AVAILABLE_OPTIONS:
        return f"✅ Selected: {name}"
    return f"❌ Error: '{name}' not available. Available: {', '.join(AVAILABLE_OPTIONS)}"


def get_tool_call_order(result) -> list[str]:
    """Extract the order of tool calls from messages."""
    tool_calls = []
    for msg in result.all_messages():
        for part in msg.parts:
            if isinstance(part, ToolCallPart):
                tool_calls.append(part.tool_name)
    return tool_calls


def phase2_test1_explicit_sequence():
    """Test 1: Explicit sequential instruction."""
    print("\n" + "="*70)
    print("PHASE 2 - TEST 1: Explicit Sequential Instruction")
    print("="*70)
    
    test_model = TestModel()
    agent = Agent(
        test_model,
        tools=[list_options, select_option],
        system_prompt=(
            "ALWAYS follow this pattern:\n"
            "1. Call list_options() to see available options\n"
            "2. Then call select_option(name) with your choice"
        )
    )
    
    result = agent.run_sync("Select the blue option")
    
    # Get tool call order
    tool_order = get_tool_call_order(result)
    correct_order = tool_order == ['list_options', 'select_option']
    
    print(f"\n📊 Results:")
    print(f"   Tools registered: 2 (list_options, select_option)")
    print(f"   Tool call order: {' → '.join(tool_order) if tool_order else 'None'}")
    print(f"   Correct sequence: {'✅ YES' if correct_order else '❌ NO'}")
    print(f"   Output: {result.output}")
    
    return correct_order


def phase2_test2_imperative():
    """Test 2: Strong imperative instruction."""
    print("\n" + "="*70)
    print("PHASE 2 - TEST 2: Strong Imperative")
    print("="*70)
    
    test_model = TestModel()
    agent = Agent(
        test_model,
        tools=[list_options, select_option],
        system_prompt=(
            "CRITICAL: You MUST call list_options() BEFORE calling select_option(). "
            "NEVER call select_option() without calling list_options() first. "
            "This order is MANDATORY."
        )
    )
    
    result = agent.run_sync("I want the green one")
    
    tool_order = get_tool_call_order(result)
    correct_order = tool_order == ['list_options', 'select_option']
    
    print(f"\n📊 Results:")
    print(f"   System prompt: 'CRITICAL: MUST call list_options BEFORE select_option'")
    print(f"   Tool call order: {' → '.join(tool_order) if tool_order else 'None'}")
    print(f"   Correct sequence: {'✅ YES' if correct_order else '❌ NO'}")
    print(f"   Output: {result.output}")
    
    return correct_order


def phase2_test3_explanation_based():
    """Test 3: Explanation-based instruction."""
    print("\n" + "="*70)
    print("PHASE 2 - TEST 3: Explanation-Based Instruction")
    print("="*70)
    
    test_model = TestModel()
    agent = Agent(
        test_model,
        tools=[list_options, select_option],
        system_prompt=(
            "To help users select options:\n"
            "- First, call list_options() to discover what options are available\n"
            "- This ensures you make informed decisions\n"
            "- Then use select_option(name) with a valid option name"
        )
    )
    
    result = agent.run_sync("Choose red for me")
    
    tool_order = get_tool_call_order(result)
    correct_order = tool_order == ['list_options', 'select_option']
    
    print(f"\n📊 Results:")
    print(f"   System prompt: Explanation-based (why the order matters)")
    print(f"   Tool call order: {' → '.join(tool_order) if tool_order else 'None'}")
    print(f"   Correct sequence: {'✅ YES' if correct_order else '❌ NO'}")
    print(f"   Output: {result.output}")
    
    return correct_order


def phase2_test4_no_order_specified():
    """Test 4: No order specified - baseline."""
    print("\n" + "="*70)
    print("PHASE 2 - TEST 4: No Order Specified (Baseline)")
    print("="*70)
    
    test_model = TestModel()
    agent = Agent(
        test_model,
        tools=[list_options, select_option],
        system_prompt="You are a helpful assistant with access to option tools."
    )
    
    result = agent.run_sync("Select blue")
    
    tool_order = get_tool_call_order(result)
    # We're not expecting correct order here, just observing
    has_list_first = tool_order and tool_order[0] == 'list_options'
    
    print(f"\n📊 Results:")
    print(f"   System prompt: Generic (no order instruction)")
    print(f"   Tool call order: {' → '.join(tool_order) if tool_order else 'None'}")
    print(f"   Called list_options first: {'✅ YES' if has_list_first else '❌ NO'}")
    print(f"   Output: {result.output}")
    
    # This test always "passes" - we're just observing behavior
    return True


def phase2_test5_wrong_order():
    """Test 5: What happens if LLM calls select_option first?"""
    print("\n" + "="*70)
    print("PHASE 2 - TEST 5: Direct select_option Call")
    print("="*70)
    
    test_model = TestModel(
        # Force TestModel to call select_option directly (simulating bad LLM behavior)
        call_tools=['select_option']
    )
    agent = Agent(
        test_model,
        tools=[list_options, select_option],
        system_prompt="ALWAYS call list_options() first, then select_option()"
    )
    
    result = agent.run_sync("Select purple")  # purple is NOT in available options
    
    tool_order = get_tool_call_order(result)
    
    print(f"\n📊 Results:")
    print(f"   Forced tool call: select_option (skipping list_options)")
    print(f"   Tool call order: {' → '.join(tool_order) if tool_order else 'None'}")
    print(f"   Output: {result.output}")
    print(f"   Note: This simulates LLM ignoring sequential instructions")
    
    # Check if error message is present (purple not available)
    error_present = '❌' in str(result.output) or 'not available' in str(result.output).lower()
    return error_present  # Passes if error is correctly returned


def run_phase2():
    """Run all Phase 2 tests."""
    print("\n" + "="*70)
    print("PHASE 2: TWO-TOOL DISCOVERY PATTERN")
    print("="*70)
    print("\nGoal: Test if LLM follows sequential tool calling instructions")
    print("Tools: list_options() → select_option(name)")
    print("Available options: red, blue, green")
    
    results = {
        "Test 1 (Explicit sequence)": phase2_test1_explicit_sequence(),
        "Test 2 (Imperative)": phase2_test2_imperative(),
        "Test 3 (Explanation)": phase2_test3_explanation_based(),
        "Test 4 (No order)": phase2_test4_no_order_specified(),
        "Test 5 (Wrong order)": phase2_test5_wrong_order(),
    }
    
    print("\n" + "="*70)
    print("PHASE 2 SUMMARY")
    print("="*70)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    # Count how many tests got the correct sequence
    sequence_tests = [results[k] for k in list(results.keys())[:3]]  # First 3 tests check sequence
    correct_sequence_count = sum(sequence_tests)
    
    print(f"\nSequential ordering: {correct_sequence_count}/3 tests followed correct order")
    
    return all(results.values())


# ==============================================================================
# PHASE 2B: REALISTIC MULTI-DIRECTORY SIMULATION
# ==============================================================================

# Directory metadata
DIRECTORY_METADATA = {
    "doctors": {
        "name": "doctors",
        "description": "Medical professionals with specialties and contact info",
        "use_cases": ["Find doctors by specialty", "Get doctor contact information"]
    },
    "departments": {
        "name": "departments",
        "description": "Hospital departments with phone numbers and locations",
        "use_cases": ["Get department phone numbers", "Find department locations"]
    },
    "services": {
        "name": "services",
        "description": "Medical services offered with descriptions and hours",
        "use_cases": ["Learn about available services", "Check service hours"]
    },
    "products": {
        "name": "products",
        "description": "Medical products and equipment with categories",
        "use_cases": ["Find medical products", "Check product availability"]
    },
    "locations": {
        "name": "locations",
        "description": "Building locations with floor information",
        "use_cases": ["Find building locations", "Get floor information"]
    }
}

# Directory data - 10 items per directory
DIRECTORY_DATA = {
    "doctors": [
        {"name": "Dr. Sarah Johnson", "specialty": "Cardiology", "phone": "555-0101"},
        {"name": "Dr. Michael Chen", "specialty": "Neurology", "phone": "555-0102"},
        {"name": "Dr. Emily Rodriguez", "specialty": "Pediatrics", "phone": "555-0103"},
        {"name": "Dr. James Williams", "specialty": "Orthopedics", "phone": "555-0104"},
        {"name": "Dr. Lisa Anderson", "specialty": "Dermatology", "phone": "555-0105"},
        {"name": "Dr. David Kim", "specialty": "Cardiology", "phone": "555-0106"},
        {"name": "Dr. Maria Garcia", "specialty": "Nephrology", "phone": "555-0107"},
        {"name": "Dr. Robert Taylor", "specialty": "Gastroenterology", "phone": "555-0108"},
        {"name": "Dr. Jennifer Lee", "specialty": "Endocrinology", "phone": "555-0109"},
        {"name": "Dr. Thomas Brown", "specialty": "Pulmonology", "phone": "555-0110"}
    ],
    "departments": [
        {"name": "Emergency", "location": "Building A - 1st Floor", "phone": "555-0201"},
        {"name": "Cardiology", "location": "Building A - 3rd Floor", "phone": "555-0202"},
        {"name": "Pediatrics", "location": "Building B - 2nd Floor", "phone": "555-0203"},
        {"name": "Radiology", "location": "Building C - Ground Floor", "phone": "555-0204"},
        {"name": "Laboratory", "location": "Building C - 1st Floor", "phone": "555-0205"},
        {"name": "Surgery", "location": "Building A - 4th Floor", "phone": "555-0206"},
        {"name": "Neurology", "location": "Building B - 3rd Floor", "phone": "555-0207"},
        {"name": "Orthopedics", "location": "Building D - 2nd Floor", "phone": "555-0208"},
        {"name": "Billing", "location": "Building E - 1st Floor", "phone": "555-0209"},
        {"name": "Reception", "location": "Main Entrance", "phone": "555-0210"}
    ],
    "services": [
        {"name": "MRI Scan", "description": "Magnetic resonance imaging", "hours": "Mon-Fri 8am-6pm"},
        {"name": "Blood Work", "description": "Laboratory testing services", "hours": "Mon-Sat 7am-5pm"},
        {"name": "Physical Therapy", "description": "Rehabilitation services", "hours": "Mon-Fri 9am-7pm"},
        {"name": "X-Ray", "description": "Radiological imaging", "hours": "24/7"},
        {"name": "Ultrasound", "description": "Diagnostic ultrasound services", "hours": "Mon-Fri 8am-4pm"},
        {"name": "CT Scan", "description": "Computed tomography imaging", "hours": "24/7"},
        {"name": "EKG", "description": "Electrocardiogram testing", "hours": "Mon-Fri 8am-6pm"},
        {"name": "Vaccination", "description": "Immunization services", "hours": "Mon-Fri 9am-5pm"},
        {"name": "Pharmacy", "description": "Prescription services", "hours": "Mon-Sat 8am-8pm"},
        {"name": "Nutrition Counseling", "description": "Dietary consultation", "hours": "Mon-Thu 10am-4pm"}
    ],
    "products": [
        {"name": "Digital Thermometer", "category": "Diagnostics", "price": "$15.99"},
        {"name": "Blood Pressure Monitor", "category": "Diagnostics", "price": "$45.99"},
        {"name": "Wheelchair", "category": "Mobility", "price": "$299.99"},
        {"name": "Crutches", "category": "Mobility", "price": "$35.99"},
        {"name": "Nebulizer", "category": "Respiratory", "price": "$89.99"},
        {"name": "Pulse Oximeter", "category": "Diagnostics", "price": "$29.99"},
        {"name": "Walking Cane", "category": "Mobility", "price": "$25.99"},
        {"name": "Compression Socks", "category": "Therapeutic", "price": "$19.99"},
        {"name": "Heating Pad", "category": "Therapeutic", "price": "$24.99"},
        {"name": "First Aid Kit", "category": "Emergency", "price": "$39.99"}
    ],
    "locations": [
        {"name": "Main Entrance", "building": "Building A", "floor": "Ground Floor"},
        {"name": "Emergency Room", "building": "Building A", "floor": "1st Floor"},
        {"name": "Cafeteria", "building": "Building B", "floor": "Ground Floor"},
        {"name": "Chapel", "building": "Building C", "floor": "2nd Floor"},
        {"name": "Gift Shop", "building": "Building A", "floor": "Ground Floor"},
        {"name": "Parking Garage", "building": "Parking Structure", "floor": "Multi-level"},
        {"name": "Conference Room", "building": "Building E", "floor": "3rd Floor"},
        {"name": "Library", "building": "Building D", "floor": "2nd Floor"},
        {"name": "Waiting Area", "building": "Building B", "floor": "1st Floor"},
        {"name": "Administrative Offices", "building": "Building E", "floor": "4th Floor"}
    ]
}


def get_directory_list() -> str:
    """Get list of available directories with descriptions and use cases.
    
    Call this FIRST to discover what directories are available before searching."""
    result = {
        "directories": [
            {
                "name": meta["name"],
                "description": meta["description"],
                "use_cases": meta["use_cases"],
                "item_count": len(DIRECTORY_DATA[name])
            }
            for name, meta in DIRECTORY_METADATA.items()
        ]
    }
    return json.dumps(result, indent=2)


def search_directory(directory_name: str, query: str) -> str:
    """Search within a specific directory.
    
    Args:
        directory_name: Name of directory (get from get_directory_list())
        query: Search query (case-insensitive, searches all fields)
    
    Returns:
        JSON with matching items or error message
    """
    # Validate directory exists
    if directory_name not in DIRECTORY_DATA:
        available = ", ".join(DIRECTORY_DATA.keys())
        return json.dumps({
            "error": f"Directory '{directory_name}' not found",
            "available_directories": list(DIRECTORY_DATA.keys())
        })
    
    # Search all fields in items (case-insensitive)
    query_lower = query.lower()
    matches = []
    
    for item in DIRECTORY_DATA[directory_name]:
        # Check if query matches any field value
        if any(query_lower in str(value).lower() for value in item.values()):
            matches.append(item)
    
    if not matches:
        return json.dumps({
            "directory": directory_name,
            "query": query,
            "matches": [],
            "message": f"No matches found for '{query}' in {directory_name}"
        })
    
    return json.dumps({
        "directory": directory_name,
        "query": query,
        "matches": matches,
        "count": len(matches)
    }, indent=2)


def phase2b_test1_discovery_with_realistic_data():
    """Test 1: Discovery pattern with realistic multi-directory data."""
    print("\n" + "="*70)
    print("PHASE 2B - TEST 1: Discovery Pattern with Realistic Data")
    print("="*70)
    
    test_model = TestModel()
    agent = Agent(
        test_model,
        tools=[get_directory_list, search_directory],
        system_prompt=(
            "ALWAYS follow this pattern:\n"
            "1. Call get_directory_list() to see available directories\n"
            "2. Choose appropriate directory based on the query\n"
            "3. Call search_directory(directory_name, query)"
        )
    )
    
    result = agent.run_sync("Find the cardiology department phone number")
    tool_order = get_tool_call_order(result)
    correct_order = tool_order == ['get_directory_list', 'search_directory']
    
    print(f"\n📊 Results:")
    print(f"   Query: 'Find the cardiology department phone number'")
    print(f"   Tool call order: {' → '.join(tool_order) if tool_order else 'None'}")
    print(f"   Correct sequence: {'✅ YES' if correct_order else '❌ NO'}")
    print(f"   Output preview: {str(result.output)[:200]}...")
    
    return correct_order


def phase2b_test2_search_doctors():
    """Test 2: Search across doctors directory."""
    print("\n" + "="*70)
    print("PHASE 2B - TEST 2: Search Doctors by Specialty")
    print("="*70)
    
    test_model = TestModel()
    agent = Agent(
        test_model,
        tools=[get_directory_list, search_directory],
        system_prompt=(
            "First call get_directory_list() to see what's available, "
            "then search the appropriate directory."
        )
    )
    
    result = agent.run_sync("I need a cardiologist")
    tool_order = get_tool_call_order(result)
    correct_order = tool_order == ['get_directory_list', 'search_directory']
    
    print(f"\n📊 Results:")
    print(f"   Query: 'I need a cardiologist'")
    print(f"   Tool call order: {' → '.join(tool_order) if tool_order else 'None'}")
    print(f"   Correct sequence: {'✅ YES' if correct_order else '❌ NO'}")
    
    # Check if found cardiology doctors
    output_str = str(result.output).lower()
    found_cardiology = 'cardiology' in output_str
    print(f"   Found cardiology: {'✅ YES' if found_cardiology else '❌ NO'}")
    
    return correct_order


def phase2b_test3_wrong_directory_name():
    """Test 3: Handling invalid directory name."""
    print("\n" + "="*70)
    print("PHASE 2B - TEST 3: Invalid Directory Handling")
    print("="*70)
    
    test_model = TestModel(
        # Force calling search_directory with wrong name
        call_tools=['search_directory']
    )
    agent = Agent(
        test_model,
        tools=[get_directory_list, search_directory],
        system_prompt="Use the tools to help the user."
    )
    
    result = agent.run_sync("Search for information")
    
    # Check if error is handled
    output_str = str(result.output).lower()
    error_handled = 'error' in output_str or 'not found' in output_str
    
    print(f"\n📊 Results:")
    print(f"   Forced invalid directory call")
    print(f"   Error handled: {'✅ YES' if error_handled else '❌ NO'}")
    print(f"   Output: {result.output}")
    
    return error_handled


def run_phase2b():
    """Run all Phase 2B tests."""
    print("\n" + "="*70)
    print("PHASE 2B: REALISTIC MULTI-DIRECTORY SIMULATION")
    print("="*70)
    print("\nGoal: Test discovery pattern with production-like data")
    print("Directories: doctors, departments, services, products, locations")
    print("Items per directory: 10")
    print("Tools: get_directory_list() → search_directory(name, query)")
    
    results = {
        "Test 1 (Discovery pattern)": phase2b_test1_discovery_with_realistic_data(),
        "Test 2 (Search doctors)": phase2b_test2_search_doctors(),
        "Test 3 (Error handling)": phase2b_test3_wrong_directory_name(),
    }
    
    print("\n" + "="*70)
    print("PHASE 2B SUMMARY")
    print("="*70)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    print(f"\n{'✅ All tests passed!' if all_passed else '❌ Some tests failed'}")
    
    return all_passed


# ==============================================================================
# PHASE 2C: REAL LLM TESTING VIA PYDANTIC AI GATEWAY
# ==============================================================================

async def phase2c_test_with_llm(test_num: int, query: str, expected_directory: str):
    """Test a single query with real LLM."""
    print("\n" + "="*70)
    print(f"PHASE 2C - TEST {test_num}: {expected_directory.upper()} Directory")
    print("="*70)
    
    # Setup model using Pydantic AI Gateway
    # Model string format: gateway/<api_format>:<model_name>
    # For Google Vertex: gateway/google-vertex:gemini-2.5-flash
    model = "gateway/google-vertex:gemini-2.5-flash"
    
    # Get API key from environment
    api_key = os.getenv('PYDANTIC_AI_GATEWAY_API_KEY')
    if not api_key:
        raise ValueError("PYDANTIC_AI_GATEWAY_API_KEY not found in environment")
    
    agent = Agent(
        model,
        tools=[get_directory_list, search_directory],
        system_prompt=(
            "You are a helpful assistant. You have access to tools.\n\n"
            "CRITICAL: ALWAYS follow this pattern:\n"
            "1. Call get_directory_list() FIRST to see what directories are available\n"
            "2. Review the metadata and choose the appropriate directory\n"
            "3. Call search_directory(directory_name, query) with the chosen directory\n\n"
            "DO NOT skip step 1. You MUST call get_directory_list() before search_directory()."
        )
    )
    
    print(f"\n📝 INPUT PROMPT:")
    print(f"   \"{query}\"")
    
    # Run query
    result = await agent.run(query)
    
    # Extract tool calls
    tool_order = get_tool_call_order(result)
    
    print(f"\n🔧 TOOLS CALLED:")
    if tool_order:
        for i, tool in enumerate(tool_order, 1):
            print(f"   {i}. {tool}()")
    else:
        print("   ❌ No tools called")
    
    # Check if correct pattern followed
    correct_pattern = tool_order == ['get_directory_list', 'search_directory']
    pattern_status = "✅ CORRECT" if correct_pattern else "❌ WRONG"
    print(f"\n   Discovery pattern: {pattern_status}")
    if not correct_pattern:
        print(f"   Expected: get_directory_list → search_directory")
        print(f"   Got: {' → '.join(tool_order) if tool_order else 'None'}")
    
    # Get the actual response
    response_text = result.output if hasattr(result, 'output') else str(result)
    
    print(f"\n💬 LLM RESPONSE:")
    print(f"   {response_text[:300]}{'...' if len(response_text) > 300 else ''}")
    
    # Check if expected directory was used
    directory_used = None
    for msg in result.all_messages():
        for part in msg.parts:
            if isinstance(part, ToolCallPart) and part.tool_name == 'search_directory':
                # Extract directory name from args
                if hasattr(part, 'args') and 'directory_name' in part.args:
                    directory_used = part.args['directory_name']
                    break
    
    if directory_used:
        directory_correct = directory_used == expected_directory
        directory_status = "✅ CORRECT" if directory_correct else "❌ WRONG"
        print(f"\n   Directory selected: {directory_used} {directory_status}")
        if not directory_correct:
            print(f"   Expected: {expected_directory}")
    
    return correct_pattern


async def run_phase2c():
    """Run all Phase 2C tests with real LLM."""
    print("\n" + "="*70)
    print("PHASE 2C: REAL LLM TESTING VIA PYDANTIC AI GATEWAY")
    print("="*70)
    print("\nModel: gateway/google-vertex:gemini-2.5-flash")
    print("Goal: Test if real LLM follows discovery pattern with realistic data")
    print("\nNote: This will make actual API calls via Pydantic AI Gateway")
    
    # Check for API key
    api_key = os.getenv('PYDANTIC_AI_GATEWAY_API_KEY')
    if not api_key:
        print("\n❌ ERROR: PYDANTIC_AI_GATEWAY_API_KEY not found in environment")
        print("   Please set your Pydantic AI Gateway API key to run Phase 2C")
        return False
    
    print(f"✅ API key found: {api_key[:10]}...")
    
    # Define test cases - one for each directory
    test_cases = [
        (1, "I need to find a cardiologist", "doctors"),
        (2, "What's the phone number for the emergency department?", "departments"),
        (3, "What are the hours for the pharmacy?", "services"),
        (4, "Do you have blood pressure monitors?", "products"),
        (5, "Where is the cafeteria located?", "locations"),
    ]
    
    results = {}
    
    for test_num, query, expected_dir in test_cases:
        try:
            passed = await phase2c_test_with_llm(test_num, query, expected_dir)
            results[f"Test {test_num} ({expected_dir})"] = passed
        except Exception as e:
            print(f"\n❌ ERROR in test {test_num}: {e}")
            results[f"Test {test_num} ({expected_dir})"] = False
    
    print("\n" + "="*70)
    print("PHASE 2C SUMMARY")
    print("="*70)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    correct_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n{'✅' if all_passed else '⚠️'} Discovery pattern followed: {correct_count}/{total_count} tests")
    
    if not all_passed:
        print("\n⚠️  Real LLM (Gemini 2.5 Flash) does NOT consistently follow discovery pattern")
        print("   → Proceed to Phase 3 (programmatic enforcement)")
    else:
        print("\n✅ Real LLM successfully follows discovery pattern!")
    
    return all_passed


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        phase = sys.argv[1]
        
        if phase == '1':
            success = run_phase1()
        elif phase == '2' or phase == '2a':
            success = run_phase2()
        elif phase == '2b':
            success = run_phase2b()
        elif phase == '2c':
            success = asyncio.run(run_phase2c())
        elif phase == 'all':
            success1 = run_phase1()
            success2 = run_phase2()
            success2b = run_phase2b()
            success2c = asyncio.run(run_phase2c())
            success = success1 and success2 and success2b and success2c
        else:
            print(f"Unknown phase: {phase}")
            print("Usage: python tool_calling.py [1|2|2a|2b|2c|all]")
            exit(1)
    else:
        # Default: Run Phase 1 only
        success = run_phase1()
    
    exit(0 if success else 1)

