from abc import ABC, abstractmethod
from typing import Optional, Tuple

class BaseStorage(ABC):
    @abstractmethod
    async def check_and_increment(
        self, 
        key: str, 
        limit: int, 
        window: int, 
        strategy: str,
        increment: int = 1,
        **kwargs
    ) -> Tuple[bool, int, int]:
        """
        Check if the limit is exceeded and increment the counter.
        Returns: (is_allowed, remaining_requests, retry_after)
        """
        pass

    @abstractmethod
    def close(self):
        pass
