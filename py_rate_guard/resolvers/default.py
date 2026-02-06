from abc import ABC, abstractmethod
from typing import Any, Optional

class BaseResolver(ABC):
    @abstractmethod
    async def resolve(self, request: Any) -> str:
        """Resolve a unique key from the request."""
        pass

class IPResolver(BaseResolver):
    async def resolve(self, request: Any) -> str:
        # Implementation depends on the framework (FastAPI/Django)
        # We'll use a generic approach here and specialize in adapters
        if hasattr(request, "client") and hasattr(request.client, "host"):
            return request.client.host
        if hasattr(request, "META") and "REMOTE_ADDR" in request.META:
            return request.META["REMOTE_ADDR"]
        return "unknown_ip"

class UserResolver(BaseResolver):
    def __init__(self, attr: str = "id"):
        self.attr = attr

    async def resolve(self, request: Any) -> str:
        user = getattr(request, "user", None)
        if user and hasattr(user, self.attr):
            return f"user_{getattr(user, self.attr)}"
        return "anonymous"

class HeaderResolver(BaseResolver):
    def __init__(self, header_name: str):
        self.header_name = header_name

    async def resolve(self, request: Any) -> str:
        headers = getattr(request, "headers", {})
        # FastAPI/Starlette uses headers mapping, Django uses META
        if hasattr(headers, "get"):
            val = headers.get(self.header_name)
        else:
            val = getattr(request, "META", {}).get(f"HTTP_{self.header_name.upper().replace('-', '_')}")
        
        return val or "no_header"

class CompositeResolver(BaseResolver):
    def __init__(self, resolvers: list[BaseResolver], separator: str = ":"):
        self.resolvers = resolvers
        self.separator = separator

    async def resolve(self, request: Any) -> str:
        keys = []
        for r in self.resolvers:
            keys.append(await r.resolve(request))
        return self.separator.join(keys)
