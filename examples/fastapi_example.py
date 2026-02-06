from fastapi import FastAPI, Depends, Request
from py_rate_guard.adapters.fastapi import FastAPIRateGuard, RateLimitMiddleware
from py_rate_guard.models.config import RateGuardConfig, RateLimitRule, RedisConfig
from py_rate_guard.resolvers.default import HeaderResolver

app = FastAPI()

# Configuration
config = RateGuardConfig(
    redis=RedisConfig(host="localhost", port=6379),
    global_rules=[
        RateLimitRule(limit="100/minute", strategy="sliding_window")
    ],
    in_memory_fallback=True
)

guard = FastAPIRateGuard(config)

# Global rate limiting via middleware
app.add_middleware(RateLimitMiddleware, guard=guard)

@app.get("/")
async def root():
    return {"message": "Hello World"}

# Per-route rate limiting with custom key (API Key in header)
api_key_resolver = HeaderResolver(header_name="X-API-KEY")

@app.get("/premium")
@guard.limit(limit="5/minute", strategy="token_bucket", key_resolver=api_key_resolver)
async def premium_route(request: Request):
    return {"message": "Welcome to the premium route!"}

@app.get("/fast")
@guard.limit(limit="10/second", strategy="fixed_window")
async def fast_route(request: Request):
    return {"message": "You can call this fast"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
