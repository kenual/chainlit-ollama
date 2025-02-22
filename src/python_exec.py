import io
import sys


def execute_python_code(code: str) -> str:
    # Create a string buffer to capture output
    captured_output = io.StringIO()

    # Save the original standard output
    original_stdout = sys.stdout

    try:
        # Redirect standard output to the captured output
        sys.stdout = captured_output

        # Execute the code
        exec(code)

    except Exception as e:
        # If any exception occurs, capture it as output
        return f"Error: {str(e)}"
    finally:
        # Restore the original standard output
        sys.stdout = original_stdout

    # Return the captured output
    return captured_output.getvalue()
