import os
import asyncio
from typing import Optional
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
# We define Pydantic models to represent the structured data we expect to get back.
# The `UsageData` model corresponds to the `usage` field in the OpenRouter API response.
class UsageData(BaseModel):
    """
    Model for the usage statistics of an API call.
    """
    completion_tokens: int = Field(..., description="Number of tokens generated in the completion.")
    prompt_tokens: int = Field(..., description="Number of tokens in the user's prompt.")
    total_tokens: int = Field(..., description="Total number of tokens used (prompt + completion).")
    cost: Optional[float] = Field(None, description="The monetary cost of the request in credits.")

# We create a final model that encapsulates the response, including the generated content and usage data.
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
        model_name: The name of the OpenRouter model to use (e.g., "mistralai/mixtral-8x7b-instruct-v0.1").

    Returns:
        An AgentResponse object containing the generated output and usage data, or None if an error occurs.
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
        output_type=AgentResponse,
    )

    try:
        # Run the agent with a prompt. The output will be automatically validated against
        # the `AgentResponse` Pydantic model, which now expects the `usage` data.
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
        
        # OpenRouter's API provides the actual cost in the 'cost' field of the usage object.
        if response_data.usage.cost is not None:
            print(f"Actual Cost: ${response_data.usage.cost:.6f}")
        else:
            print("Note: Actual cost data was not returned in the API response.")

    else:
        print("Failed to retrieve data.")

if __name__ == "__main__":
    asyncio.run(main())
