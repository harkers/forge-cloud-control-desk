"""GCCD Exception Handling Framework

Provides:
- Retry logic with exponential backoff
- Circuit breaker for failed operations
- Error classification and alerting
- Manual override for stuck operations

Usage:
    from exception_handler import with_retry, CircuitBreaker
    
    @with_retry(max_retries=3)
    def my_operation():
        ...
"""

import time
import functools
import traceback
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Callable, Optional, Any, Dict


class ErrorCategory(Enum):
    """Categories of errors for handling decisions."""
    TRANSIENT = "transient"      # Retry likely to succeed (network timeout)
    PERMANENT = "permanent"      # Retry won't help (invalid credentials)
    RATE_LIMIT = "rate_limit"    # Back off and retry later
    QUOTA_EXCEEDED = "quota"     # Need to wait or request more quota
    UNKNOWN = "unknown"          # Classify as transient initially


class GCCDException(Exception):
    """Base exception for GCCD operations."""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN,
                 retryable: bool = True, details: Optional[Dict] = None):
        super().__init__(message)
        self.category = category
        self.retryable = retryable
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()


class CircuitBreaker:
    """Circuit breaker pattern for external service calls."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                print(f"Circuit breaker: Attempting recovery for {func.__name__}")
            else:
                raise GCCDException(
                    f"Circuit breaker OPEN for {func.__name__} — too many failures",
                    category=ErrorCategory.TRANSIENT,
                    retryable=False
                )
        
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if not self.last_failure_time:
            return True
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout
    
    def _record_success(self):
        """Reset on success."""
        self.failures = 0
        self.state = "CLOSED"
        
    def _record_failure(self):
        """Track failure and open circuit if threshold reached."""
        self.failures += 1
        self.last_failure_time = datetime.now()
        
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            print(f"Circuit breaker: OPEN after {self.failures} failures")


def classify_error(error: Exception) -> ErrorCategory:
    """Classify an exception for handling decisions."""
    error_str = str(error).lower()
    error_type = type(error).__name__.lower()
    
    # Rate limiting
    if any(x in error_str for x in ["rate limit", "too many requests", "quota exceeded"]):
        return ErrorCategory.RATE_LIMIT
    
    # Quota exceeded
    if any(x in error_str for x in ["quota", "limit exceeded", "resource exhausted"]):
        return ErrorCategory.QUOTA_EXCEEDED
    
    # Permanent errors
    if any(x in error_str for x in ["permission denied", "not found", "invalid", "unauthorized"]):
        return ErrorCategory.PERMANENT
    
    # Transient errors
    if any(x in error_str for x in ["timeout", "connection", "temporary", "unavailable", "retry"]):
        return ErrorCategory.TRANSIENT
    
    # Check if it's a GCCDException
    if isinstance(error, GCCDException):
        return error.category
    
    return ErrorCategory.UNKNOWN


def with_retry(max_retries: int = 3, base_delay: float = 1.0,
               max_delay: float = 60.0, circuit_breaker: Optional[CircuitBreaker] = None):
    """Decorator for retry logic with exponential backoff."""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    # Use circuit breaker if provided
                    if circuit_breaker:
                        return circuit_breaker.call(func, *args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                        
                except Exception as e:
                    last_error = e
                    category = classify_error(e)
                    
                    # Don't retry permanent errors
                    if category == ErrorCategory.PERMANENT:
                        print(f"Permanent error on {func.__name__}: {e}")
                        raise GCCDException(
                            f"Permanent error in {func.__name__}: {e}",
                            category=category,
                            retryable=False,
                            details={"original_error": str(e)}
                        )
                    
                    # Last attempt failed
                    if attempt == max_retries:
                        break
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    
                    # Extra delay for rate limiting
                    if category == ErrorCategory.RATE_LIMIT:
                        delay *= 2
                        print(f"Rate limit hit, extending delay to {delay}s")
                    
                    print(f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}")
                    print(f"Retrying in {delay}s...")
                    time.sleep(delay)
            
            # All retries exhausted
            raise GCCDException(
                f"All {max_retries + 1} attempts failed for {func.__name__}",
                category=classify_error(last_error),
                retryable=False,
                details={
                    "last_error": str(last_error),
                    "traceback": traceback.format_exc()
                }
            )
        
        return wrapper
    return decorator


class ManualOverride:
    """Allow manual override for stuck operations."""
    
    def __init__(self, override_dir: Path = None):
        if override_dir is None:
            override_dir = Path(__file__).parent.parent.parent / "data" / "overrides"
        self.override_dir = override_dir
        self.override_dir.mkdir(parents=True, exist_ok=True)
    
    def request_override(self, operation_id: str, reason: str) -> Path:
        """Create override request file."""
        override_file = self.override_dir / f"override_{operation_id}.json"
        
        import json
        override_data = {
            "operation_id": operation_id,
            "requested_at": datetime.now().isoformat(),
            "reason": reason,
            "status": "pending",
            "approved_by": None,
            "approved_at": None
        }
        
        with open(override_file, "w") as f:
            json.dump(override_data, f, indent=2)
        
        print(f"Override requested: {override_file}")
        print(f"Operation {operation_id} will proceed when approved")
        return override_file
    
    def check_override(self, operation_id: str) -> bool:
        """Check if operation has approved override."""
        import json
        
        # Check for approved override file
        override_file = self.override_dir / f"override_{operation_id}.json"
        
        if not override_file.exists():
            return False
        
        try:
            with open(override_file) as f:
                data = json.load(f)
            return data.get("status") == "approved"
        except Exception:
            return False
    
    def approve_override(self, operation_id: str, approver: str):
        """Approve override request."""
        import json
        
        override_file = self.override_dir / f"override_{operation_id}.json"
        
        if not override_file.exists():
            raise ValueError(f"No override request found for {operation_id}")
        
        with open(override_file) as f:
            data = json.load(f)
        
        data["status"] = "approved"
        data["approved_by"] = approver
        data["approved_at"] = datetime.now().isoformat()
        
        with open(override_file, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"Override approved for {operation_id} by {approver}")


def log_error(error: Exception, operation: str, evidence_dir: Path = None):
    """Log error to evidence directory for troubleshooting."""
    if evidence_dir is None:
        evidence_dir = Path(__file__).parent.parent.parent / "data" / "evidence" / "errors"
    
    evidence_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    error_file = evidence_dir / f"error_{operation}_{timestamp}.json"
    
    import json
    error_data = {
        "timestamp": datetime.now().isoformat(),
        "operation": operation,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "category": classify_error(error).value,
        "traceback": traceback.format_exc()
    }
    
    with open(error_file, "w") as f:
        json.dump(error_data, f, indent=2)
    
    print(f"Error logged: {error_file}")
    return error_file


# Convenience instances
default_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=300)
manual_override = ManualOverride()
