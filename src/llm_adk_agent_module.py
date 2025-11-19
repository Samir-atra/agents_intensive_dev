
import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPServerParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
import asyncio
from file_reader_tool import read_file, read_directory_files, read_github_repository, get_linting_score, cleanup_temp_directory


async def initialize_adk_model():
    """Initializes the Google ADK LLM agent with Gemini model."""
    load_dotenv()  # Load environment variables from .env file
    api_key = os.getenv("GOOGLE_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")
    os.environ["GOOGLE_API_KEY"] = api_key  # This keeps the compatibility with how ADK might expect the API key internally
    os.environ["GITHUB_TOKEN"] = github_token
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable not set.")

    # Assuming Gemini model can be initialized directly with an API key or it's handled internally by ADK
    # Based on the notebook, it seems the API key is set as an environment variable.
    agent = LlmAgent(
        name="helpful_assistant",
        model="gemini-2.5-flash",  # Changed to gemini-1.5-pro as it's more robust, user can change to flash-lite if preferred.
        description="An agent specialized in code style assessment.",
        instruction="""You are an expert code style assessor. Your task is to provide a structured code style assessment for the provided code or repository.

            **If a GitHub repository URL is provided:**
            1.  Use `read_github_repository` to clone the repository. This will give you `file_contents` (a dictionary of file paths and their content) and `temp_dir` (the path to the temporary directory where the repo was cloned).
            2.  For any Python files within `file_contents`, use `get_linting_score` on their *absolute paths* (e.g., `os.path.join(temp_dir, relative_file_path)`).
            3.  After completing the assessment, always call `cleanup_temp_directory(temp_dir)` to remove the cloned repository.

            **For any code input (file or directory):**
            Evaluate the code based on:
                -   **Readability:** Descriptive naming, consistent formatting, comments.
                -   **Maintainability & Organization:** Structure, modularity, large functions, duplication.
                -   **Python Linting (if applicable):** Use `get_linting_score` for Python files.
                -   **Repository Best Practices (if applicable):** Presence of `README.md`, `.gitignore`, `requirements.txt`, etc.

            Provide a concise analysis (2-3 sentences) and a percentage score (0-100%) for each aspect. Conclude with an overall code style score (0-100%). Present your assessment in clear Markdown with dedicated sections 
            for each point and the final overall score. **Do not output raw file contents.
            """,

        tools=[
            FunctionTool(read_file),
            FunctionTool(read_directory_files),
            FunctionTool(read_github_repository),
            FunctionTool(get_linting_score),
            FunctionTool(cleanup_temp_directory),
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
        # response_text = await generate_adk_response(
        #     "Tell me a very short story about a brave knight."
        # )
        # print(response_text)

        response_text = await generate_adk_response(
            "Please provide a code style assessment for the repository at: https://github.com/Samir-atra/MCP_server"
        )
        # print(response_text)

    except ValueError as e:
        print(f"Error: {e}")
        print("Please set the GEMINI_API_KEY environment variable.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
