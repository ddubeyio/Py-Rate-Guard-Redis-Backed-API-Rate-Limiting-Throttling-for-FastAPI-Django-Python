import time
import asyncio
from typing import Tuple, Dict, List, Optional
from py_rate_guard.storage.base import BaseStorage

class MemoryStorage(BaseStorage):
    def __init__(self):
        self._data: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()

    async def check_and_increment(
        self, 
        key: str, 
        limit: int, 
        window: int, 
        strategy: str,
        increment: int = 1,
        **kwargs
    ) -> Tuple[bool, int, int]:
        async with self._lock:
            now = time.time()
            if key not in self._data:
                self._data[key] = []
            
            # Simple Sliding Window implementation for memory
            window_start = now - window
            self._data[key] = [t for t in self._data[key] if t > window_start]
            
            if len(self._data[key]) + increment <= limit:
                for _ in range(increment):
                    self._data[key].append(now)
                return True, limit - len(self._data[key]), 0
            else:
                retry_after = 0
                if self._data[key]:
                    retry_after = int(max(0, self._data[key][0] + window - now))
                return False, 0, retry_after

    async def close(self):
        self._data.clear()
