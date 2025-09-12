import os
import asyncio
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent, AgentRunResult, RunUsage
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
# We define a Pydantic model for the output content.
# The usage data will be accessed separately from the result object.
class AgentOutput(BaseModel):
    """
    Model for the generated content from the LLM.
    """
    output: str = Field(..., description="The generated text content from the LLM.")

# --- Main Logic ---
async def retrieve_cost_data(prompt: str, model_name: str) -> Optional[tuple[str, RunUsage]]:
    """
    Uses pydantic-ai to make a request to the OpenRouter API and retrieves the cost data.
    
    Args:
        prompt: The user's prompt to send to the LLM.
        model_name: The name of the OpenRouter model to use (e.g., "mistralai/mixtral-8x7b-instruct-v0.1").

    Returns:
        A tuple containing the generated output string and the RunUsage object, or None if an error occurs.
    """
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        print("Error: OPENROUTER_API_KEY environment variable is not set.")
        return None
    
    # OpenRouter uses an OpenAI-compatible API. We instantiate OpenAIChatModel
    # and pass the OpenRouter-specific `base_url` and `api_key`.
    # Crucially, we use the `extra_body` parameter to explicitly request usage data.
    model_instance = OpenAIChatModel(
        model=model_name,
        provider=OpenAIProvider(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key
        ),
        extra_body={
            "usage": {
                "include": True
            }
        }
    )

    # The Agent is configured with our custom model and the Pydantic output type.
    agent = Agent(
        model=model_instance,
        output_type=AgentOutput,
    )

    try:
        # Run the agent with a prompt. The result is the `AgentRunResult` object.
        result: AgentRunResult[AgentOutput] = await agent.run(prompt=prompt)
        
        # The generated output is accessed from the validated output property.
        generated_output = result.output.output
        
        # The usage data is accessed directly from the `usage` attribute of the result object.
        usage_data = result.usage
        
        return (generated_output, usage_data)

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

async def main():
    """
    Main function to run the cost data retrieval example.
    """
    model = "mistralai/mixtral-8x7b-instruct-v0.1"
    my_prompt = "Generate a short, friendly message about the importance of being on time."

    print(f"Attempting to retrieve cost data for model: '{model}'")
    print("-" * 50)

    # Call the async function to get the data
    response_data = await retrieve_cost_data(prompt=my_prompt, model_name=model)

    if response_data:
        generated_message, usage_data = response_data
        
        # The RunUsage object contains the token and cost information.
        # We access the 'details' dictionary to get the 'cost' field,
        # which OpenRouter provides.
        actual_cost = usage_data.details.get("cost")
        
        print("Successfully retrieved data!")
        print(f"Generated Message: {generated_message}")
        print("\n--- Cost and Usage Data ---")
        print(f"Model: {model}")
        print(f"Prompt Tokens: {usage_data.input_tokens}")
        print(f"Completion Tokens: {usage_data.output_tokens}")
        print(f"Total Tokens: {usage_data.total_tokens}")
        
        if actual_cost is not None:
            print(f"Actual Cost: ${actual_cost:.6f}")
        else:
            print("Note: Actual cost data was not found in the API response details.")

    else:
        print("Failed to retrieve data.")

if __name__ == "__main__":
    asyncio.run(main())
