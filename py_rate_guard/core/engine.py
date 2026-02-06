import logging
import time
from typing import List, Tuple, Optional, Any
from py_rate_guard.storage.base import BaseStorage
from py_rate_guard.storage.redis import RedisStorage
from py_rate_guard.storage.memory import MemoryStorage
from py_rate_guard.models.config import RateGuardConfig, RateLimitRule
from py_rate_guard.exceptions import RateLimitExceeded, StorageError
from py_rate_guard.observability.metrics import RateGuardLogger, REDIS_LATENCY
from py_rate_guard.resolvers.default import BaseResolver

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, config: RateGuardConfig):
        self.config = config
        self.storage: BaseStorage = RedisStorage(config.redis)
        self.fallback_storage: Optional[BaseStorage] = None
        self.rg_logger = RateGuardLogger()
        if config.in_memory_fallback:
            self.fallback_storage = MemoryStorage()

    async def check(
        self, 
        key: str, 
        rules: List[RateLimitRule]
    ) -> Tuple[bool, Optional[RateLimitRule], int]:
        """
        Check all rules for a given key.
        Returns: (is_allowed, violated_rule, retry_after)
        """
        if not self.config.enabled:
            return True, None, 0

        for rule in rules:
            full_key = f"{rule.key_prefix}:{key}:{rule.limit}"
            
            allowed, remaining, retry_after = False, 0, 0
            
            try:
                start_time = time.perf_counter()
                allowed, remaining, retry_after = await self.storage.check_and_increment(
                    key=full_key,
                    limit=rule.requests,
                    window=rule.window_seconds,
                    strategy=rule.strategy,
                    capacity=rule.capacity
                )
                REDIS_LATENCY.observe(time.perf_counter() - start_time)
            except StorageError as e:
                logger.warning(f"Rate limiter primary storage error: {e}")
                if self.config.graceful_degradation and self.fallback_storage:
                    logger.info(f"Falling back to memory storage for key {full_key}")
                    allowed, remaining, retry_after = await self.fallback_storage.check_and_increment(
                        key=full_key,
                        limit=rule.requests,
                        window=rule.window_seconds,
                        strategy=rule.strategy,
                        capacity=rule.capacity
                    )
                elif self.config.fail_open:
                    logger.warning("Primary storage failed and no fallback available, failing open")
                    return True, None, 0
                else:
                    logger.error("Primary storage failed, no fallback, and fail_open is False")
                    raise

            if not allowed:
                self.rg_logger.log_violation(key, rule, retry_after)
                return False, rule, retry_after

            self.rg_logger.log_allowed(rule)

        return True, None, 0

    async def close(self):
        await self.storage.close()
        if self.fallback_storage:
            await self.fallback_storage.close()
