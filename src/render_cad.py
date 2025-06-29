"""CAD rendering utilities for generating STL files and PNG views."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_stl(script_path: Path, output_path: Path) -> tuple[bool, str]:
    """
    Generate STL file from CAD-Query script.

    Args:
        script_path: Path to the CAD-Query Python script
        output_path: Path where STL file should be saved

    Returns:
        tuple: (success: bool, error_message: str)
    """
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Use cq-cli to convert CAD-Query script to STL
        import subprocess
        result = subprocess.run([
            "/Users/rishigundakaram/.pyenv/shims/uv",
            "run", "-m", "cq_cli.main",
            "--codec", "stl",
            "--infile", str(script_path),
            "--outfile", str(output_path),
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.info(f"STL generated successfully: {output_path}")
            return True, ""
        else:
            error_msg = f"CadQuery compilation failed:\n{result.stderr}\n{result.stdout}".strip()
            logger.error(f"cq-cli execution failed: {result.stderr}")
            logger.error(f"cq-cli stdout: {result.stdout}")
            return False, error_msg

    except Exception as e:
        error_msg = f"Failed to generate STL: {e}. If the error is a timeout, most likely the geometry is invalid."
        logger.error(error_msg)
        return False, error_msg

