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


async def read_github_repository(repo_url: str) -> dict:
    """
    Clones a public GitHub repository and reads the content of all its files.
    Returns the temporary directory path where the repository was cloned, along with file contents.

    Args:
        repo_url: The full URL of the GitHub repository to clone.

    Returns:
        A dictionary with keys 'file_contents' (dictionary of file paths and contents) and 'temp_dir' (path to the temporary directory),
        or an error message.
    """
    print(f"Debug: read_github_repository received URL: {repo_url}") # Debug print
    # Validate the GitHub URL - more flexible regex
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
            # Clean up on clone failure
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return {"error": f"Failed to clone repository. Error: {stderr.decode()}"}

        # Read the files from the cloned repository
        file_contents = read_directory_files(temp_dir)
        return {"file_contents": file_contents, "temp_dir": temp_dir}

    except Exception as e:
        # Clean up on unexpected error
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return {"error": f"An unexpected error occurred: {e}"}
            

def cleanup_temp_directory(directory_path: str) -> dict:
    """
    Removes a temporary directory and its contents.

    Args:
        directory_path: The path to the temporary directory to remove.

    Returns:
        A dictionary indicating success or an error message.
    """
    if not os.path.isdir(directory_path):
        return {"error": f"Error: Directory not found at {directory_path}"}
    try:
        shutil.rmtree(directory_path)
        return {"success": f"Successfully removed directory: {directory_path}"}
    except Exception as e:
        return {"error": f"Error removing directory {directory_path}: {e}"}


async def get_linting_score(file_path: str) -> dict:
    """
    Runs pylint on a given Python file and returns its linting score.

    Args:
        file_path: The path to the Python file to lint.

    Returns:
        A dictionary containing the linting score as a float and any errors,
        or an error message if the file is not found or pylint fails.
    """
    if not os.path.exists(file_path):
        return {"error": f"Error: File not found at {file_path}"}
    if not file_path.endswith('.py'):
        return {"error": "Error: Not a Python file."}

    try:
        # Run pylint as a subprocess with the absolute file path
        absolute_file_path = os.path.abspath(file_path)
        command = f"pylint {absolute_file_path}"
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        pylint_output = stdout.decode()
        pylint_error = stderr.decode()

        if process.returncode != 0 and "No such file or directory" in pylint_error:
             return {"error": "Pylint is not installed or not found. Please install it using 'pip install pylint'."}
        elif process.returncode != 0 and pylint_error:
             return {"error": f"Pylint encountered an error: {pylint_error}"}

        # Extract the score using a regular expression
        match = re.search(r"Your code has been rated at ([-+]?\d*\.\d+|\d+)/10", pylint_output)
        if match:
            score_out_of_10 = float(match.group(1))
            percentage_score = score_out_of_10 * 10  # Convert to percentage
            return {"linting_score": percentage_score}
        else:
            # If pylint runs but doesn't output a score (e.g., empty file, only errors, no code)
            return {"linting_score": 0.0, "message": "Pylint ran, but no score could be extracted. Check output for details.", "pylint_output": pylint_output}

    except Exception as e:
        return {"error": f"An unexpected error occurred during linting: {e}"}
    