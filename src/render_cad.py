"""CAD rendering utilities for generating STL files and PNG views."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_stl(script_path: Path, output_path: Path) -> bool:
    """
    Generate STL file from CAD-Query script.

    Args:
        script_path: Path to the CAD-Query Python script
        output_path: Path where STL file should be saved

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Use cq-cli to convert CAD-Query script to STL
        import subprocess
        result = subprocess.run([
            "cq-cli", 
            "--codec", "stl",
            "--infile", str(script_path),
            "--outfile", str(output_path),
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.info(f"STL generated successfully: {output_path}")
            return True
        else:
            logger.error(f"cq-cli execution failed: {result.stderr}")
            logger.error(f"cq-cli stdout: {result.stdout}")
            return False

    except Exception as e:
        logger.error(f"Failed to generate STL: {e}. If the error is a timeout, most likely the \
        geometry is invalid. ")
        return False

