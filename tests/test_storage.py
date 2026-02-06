import pytest
import asyncio
import time
from fakeredis.aioredis import FakeRedis
from py_rate_guard.storage.redis import RedisStorage
from py_rate_guard.models.config import RedisConfig

@pytest.fixture
async def redis_storage():
    config = RedisConfig()
    storage = RedisStorage(config)
    # Patch the client with FakeRedis
    storage.client = FakeRedis(decode_responses=True)
    # Register scripts manually for FakeRedis
    from py_rate_guard.utils.lua import SLIDING_WINDOW_SCRIPT, TOKEN_BUCKET_SCRIPT, FIXED_WINDOW_SCRIPT
    storage._scripts['sliding_window'] = storage.client.register_script(SLIDING_WINDOW_SCRIPT)
    storage._scripts['token_bucket'] = storage.client.register_script(TOKEN_BUCKET_SCRIPT)
    storage._scripts['fixed_window'] = storage.client.register_script(FIXED_WINDOW_SCRIPT)
    return storage

@pytest.mark.asyncio
async def test_fixed_window(redis_storage):
    key = "test_fixed"
    limit = 2
    window = 10
    
    # First request
    allowed, remaining, retry_after = await redis_storage.check_and_increment(
        key, limit, window, "fixed_window"
    )
    assert allowed is True
    assert remaining == 1
    
    # Second request
    allowed, remaining, retry_after = await redis_storage.check_and_increment(
        key, limit, window, "fixed_window"
    )
    assert allowed is True
    assert remaining == 0
    
    # Third request (blocked)
    allowed, remaining, retry_after = await redis_storage.check_and_increment(
        key, limit, window, "fixed_window"
    )
    assert allowed is False
    assert retry_after > 0

@pytest.mark.asyncio
async def test_sliding_window(redis_storage):
    key = "test_sliding"
    limit = 2
    window = 1 # 1 second window
    
    # Fill limit
    await redis_storage.check_and_increment(key, limit, window, "sliding_window")
    await redis_storage.check_and_increment(key, limit, window, "sliding_window")
    
    # Third should be blocked
    allowed, _, _ = await redis_storage.check_and_increment(key, limit, window, "sliding_window")
    assert allowed is False
    
    # Wait for window to pass
    await asyncio.sleep(1.1)
    
    # Should be allowed again
    allowed, _, _ = await redis_storage.check_and_increment(key, limit, window, "sliding_window")
    assert allowed is True
