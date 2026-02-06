# py-rate-guard

A production-grade, Redis-backed API Rate Limiting & Throttling library for Python. Developed for high-traffic environments where correctness, performance, and observability are critical.

## Features

-   **Multiple Algorithms**: Sliding Window, Token Bucket, and Fixed Window.
-   **Atomic Operations**: All Redis operations are implemented using Lua scripts to ensure correctness and prevent race conditions.
-   **Framework Agnostic**: Core engine works anywhere. Built-in adapters for **FastAPI**, **Starlette**, and **Django**.
-   **Hierarchical Rules**: Apply global, per-IP, per-user, or per-route limits simultaneously.
-   **Flexible Key Resolution**: Extract keys from IP, Headers, JWT claims, or custom logic.
-   **Graceful Degradation**: Support for fail-open and in-memory fallback if Redis is unavailable.
-   **Deep Observability**: Structured JSON logging and Prometheus metrics out of the box.
-   **Distributed Ready**: Supports Redis Cluster, Sentinel, and connection pooling.

## Installation

```bash
pip install py-rate-guard
```

For FastAPI support:
```bash
pip install py-rate-guard[fastapi]
```

## Quick Start (FastAPI)

```python
from fastapi import FastAPI, Request
from py_rate_guard.adapters.fastapi import FastAPIRateGuard, RateLimitMiddleware
from py_rate_guard.models.config import RateGuardConfig, RateLimitRule

app = FastAPI()

# 1. Configure the guard
config = RateGuardConfig(
    global_rules=[RateLimitRule(limit="100/minute")]
)
guard = FastAPIRateGuard(config)

# 2. Add global middleware
app.add_middleware(RateLimitMiddleware, guard=guard)

# 3. Add per-route limits
@app.get("/sensitive-data")
@guard.limit(limit="5/minute")
async def get_data(request: Request):
    return {"data": "..."}
```

## Configuration

`py-rate-guard` uses Pydantic for configuration, allowing easy validation and integration with environment variables.

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `enabled` | `bool` | `True` | Master switch for the rate limiter. |
| `fail_open` | `bool` | `True` | If Redis is down, allow requests. |
| `in_memory_fallback`| `bool` | `False` | Use local memory if Redis is down. |
| `global_rules` | `List` | `[]` | List of rules applied to every request. |

## Observability

The library exports Prometheus metrics:
-   `rate_guard_requests_allowed_total`: Counter of allowed requests.
-   `rate_guard_requests_blocked_total`: Counter of blocked requests.
-   `rate_guard_redis_latency_seconds`: Histogram of Redis operation times.

## License

MIT
