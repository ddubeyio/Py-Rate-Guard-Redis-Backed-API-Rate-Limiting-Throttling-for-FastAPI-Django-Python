class RateLimitError(Exception):
    """Base exception for all rate limiting errors."""
    pass

class RateLimitExceeded(RateLimitError):
    """Exception raised when a rate limit is exceeded."""
    def __init__(self, limit: str, retry_after: int, key: str):
        self.limit = limit
        self.retry_after = retry_after
        self.key = key
        super().__init__(f"Rate limit exceeded: {limit}. Retry after {retry_after}s.")

class ConfigurationError(RateLimitError):
    """Exception raised when there is a configuration error."""
    pass

class StorageError(RateLimitError):
    """Exception raised when there is an error with the storage backend."""
    pass
