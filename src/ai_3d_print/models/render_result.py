"""Render result models for CAD operations."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
from .image_views import ImageViews


@dataclass
class RenderResult:
    """Result object for CAD rendering operations."""
    
    success: bool
    stl_path: Optional[Path] = None
    image_views: Optional[ImageViews] = None
    errors: List[str] = None
    
    def __post_init__(self):
        """Initialize errors list if None."""
        if self.errors is None:
            self.errors = []
    
    @classmethod
    def success_with_files(cls, stl_path: Path, image_views: ImageViews) -> "RenderResult":
        """Create a successful render result with files."""
        return cls(
            success=True,
            stl_path=stl_path,
            image_views=image_views
        )
    
    @classmethod
    def failure(cls, errors: List[str]) -> "RenderResult":
        """Create a failed render result."""
        return cls(
            success=False,
            errors=errors
        )
    
    def has_images(self) -> bool:
        """Check if render result includes valid image views."""
        return self.success and self.image_views is not None
    
    def has_stl(self) -> bool:
        """Check if render result includes valid STL file."""
        return self.success and self.stl_path is not None and self.stl_path.exists()
    
    def get_error_summary(self) -> str:
        """Get a summary of all errors."""
        if not self.errors:
            return "No errors"
        return "; ".join(self.errors)