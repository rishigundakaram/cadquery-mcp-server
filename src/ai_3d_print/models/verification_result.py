"""Verification result models and enums."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class VerificationResult(Enum):
    """Enum for verification results."""
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"


@dataclass
class VerificationResponse:
    """Response object for CAD verification operations."""
    
    status: VerificationResult
    details: str
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Validate the response object."""
        if self.status == VerificationResult.ERROR and not self.error_message:
            raise ValueError("ERROR status requires an error_message")
        
        if self.status != VerificationResult.ERROR and self.error_message:
            raise ValueError("Non-ERROR status should not have error_message")
    
    @classmethod
    def success(cls, details: str) -> "VerificationResponse":
        """Create a successful verification response."""
        return cls(status=VerificationResult.PASS, details=details)
    
    @classmethod
    def failure(cls, details: str) -> "VerificationResponse":
        """Create a failed verification response."""
        return cls(status=VerificationResult.FAIL, details=details)
    
    @classmethod
    def error(cls, error_message: str) -> "VerificationResponse":
        """Create an error verification response."""
        return cls(
            status=VerificationResult.ERROR,
            details="Verification could not be completed",
            error_message=error_message
        )
    
    def is_success(self) -> bool:
        """Check if verification was successful."""
        return self.status == VerificationResult.PASS
    
    def is_failure(self) -> bool:
        """Check if verification failed."""
        return self.status == VerificationResult.FAIL
    
    def is_error(self) -> bool:
        """Check if verification encountered an error."""
        return self.status == VerificationResult.ERROR