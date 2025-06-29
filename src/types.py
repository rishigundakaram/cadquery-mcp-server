from pathlib import Path
from pydantic import BaseModel


class PNGPaths(BaseModel):
    front: Path
    right: Path
    top: Path
    iso: Path
    back_left: Path
    bottom_right: Path


class VerificationResult(BaseModel):
    status: str
    reasoning: str
    criteria: str
