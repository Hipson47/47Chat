"""Configuration for resilience layer.

Loads resilience settings from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass

from .retry import RetryPolicy


@dataclass
class ResilienceConfig:
    """Configuration for retry policies and circuit breakers."""
    
    # Retry policy settings
    max_retries: int
    timeout_s: float
    base_backoff_ms: int
    max_backoff_ms: int
    jitter_ms: int
    
    # Circuit breaker settings
    cb_failure_threshold: int
    cb_recovery_time_s: int
    cb_half_open_max_success: int
    
    @classmethod
    def from_env(cls) -> "ResilienceConfig":
        """Load configuration from environment variables."""
        return cls(
            # Retry settings
            max_retries=int(os.getenv("R_POLICY_MAX_RETRIES", "3")),
            timeout_s=float(os.getenv("R_POLICY_TIMEOUT_S", "30.0")),
            base_backoff_ms=int(os.getenv("R_POLICY_BASE_BACKOFF_MS", "200")),
            max_backoff_ms=int(os.getenv("R_POLICY_MAX_BACKOFF_MS", "5000")),
            jitter_ms=int(os.getenv("R_POLICY_JITTER_MS", "100")),
            
            # Circuit breaker settings
            cb_failure_threshold=int(os.getenv("CB_THRESHOLD", "5")),
            cb_recovery_time_s=int(os.getenv("CB_COOLDOWN_S", "30")),
            cb_half_open_max_success=int(os.getenv("CB_HALF_OPEN_SUCCESS", "2")),
        )
    
    def to_retry_policy(self) -> RetryPolicy:
        """Convert to RetryPolicy instance."""
        return RetryPolicy(
            max_retries=self.max_retries,
            base_backoff_ms=self.base_backoff_ms,
            max_backoff_ms=self.max_backoff_ms,
            jitter_ms=self.jitter_ms,
            timeout_s=self.timeout_s,
        )


# Global configuration instance
_config: ResilienceConfig | None = None


def get_resilience_config() -> ResilienceConfig:
    """Get the global resilience configuration, loading from env if needed."""
    global _config
    if _config is None:
        _config = ResilienceConfig.from_env()
    return _config
