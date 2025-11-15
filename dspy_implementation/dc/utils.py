"""
Utility functions for Dynamic Cheatsheet integration
Includes extractors and code execution utilities
"""

def extract_answer(response: str) -> str:
    """
    Extracts the final answer from the model response.
    Supports both <answer> tags and FINAL ANSWER format.

    Arguments:
        response : str : The response from the model.

    Returns:
        str : The extracted final answer (if not found, returns "No final answer found").
    """
    if "<answer>" in response:
        # <answer> (content) </answer>
        try:
            txt = response.split("<answer>")[-1].strip()
            txt = txt.split("</answer>")[0].strip()
            return txt
        except:
            return "No final answer found"
    else:
        if not("FINAL ANSWER" in response):
            return "No final answer found"
        try:
            response = response.split("FINAL ANSWER")[-1].strip()
            if response[0] == ":":
                response = response[1:].strip()

            # First decide whether to split by "```" or "'''" based on the presence of "```" or "'''"
            idx_1 = response.find("'''")
            idx_2 = response.find("```")
            if min(idx_1, idx_2) != -1: 
                if idx_1 < idx_2:
                    response = response.split("'''")[1].strip()
                else:
                    response = response.split("```")[1].strip()
            else:
                if idx_1 == -1:
                    response = response.split("```")[1].strip()
                else:
                    response = response.split("'''")[1].strip()

            # Special case: If the first line contains "python" then remove it
            if response.split("\n")[0].strip().lower() == "python":
                response = "\n".join(response.split("\n")[1:]).strip()
            return response
        except:
            return "No final answer found"


def extract_cheatsheet(response: str, old_cheatsheet: str) -> str:
    """
    Extracts the cheatsheet from the model response.
    
    Arguments:
        response : str : The response from the model.
        old_cheatsheet : str : The old cheatsheet to return if the new one is not found.

    Returns:
        str : The extracted cheatsheet (if not found, returns the old cheatsheet).
    """
    response = response.strip()
    # <cheatsheet> (content) </cheatsheet>
    if "<cheatsheet>" in response:
        try:
            txt = response.split("<cheatsheet>")[1].strip()
            txt = txt.split("</cheatsheet>")[0].strip()
            return txt
        except:
            return old_cheatsheet
    else:
        return old_cheatsheet


def extract_and_run_python_code(txt: str) -> str:
    """
    Extract and execute Python code from a provided string.
    Handles missing print statements for non-comment last lines,
    executes the code, and captures output or errors.

    Parameters:
        txt (str): Input string containing a possible Python code block.

    Returns:
        str: Execution result or error message wrapped in output formatting.
    """
    import os
    import tempfile
    from subprocess import Popen, PIPE, TimeoutExpired
    
    def extract_code(input_str: str) -> str:
        """Extract Python code block delimited by ```python and ```."""
        try:
            return input_str.split("```python", 1)[1].split("```", 1)[0].strip()
        except IndexError:
            raise ValueError("No valid Python code block found.")

    def ensure_print_statement(code: str) -> str:
        """
        Append a print statement if the last line isn't a comment or a print statement.
        """
        lines = code.splitlines()
        last_line = lines[-1].rstrip()
        if not last_line.startswith(("print(", "#", " ", "\t")) and (not ("return" in last_line)):
            lines[-1] = f"print({last_line})"
        return "\n".join(lines)

    if "```python" not in txt:
        return None  # Return early if no Python code block is present

    try:
        # Extract and sanitize the code
        code_block = extract_code(txt)
        code_with_print = ensure_print_statement(code_block)

        # Execute the code and return output
        python_output = execute_code_with_timeout(code_with_print)
        return f"Output of the Python code above:\n```\n{python_output}\n```"

    except Exception as error:
        return f"PYTHON CODE OUTPUT:\n```\nError: {str(error)}\n```"


def execute_code_with_timeout(code: str, timeout: int = 3) -> str:
    """
    Execute Python code with a timeout and return the output.
    
    Parameters:
        code (str): Python code to execute.
        timeout (int): Timeout duration in seconds.

    Returns:
        str: Captured output or error message from the code execution.
    """
    import os
    import tempfile
    from subprocess import Popen, PIPE, TimeoutExpired
    
    with tempfile.NamedTemporaryFile(
        mode="w+t", suffix=".py", delete=False
    ) as temp_file:
        temp_file.write(code)
        temp_file.flush()

    try:
        # In case alias python=python3 is not set, use python3 instead of python
        process = Popen(["python3", temp_file.name], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate(timeout=timeout)
        captured_output = stdout.decode().strip()
        error_output = stderr.decode().strip()

        if captured_output == "":
            if error_output != "":
                captured_output = f"Error in execution: {error_output}"
            else:
                captured_output = "(No output was generated. It is possible that you did not include a print statement in your code. If you want to see the output, please include a print statement.)"

    except TimeoutExpired:
        process.kill()
        captured_output = "Execution took too long, aborting..."

    finally:
        os.remove(temp_file.name)

    return captured_output

