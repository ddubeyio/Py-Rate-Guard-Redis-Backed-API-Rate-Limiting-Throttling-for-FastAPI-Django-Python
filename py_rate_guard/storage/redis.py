import time
import asyncio
from typing import Tuple, Optional, Any
import redis.asyncio as redis
from redis.asyncio.cluster import RedisCluster
from redis.asyncio.sentinel import Sentinel

from py_rate_guard.storage.base import BaseStorage
from py_rate_guard.utils.lua import (
    SLIDING_WINDOW_SCRIPT, 
    TOKEN_BUCKET_SCRIPT, 
    FIXED_WINDOW_SCRIPT,
    LEAKY_BUCKET_SCRIPT
)
from py_rate_guard.exceptions import StorageError
from py_rate_guard.models.config import RedisConfig

class RedisStorage(BaseStorage):
    def __init__(self, config: RedisConfig):
        self.config = config
        self.client: Optional[redis.Redis] = None
        self._scripts = {}

    async def connect(self):
        if self.client:
            return

        try:
            if self.config.cluster:
                self.client = RedisCluster(
                    host=self.config.host,
                    port=self.config.port,
                    password=self.config.password,
                    ssl=self.config.ssl,
                    decode_responses=True
                )
            elif self.config.sentinel:
                sentinel = Sentinel(
                    self.config.sentinel_nodes,
                    password=self.config.password,
                    socket_timeout=self.config.timeout
                )
                self.client = sentinel.master_for(
                    self.config.master_name,
                    decode_responses=True
                )
            else:
                self.client = redis.Redis(
                    host=self.config.host,
                    port=self.config.port,
                    db=self.config.db,
                    password=self.config.password,
                    ssl=self.config.ssl,
                    decode_responses=True,
                    max_connections=self.config.connection_pool_size
                )
            
            # Register scripts
            self._scripts['sliding_window'] = self.client.register_script(SLIDING_WINDOW_SCRIPT)
            self._scripts['token_bucket'] = self.client.register_script(TOKEN_BUCKET_SCRIPT)
            self._scripts['fixed_window'] = self.client.register_script(FIXED_WINDOW_SCRIPT)
            self._scripts['leaky_bucket'] = self.client.register_script(LEAKY_BUCKET_SCRIPT)
            
        except Exception as e:
            raise StorageError(f"Failed to connect to Redis: {e}")

    async def check_and_increment(
        self, 
        key: str, 
        limit: int, 
        window: int, 
        strategy: str,
        increment: int = 1,
        **kwargs
    ) -> Tuple[bool, int, int]:
        if not self.client:
            await self.connect()

        try:
            if strategy == "sliding_window":
                # Convert window and now to milliseconds
                now = int(time.time() * 1000)
                window_ms = window * 1000
                res = await self._scripts['sliding_window'](
                    keys=[key], 
                    args=[now, window_ms, limit, increment]
                )
            elif strategy == "token_bucket":
                now = int(time.time())
                fill_rate = limit / window
                capacity = kwargs.get('capacity', limit)
                res = await self._scripts['token_bucket'](
                    keys=[key], 
                    args=[now, fill_rate, capacity, increment]
                )
            elif strategy == "fixed_window":
                res = await self._scripts['fixed_window'](
                    keys=[key], 
                    args=[window, limit, increment]
                )
            elif strategy == "leaky_bucket":
                now = int(time.time())
                leak_rate = limit / window
                capacity = kwargs.get('capacity', limit)
                res = await self._scripts['leaky_bucket'](
                    keys=[key], 
                    args=[now, leak_rate, capacity, increment]
                )
            else:
                raise StorageError(f"Unsupported strategy: {strategy}")

            return bool(res[0]), int(res[1]), int(res[2])
        except Exception as e:
            raise StorageError(f"Redis operation failed: {e}")

    async def close(self):
        if self.client:
            await self.client.close()
            self.client = None
