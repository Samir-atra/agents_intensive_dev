import os
import re
import shutil
import tempfile
import asyncio

def read_file(file_path: str) -> str:
    """
    Reads the content of a file.

    Args:
        file_path: The path to the file.

    Returns:
        The content of the file as a string.
    """
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def read_directory_files(directory_path: str) -> dict[str, str]:
    """
    Reads the content of all files in a directory and its subdirectories.

    Args:
        directory_path: The path to the directory.

    Returns:
        A dictionary where keys are file paths and values are file contents.
    """
    if not os.path.isdir(directory_path):
        return {"error": f"Error: Directory not found at {directory_path}"}
    
    file_contents = {}
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            # Skip .git directory files
            if '.git' in file_path.split(os.sep):
                continue
            file_contents[file_path] = read_file(file_path)
            
    return file_contents

async def read_github_repository(repo_url: str) -> dict[str, str]:
    """
    Clones a public GitHub repository and reads the content of all its files.

    Args:
        repo_url: The full URL of the GitHub repository to clone.

    Returns:
        A dictionary where keys are file paths and values are their contents,
        or an error message.
    """
    # Validate the GitHub URL
    if not re.match(r"https://github\.com/([^/]+)/([^/]+)", repo_url):
        return {"error": "Invalid GitHub repository URL provided."}

    temp_dir = tempfile.mkdtemp()
    try:
        # Construct the git clone command
        command = f"git clone --depth 1 {repo_url} ."
        
        # Execute the command in the temporary directory
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=temp_dir
        )
        
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            return {"error": f"Failed to clone repository. Error: {stderr.decode()}"}

        # Read the files from the cloned repository
        return read_directory_files(temp_dir)

    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}
    finally:
        # Clean up the temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)