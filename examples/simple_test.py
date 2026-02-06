import asyncio
import logging
import sys
from py_rate_guard.core.engine import RateLimiter
from py_rate_guard.models.config import RateGuardConfig, RateLimitRule

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(levelname)s: %(message)s')

async def run_test():
    """
    Demonstrates rate limiting with in-memory fallback.
    If Redis is not running (default), it will log a warning and use local memory.
    """
    config = RateGuardConfig(
        in_memory_fallback=True,  # Enables local memory fallback
        fail_open=False,          # Do not allow requests if all storage fails
        graceful_degradation=True # Enable falling back to memory if Redis fails
    )
    
    limiter = RateLimiter(config)
    
    # Rule: 3 requests per 10 seconds (Shortened for fast demonstration)
    # Note: Primary Redis attempts may slow down this further if Redis is absent.
    rules = [RateLimitRule(limit="3/10s", strategy="sliding_window")]
    user_key = "demo_user"

    print(f"\n--- Starting py-rate-guard Demo (Limit: 3 req / 10s) ---")
    
    for i in range(1, 6):
        print(f"Request {i}:", end=" ", flush=True)
        allowed, rule, retry_after = await limiter.check(user_key, rules)
        
        if allowed:
            print("OK")
        else:
            print(f"BLOCKED (Retry after {retry_after}s)")
            
    await limiter.close()

if __name__ == "__main__":
    asyncio.run(run_test())
