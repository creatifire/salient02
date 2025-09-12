import os
import asyncio
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from dotenv import load_dotenv

# Load environment variables from .env file at project root
from pathlib import Path
backend_dir = Path(__file__).parent.parent.parent
load_dotenv(backend_dir.parent / ".env")

# --- Installation Notes ---
# You need to install the required libraries.
# pip install "pydantic-ai-slim[openai]" pydantic

# --- Pydantic Models for Data Retrieval ---
# We define Pydantic models to represent the structured data we expect to get back.
# The `UsageData` model corresponds to the `usage` field in the OpenRouter API response.
class UsageData(BaseModel):
    """
    Model for the usage statistics of an API call.
    """
    completion_tokens: int = Field(..., description="Number of tokens generated in the completion.")
    prompt_tokens: int = Field(..., description="Number of tokens in the user's prompt.")
    total_tokens: int = Field(..., description="Total number of tokens used (prompt + completion).")

# We create a final model that encapsulates the response, including the usage data.
class AgentResponse(BaseModel):
    """
    Model for the overall agent response, including the generated content and usage data.
    """
    output: str = Field(..., description="The generated text content from the LLM.")
    usage: UsageData = Field(..., description="The token usage data for the request.")

# --- Main Logic ---
async def retrieve_cost_data(prompt: str, model_name: str) -> Optional[AgentResponse]:
    """
    Uses pydantic-ai to make a request to the OpenRouter API and retrieves the cost data.
    
    Args:
        prompt: The user's prompt to send to the LLM.
        model_name: The name of the OpenRouter model to use (e.g., "mistralai/mistral-7b-instruct").

    Returns:
        An AgentResponse object containing the generated output and usage data, or None if an error occurs.
    """
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        print("Error: OPENROUTER_API_KEY environment variable is not set.")
        return None

    # The Agent is configured to use the OpenAI API interface, which OpenRouter is compatible with.
    # The `base_url` is set to OpenRouter's API endpoint.
    agent = Agent(
        model=model_name,
        output_type=AgentResponse,
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_api_key
    )

    try:
        # Run the agent with a prompt. The output will be automatically validated against
        # the `AgentResponse` Pydantic model.
        # This will return a `RunResult` object which contains the `output`.
        result = await agent.run(prompt=prompt)
        
        # The `result.output` is the validated `AgentResponse` object.
        return result.output

    except Exception as e:
        print(f"An error occurred: {e}")
        # In a real application, you might want to handle this more gracefully.
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
        # The API response contains the `usage` field with token counts.
        # We can directly access this data because `pydantic-ai` has validated it for us.
        print("Successfully retrieved data!")
        print(f"Generated Message: {response_data.output}")
        print("\n--- Cost and Usage Data ---")
        print(f"Model: {model}")
        print(f"Prompt Tokens: {response_data.usage.prompt_tokens}")
        print(f"Completion Tokens: {response_data.usage.completion_tokens}")
        print(f"Total Tokens: {response_data.usage.total_tokens}")
        
        # OpenRouter provides token pricing, but it's not in the API response payload.
        # You'd typically fetch this from their models API or a known pricing table.
        # For this example, we'll use a placeholder for calculation.
        input_cost_per_million = 0.6  # Placeholder example cost
        output_cost_per_million = 0.6 # Placeholder example cost
        
        calculated_cost = (
            (response_data.usage.prompt_tokens / 1_000_000) * input_cost_per_million +
            (response_data.usage.completion_tokens / 1_000_000) * output_cost_per_million
        )
        
        print(f"Estimated Cost (based on placeholder rates): ${calculated_cost:.6f}")
    else:
        print("Failed to retrieve data.")

if __name__ == "__main__":
    asyncio.run(main())
