import asyncio
from typing import Any, Callable, Optional
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import MiddlewareNotUsed
from py_rate_guard.core.engine import RateLimiter
from py_rate_guard.models.config import RateGuardConfig, RateLimitRule
from py_rate_guard.resolvers.default import IPResolver
import asgiref.sync

class DjangoRateGuardMiddleware:
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        # Typically loaded from settings.py
        from django.conf import settings
        config_dict = getattr(settings, "RATE_GUARD", {})
        self.config = RateGuardConfig(**config_dict)
        
        if not self.config.enabled:
            raise MiddlewareNotUsed()
            
        self.limiter = RateLimiter(self.config)
        self.resolver = IPResolver()

    def __call__(self, request):
        if asyncio.iscoroutinefunction(self.get_response):
            return self._async_call(request)
        return self._sync_call(request)

    def _sync_call(self, request):
        if self.config.global_rules:
            # Resolve key
            key = asgiref.sync.async_to_sync(self.resolver.resolve)(request)
            
            allowed, rule, retry_after = asgiref.sync.async_to_sync(self.limiter.check)(
                key, self.config.global_rules
            )
            
            if not allowed:
                return self._rate_limit_response(retry_after)

        response = self.get_response(request)
        return response

    async def _async_call(self, request):
        if self.config.global_rules:
            key = await self.resolver.resolve(request)
            allowed, rule, retry_after = await self.limiter.check(
                key, self.config.global_rules
            )
            
            if not allowed:
                return self._rate_limit_response(retry_after)

        response = await self.get_response(request)
        return response

    def _rate_limit_response(self, retry_after: int):
        response = JsonResponse(
            {"detail": "Rate limit exceeded", "retry_after": retry_after},
            status=429
        )
        response["Retry-After"] = str(retry_after)
        return response
