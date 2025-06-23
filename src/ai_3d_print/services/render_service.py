"""Rendering service for CAD models."""

import logging
from pathlib import Path
from typing import List

import cadquery as cq

from ..models import RenderResult, ImageViews
from ..render_svg import generate_svg_views
from ..svg_to_png import convert_svg_views_to_png

logger = logging.getLogger(__name__)


class RenderService:
    """Service for rendering CAD models to STL and PNG files."""
    
    def __init__(self):
        """Initialize the render service."""
        pass
    
    def generate_stl(self, model: cq.Workplane, output_path: Path) -> bool:
        """
        Generate STL file from CAD-Query model.
        
        Args:
            model: CAD-Query Workplane object
            output_path: Path where STL file should be saved
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Export to STL
            cq.exporters.export(model, str(output_path))
            logger.info(f"STL generated successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate STL: {e}")
            return False
    
    def generate_image_views(self, model: cq.Workplane, output_dir: Path, base_name: str) -> ImageViews:
        """
        Generate PNG image views of the CAD model.
        
        Args:
            model: CAD-Query Workplane object
            output_dir: Directory to save PNG files
            base_name: Base name for the PNG files (without extension)
        
        Returns:
            ImageViews object with paths to generated images
            
        Raises:
            RuntimeError: If image generation fails
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating PNG views for {base_name} using SVG conversion method")
        
        # First, generate SVG views
        svg_results = generate_svg_views(model, output_dir, base_name)
        
        if svg_results["status"] == "error":
            raise RuntimeError(f"Failed to generate SVG views: {'; '.join(svg_results['errors'])}")
        
        # Convert SVG views to PNG
        png_results = convert_svg_views_to_png(svg_results["files"], output_dir, base_name)
        
        if png_results["status"] == "error":
            raise RuntimeError(f"Failed to convert SVG to PNG: {'; '.join(png_results['errors'])}")
        
        # Create ImageViews object
        try:
            image_views = ImageViews.from_directory(output_dir, base_name)
            logger.info(f"Successfully generated {len(image_views.get_all_paths())} PNG views")
            return image_views
            
        except FileNotFoundError as e:
            raise RuntimeError(f"Generated image files not found: {e}")
    
    def render_model(self, model: cq.Workplane, output_dir: Path, base_name: str) -> RenderResult:
        """
        Render CAD model to both STL and PNG files.
        
        Args:
            model: CAD-Query Workplane object
            output_dir: Directory to save output files
            base_name: Base name for output files
        
        Returns:
            RenderResult with paths to generated files or error information
        """
        errors = []
        stl_path = None
        image_views = None
        
        # Generate STL file
        stl_output_path = output_dir / f"{base_name}.stl"
        if self.generate_stl(model, stl_output_path):
            stl_path = stl_output_path
        else:
            errors.append("Failed to generate STL file")
        
        # Generate PNG views
        try:
            image_views = self.generate_image_views(model, output_dir, base_name)
        except RuntimeError as e:
            errors.append(str(e))
        
        # Return result
        if errors:
            return RenderResult.failure(errors)
        else:
            return RenderResult.success_with_files(stl_path, image_views)