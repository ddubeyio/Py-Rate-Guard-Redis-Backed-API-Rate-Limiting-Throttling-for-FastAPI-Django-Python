from typing import Callable, List, Optional, Union
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from functools import wraps

from py_rate_guard.core.engine import RateLimiter
from py_rate_guard.models.config import RateLimitRule, RateGuardConfig
from py_rate_guard.resolvers.default import BaseResolver, IPResolver

class FastAPIRateGuard:
    def __init__(self, config: RateGuardConfig):
        self.limiter = RateLimiter(config)
        self.config = config

    def middleware(self) -> Callable:
        async def dispatch(request: Request, call_next: Callable) -> Response:
            if not self.config.enabled:
                return await call_next(request)

            # Global rules check
            if self.config.global_rules:
                # Use IP as default global key
                resolver = IPResolver()
                key = await resolver.resolve(request)
                
                allowed, rule, retry_after = await self.limiter.check(key, self.config.global_rules)
                if not allowed:
                    return self._rate_limit_response(retry_after)

            response = await call_next(request)
            return response

        return dispatch

    def limit(
        self, 
        limit: str, 
        strategy: str = "sliding_window", 
        key_resolver: Optional[BaseResolver] = None
    ):
        def decorator(func: Callable):
            rule = RateLimitRule(limit=limit, strategy=strategy)
            resolver = key_resolver or IPResolver()

            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Search for request in kwargs or args
                request: Optional[Request] = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                if not request:
                    for k, v in kwargs.items():
                        if isinstance(v, Request):
                            request = v
                            break
                
                if request:
                    key = await resolver.resolve(request)
                    allowed, vi_rule, retry_after = await self.limiter.check(key, [rule])
                    if not allowed:
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="Rate limit exceeded",
                            headers={"Retry-After": str(retry_after)}
                        )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator

    def _rate_limit_response(self, retry_after: int) -> Response:
        return Response(
            content="Rate limit exceeded",
            status_code=429,
            headers={"Retry-After": str(retry_after)}
        )

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, guard: FastAPIRateGuard):
        super().__init__(app)
        self.guard = guard

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        return await self.guard.middleware()(request, call_next)
