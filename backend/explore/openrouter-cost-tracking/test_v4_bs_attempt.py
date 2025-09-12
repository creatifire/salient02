import os
import asyncio
from typing import Optional, Any
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file at project root
backend_dir = Path(__file__).parent.parent.parent
load_dotenv(backend_dir.parent / ".env")

# --- Installation Notes ---
# You need to install the required libraries.
# pip install "pydantic-ai-slim[openai]" pydantic

# --- Pydantic Models for Data Retrieval ---
# We define a Pydantic model to represent the structured data we expect back from the agent.
# This model will not include 'cost', as pydantic-ai does not automatically parse it.
class AgentResponse(BaseModel):
    """
    Model for the overall agent response, containing only the generated content.
    """
    output: str = Field(..., description="The generated text content from the LLM.")

# --- Main Logic ---
async def retrieve_cost_data(prompt: str, model_name: str) -> Optional[tuple[str, dict[str, Any]]]:
    """
    Uses pydantic-ai to make a request to the OpenRouter API and retrieves the cost data.
    
    Args:
        prompt: The user's prompt to send to the LLM.
        model_name: The name of the OpenRouter model to use (e.g., "mistralai/mixtral-8x7b-instruct-v0.1").

    Returns:
        A tuple containing the generated output and the raw usage data dictionary, or None if an error occurs.
    """
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        print("Error: OPENROUTER_API_KEY environment variable is not set.")
        return None
    
    # OpenRouter uses an OpenAI-compatible API. We instantiate OpenAIChatModel
    # and pass the OpenRouter-specific `base_url` and `api_key`.
    # Crucially, we use the `extra_body` parameter to explicitly request usage data.
    provider = OpenAIProvider(
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_api_key
    )
    model_instance = OpenAIChatModel(
        model_name=model_name,
        provider=provider
    )

    # The Agent is configured with our custom model and the Pydantic output type.
    agent = Agent(
        model=model_instance,
        output_type=AgentResponse,
    )

    try:
        # Run the agent with a prompt. The result is the run result object.
        result = await agent.run(prompt)
        
        print("🔍 DEBUG: Examining result structure...")
        print(f"   Result type: {type(result)}")
        print(f"   Has all_messages: {hasattr(result, 'all_messages')}")
        
        # Access the raw message history to get the full API response.
        # The last message in the history contains the final API response.
        messages = result.all_messages()
        print(f"   Message count: {len(messages)}")
        print(f"   Last message type: {type(messages[-1])}")
        print(f"   Last message has data: {hasattr(messages[-1], 'data')}")
        
        if hasattr(messages[-1], 'data'):
            raw_response = messages[-1].data
            print(f"   Raw response keys: {list(raw_response.keys()) if isinstance(raw_response, dict) else 'Not a dict'}")
        else:
            # Try different approaches to access raw data
            raw_response = {}
            print(f"   Trying to access raw data differently...")
        
        # The 'usage' data, including the 'cost', is located here.
        usage_data = raw_response.get("usage", {})
        print(f"   Usage data: {usage_data}")
        
        # The generated output is validated by the Pydantic model.
        generated_output = result.output.output

        return (generated_output, usage_data)

    except Exception as e:
        print(f"An error occurred: {e}")
        print(f"Exception type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None

async def main():
    """
    Main function to run the cost data retrieval example.
    """
    model = "deepseek/deepseek-chat-v3.1"
    my_prompt = "Generate a short, friendly message about the importance of being on time."

    print(f"Attempting to retrieve cost data for model: '{model}'")
    print("-" * 50)

    # Call the async function to get the data
    response_data = await retrieve_cost_data(prompt=my_prompt, model_name=model)

    if response_data:
        generated_message, usage_data = response_data
        
        # We can now access the raw usage data directly.
        prompt_tokens = usage_data.get("prompt_tokens", 0)
        completion_tokens = usage_data.get("completion_tokens", 0)
        total_tokens = usage_data.get("total_tokens", 0)
        actual_cost = usage_data.get("cost")
        
        print("Successfully retrieved data!")
        print(f"Generated Message: {generated_message}")
        print("\n--- Cost and Usage Data ---")
        print(f"Model: {model}")
        print(f"Prompt Tokens: {prompt_tokens}")
        print(f"Completion Tokens: {completion_tokens}")
        print(f"Total Tokens: {total_tokens}")
        
        if actual_cost is not None:
            print(f"Actual Cost: ${actual_cost:.6f}")
        else:
            print("Note: Actual cost data was not found in the API response.")

    else:
        print("Failed to retrieve data.")

if __name__ == "__main__":
    asyncio.run(main())
