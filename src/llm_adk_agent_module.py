
import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPServerParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
import asyncio
from file_reader_tool import read_file, read_directory_files, read_github_repository


async def initialize_adk_model():
    """Initializes the Google ADK LLM agent with Gemini model."""
    load_dotenv()  # Load environment variables from .env file
    api_key = os.getenv("GEMINI_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")
    os.environ["GOOGLE_API_KEY"] = api_key  # This keeps the compatibility with how ADK might expect the API key internally
    os.environ["GITHUB_TOKEN"] = github_token
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")

    # Assuming Gemini model can be initialized directly with an API key or it's handled internally by ADK
    # Based on the notebook, it seems the API key is set as an environment variable.
    agent = LlmAgent(
        name="helpful_assistant",
        model="gemini-2.5-flash",  # Changed to gemini-1.5-pro as it's more robust, user can change to flash-lite if preferred.
        description="A simple agent that can answer general questions.",
        instruction="You are a helpful assistant. Use Google Search for current info or if unsure.",
        tools=[
            FunctionTool(read_file),
            FunctionTool(read_directory_files),
            FunctionTool(read_github_repository),
        ],
    )
    return agent


async def generate_adk_response(prompt: str) -> str:
    """
    Generates a response from the Google ADK LLM agent based on the given prompt.

    Args:
        prompt: The input prompt for the model.

    Returns:
        The generated text response.
    """
    agent = await initialize_adk_model()
    runner = InMemoryRunner(agent=agent)
    response = await runner.run_debug(prompt)
    return response  # Assuming the output is directly accessible via .output


async def main():
    # Example usage:
    print("Initializing Google ADK LLM agent...")
    try:
        # Ensure GEMINI_API_KEY is set in your environment variables
        # For example: export GEMINI_API_KEY="YOUR_API_KEY"
        response_text = await generate_adk_response(
            "Tell me a very short story about a brave knight."
        )
        # print(response_text)

        response_text = await generate_adk_response(
            "what are the contents of the files in the repository at: https://github.com/fabiodrbarros/awesome-SOTA-FER"
        )
        # print(response_text)

    except ValueError as e:
        print(f"Error: {e}")
        print("Please set the GEMINI_API_KEY environment variable.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
