"""SVG to PNG conversion utilities."""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def convert_svg_to_png_cairosvg(svg_path: Path, png_path: Path, width: int = 800, height: int = 600) -> bool:
    """
    Convert SVG to PNG using cairosvg library.
    
    Args:
        svg_path: Path to input SVG file
        png_path: Path to output PNG file
        width: Output width in pixels
        height: Output height in pixels
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import cairosvg
        
        cairosvg.svg2png(
            url=str(svg_path),
            write_to=str(png_path),
            output_width=width,
            output_height=height
        )
        
        logger.info(f"Converted SVG to PNG: {svg_path} -> {png_path}")
        return True
        
    except ImportError:
        logger.warning("cairosvg not available, trying alternative method")
        return False
    except Exception as e:
        logger.error(f"Failed to convert SVG to PNG with cairosvg: {e}")
        return False


def convert_svg_to_png_wand(svg_path: Path, png_path: Path, width: int = 800, height: int = 600) -> bool:
    """
    Convert SVG to PNG using Wand (ImageMagick) library.
    
    Args:
        svg_path: Path to input SVG file
        png_path: Path to output PNG file
        width: Output width in pixels
        height: Output height in pixels
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from wand.image import Image
        from wand.color import Color
        
        with Image() as img:
            img.format = 'svg'
            img.background_color = Color('white')
            
            # Read SVG
            with open(svg_path, 'rb') as f:
                svg_data = f.read()
            img.read(blob=svg_data)
            
            # Resize to desired dimensions
            img.resize(width, height)
            
            # Convert to PNG
            img.format = 'png'
            img.save(filename=str(png_path))
        
        logger.info(f"Converted SVG to PNG with Wand: {svg_path} -> {png_path}")
        return True
        
    except ImportError:
        logger.warning("Wand not available, trying alternative method")
        return False
    except Exception as e:
        logger.error(f"Failed to convert SVG to PNG with Wand: {e}")
        return False


def convert_svg_to_png_subprocess(svg_path: Path, png_path: Path, width: int = 800, height: int = 600) -> bool:
    """
    Convert SVG to PNG using subprocess calls to system tools.
    
    Args:
        svg_path: Path to input SVG file
        png_path: Path to output PNG file
        width: Output width in pixels
        height: Output height in pixels
    
    Returns:
        bool: True if successful, False otherwise
    """
    import subprocess
    import shutil
    
    # Try different system tools in order of preference
    tools = [
        ["rsvg-convert", "-w", str(width), "-h", str(height), "-o", str(png_path), str(svg_path)],
        ["inkscape", "--export-type=png", f"--export-width={width}", f"--export-height={height}", 
         f"--export-filename={png_path}", str(svg_path)],
        ["convert", "-size", f"{width}x{height}", str(svg_path), str(png_path)]  # ImageMagick
    ]
    
    for tool_cmd in tools:
        tool_name = tool_cmd[0]
        
        # Check if tool is available
        if not shutil.which(tool_name):
            logger.debug(f"Tool {tool_name} not found")
            continue
            
        try:
            result = subprocess.run(
                tool_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and png_path.exists():
                logger.info(f"Converted SVG to PNG with {tool_name}: {svg_path} -> {png_path}")
                return True
            else:
                logger.warning(f"Tool {tool_name} failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.warning(f"Tool {tool_name} timed out")
        except Exception as e:
            logger.warning(f"Tool {tool_name} error: {e}")
    
    return False


def convert_svg_to_png(svg_path: Path, png_path: Path, width: int = 800, height: int = 600) -> bool:
    """
    Convert SVG to PNG using the best available method.
    
    Tries multiple conversion methods in order of preference:
    1. cairosvg (Python library)
    2. Wand/ImageMagick (Python library) 
    3. System tools (rsvg-convert, inkscape, convert)
    
    Args:
        svg_path: Path to input SVG file
        png_path: Path to output PNG file
        width: Output width in pixels
        height: Output height in pixels
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not svg_path.exists():
        logger.error(f"SVG file does not exist: {svg_path}")
        return False
    
    # Ensure output directory exists
    png_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Try conversion methods in order
    conversion_methods = [
        convert_svg_to_png_cairosvg,
        convert_svg_to_png_wand,
        convert_svg_to_png_subprocess
    ]
    
    for method in conversion_methods:
        if method(svg_path, png_path, width, height):
            return True
    
    logger.error(f"All SVG to PNG conversion methods failed for: {svg_path}")
    return False


def convert_svg_views_to_png(svg_files: Dict[str, str], output_dir: Path, base_name: str) -> Dict[str, Any]:
    """
    Convert a set of SVG view files to PNG format.
    
    Args:
        svg_files: Dictionary mapping view names to SVG file paths
        output_dir: Directory to save PNG files
        base_name: Base name for the PNG files
    
    Returns:
        Dict containing conversion results and PNG file paths
    """
    results = {
        "status": "success",
        "files": {},
        "errors": []
    }
    
    for view_name, svg_path_str in svg_files.items():
        svg_path = Path(svg_path_str)
        png_path = output_dir / f"{base_name}_{view_name}.png"
        
        if convert_svg_to_png(svg_path, png_path):
            results["files"][view_name] = str(png_path)
        else:
            results["errors"].append(f"Failed to convert {view_name} view from SVG to PNG")
    
    # Update status based on results
    if results["errors"] and not results["files"]:
        results["status"] = "error"
    elif results["errors"]:
        results["status"] = "partial"
    
    return results