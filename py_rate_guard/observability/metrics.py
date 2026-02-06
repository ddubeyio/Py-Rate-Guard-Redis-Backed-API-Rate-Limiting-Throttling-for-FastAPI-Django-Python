import logging
import json
import time
from typing import Any, Dict, Optional
from prometheus_client import Counter, Histogram

# Metrics
REQUESTS_ALLOWED = Counter(
    "rate_guard_requests_allowed_total",
    "Total number of allowed requests",
    ["rule_name", "strategy"]
)

REQUESTS_BLOCKED = Counter(
    "rate_guard_requests_blocked_total",
    "Total number of blocked requests",
    ["rule_name", "strategy", "key"]
)

REDIS_LATENCY = Histogram(
    "rate_guard_redis_latency_seconds",
    "Latency of Redis operations for rate limiting",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5]
)

class RateGuardLogger:
    def __init__(self, name: str = "py-rate-guard"):
        self.logger = logging.getLogger(name)

    def log_violation(self, key: str, rule: Any, retry_after: int, request_info: Optional[Dict] = None):
        log_data = {
            "event": "rate_limit_violation",
            "key": key,
            "rule": rule.limit,
            "strategy": rule.strategy,
            "retry_after": retry_after,
            "timestamp": time.time(),
        }
        if request_info:
            log_data.update(request_info)
            
        self.logger.warning(json.dumps(log_data))
        
        # Update metrics
        REQUESTS_BLOCKED.labels(
            rule_name=rule.limit,
            strategy=rule.strategy,
            key=key
        ).inc()

    def log_allowed(self, rule: Any):
        REQUESTS_ALLOWED.labels(
            rule_name=rule.limit,
            strategy=rule.strategy
        ).inc()
