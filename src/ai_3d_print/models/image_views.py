"""Image views models for CAD rendering."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict


@dataclass
class ImageViews:
    """Container for the 4 standard CAD image views."""
    
    right_path: Path
    top_path: Path  
    down_path: Path
    iso_path: Path
    
    def __post_init__(self):
        """Validate that all image files exist."""
        for view_name, path in self.get_view_paths().items():
            if not path.exists():
                raise FileNotFoundError(f"{view_name} view image not found: {path}")
    
    def get_view_paths(self) -> Dict[str, Path]:
        """Get dictionary mapping view names to paths."""
        return {
            "right": self.right_path,
            "top": self.top_path,
            "down": self.down_path,
            "iso": self.iso_path
        }
    
    def get_all_paths(self) -> List[Path]:
        """Get list of all image paths."""
        return [self.right_path, self.top_path, self.down_path, self.iso_path]
    
    def get_file_sizes(self) -> Dict[str, int]:
        """Get file sizes for all views."""
        return {
            view_name: path.stat().st_size 
            for view_name, path in self.get_view_paths().items()
        }
    
    @classmethod
    def from_directory(cls, output_dir: Path, base_name: str) -> "ImageViews":
        """Create ImageViews from a directory and base name."""
        return cls(
            right_path=output_dir / f"{base_name}_right.png",
            top_path=output_dir / f"{base_name}_top.png",
            down_path=output_dir / f"{base_name}_down.png",
            iso_path=output_dir / f"{base_name}_iso.png"
        )