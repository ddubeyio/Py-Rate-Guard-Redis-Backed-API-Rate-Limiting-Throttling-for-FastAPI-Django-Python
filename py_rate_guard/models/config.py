from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, validator
import re

class RateLimitRule(BaseModel):
    limit: str  # e.g., "100/minute", "10/second"
    capacity: Optional[int] = None  # For Token Bucket / Leaky Bucket
    strategy: str = "sliding_window"
    key_prefix: str = "rl"
    
    @property
    def requests(self) -> int:
        return int(self.limit.split('/')[0])
    
    @property
    def window_seconds(self) -> int:
        count, period = self.limit.split('/')
        count = int(count)
        period = period.lower()
        
        mapping = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
            "day": 86400,
        }
        
        # Handle cases like "10/2minutes" if needed, but for now simple
        if period in mapping:
            return mapping[period]
        
        # Regex to handle "2minutes", "5h", etc.
        match = re.match(r"(\d+)?\s*(s|sec|second|m|min|minute|h|hour|d|day)s?", period)
        if match:
            multiplier = int(match.group(1) or 1)
            unit = match.group(2)
            if unit.startswith('s'): return multiplier * 1
            if unit.startswith('m'): return multiplier * 60
            if unit.startswith('h'): return multiplier * 3600
            if unit.startswith('d'): return multiplier * 86400
            
        raise ValueError(f"Invalid period in limit: {period}")

class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    cluster: bool = False
    sentinel: bool = False
    sentinel_nodes: Optional[List[tuple]] = None
    master_name: Optional[str] = None
    connection_pool_size: int = 10
    timeout: float = 1.0

class RateGuardConfig(BaseModel):
    enabled: bool = True
    redis: RedisConfig = Field(default_factory=RedisConfig)
    fail_open: bool = True  # If Redis is down, allow request
    graceful_degradation: bool = True
    in_memory_fallback: bool = False
    emit_headers: bool = True
    
    # Global rules applied to all requests
    global_rules: List[RateLimitRule] = Field(default_factory=list)
