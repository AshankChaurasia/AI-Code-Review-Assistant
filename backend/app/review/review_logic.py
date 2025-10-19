import subprocess
import tempfile
import os
import sys
import logging

logger = logging.getLogger(__name__)

def run_flake8(code: str) -> str:
    """Run flake8 static analysis on the provided Python code string."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as temp_file:
        temp_file.write(code)
        temp_path = temp_file.name

    try:
        cmd = [sys.executable, "-m", "flake8", temp_path, "--max-line-length=120"]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0 and not result.stdout.strip():
            stderr = result.stderr.strip()
            if "ModuleNotFoundError" in stderr or "No module named 'flake8'" in stderr:
                return "Flake8 is not installed. Run: pip install flake8"
        
        return result.stdout.strip() or "No issues found."
    
    except subprocess.TimeoutExpired:
        return "Analysis timed out. Try a smaller file."
    except Exception as e:
        logger.error(f"Error running flake8: {e}", exc_info=True)
        return f"Error running static analysis: {str(e)}"
    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass