# Lua scripts for atomic rate limiting operations

# Sliding Window Algorithm
# KEYS[1]: The rate limit key
# ARGV[1]: Current timestamp (milliseconds)
# ARGV[2]: Window size (milliseconds)
# ARGV[3]: Max requests allowed
# ARGV[4]: Increment amount (usually 1)
SLIDING_WINDOW_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local increment = tonumber(ARGV[4])

local window_start = now - window

-- Remove old entries
redis.call('ZREMRANGEBYSCORE', key, 0, window_start)

-- Count current entries
local current_count = redis.call('ZCARD', key)

if current_count + increment <= limit then
    -- Add new entry for each increment
    for i=1,increment do
        redis.call('ZADD', key, now, now .. '-' .. i .. '-' .. math.random())
    end
    redis.call('PEXPIRE', key, window)
    return {1, limit - (current_count + increment), 0}
else
    -- Get earliest entry to calculate retry_after
    local earliest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after = 0
    if #earliest > 0 then
        retry_after = math.max(0, math.ceil((tonumber(earliest[2]) + window - now) / 1000))
    end
    return {0, 0, retry_after}
end
"""

# Token Bucket Algorithm
# KEYS[1]: The rate limit key
# ARGV[1]: Current timestamp (seconds)
# ARGV[2]: Fill rate (tokens/second)
# ARGV[3]: Capacity
# ARGV[4]: Increment amount
TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local fill_rate = tonumber(ARGV[2])
local capacity = tonumber(ARGV[3])
local increment = tonumber(ARGV[4])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1]) or capacity
local last_refill = tonumber(bucket[2]) or now

-- Refill tokens
local delta = math.max(0, now - last_refill)
tokens = math.min(capacity, tokens + (delta * fill_rate))

local allowed = 0
local remaining = tokens
local retry_after = 0

if tokens >= increment then
    tokens = tokens - increment
    allowed = 1
    remaining = tokens
else
    -- Calculate when enough tokens will be available
    retry_after = math.ceil((increment - tokens) / fill_rate)
end

redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
redis.call('EXPIRE', key, math.ceil(capacity / fill_rate) + 10)

return {allowed, math.floor(remaining), retry_after}
"""

# Fixed Window Algorithm
# KEYS[1]: Key
# ARGV[1]: Window size (seconds)
# ARGV[2]: Limit
# ARGV[3]: Increment
FIXED_WINDOW_SCRIPT = """
local key = KEYS[1]
local window = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local increment = tonumber(ARGV[3])

local current = redis.call('GET', key)
if current and tonumber(current) + increment > limit then
    local ttl = redis.call('TTL', key)
    return {0, 0, ttl}
else
    local new_val = redis.call('INCRBY', key, increment)
    if new_val == increment then
        redis.call('EXPIRE', key, window)
    end
    return {1, limit - new_val, 0}
end
"""

# Leaky Bucket Algorithm
# KEYS[1]: Key
# ARGV[1]: Current timestamp (seconds)
# ARGV[2]: Leak rate (requests/second)
# ARGV[3]: Capacity
# ARGV[4]: Increment
LEAKY_BUCKET_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local leak_rate = tonumber(ARGV[2])
local capacity = tonumber(ARGV[3])
local increment = tonumber(ARGV[4])

local bucket = redis.call('HMGET', key, 'level', 'last_leak')
local level = tonumber(bucket[1]) or 0
local last_leak = tonumber(bucket[2]) or now

-- Leak requests
local delta = math.max(0, now - last_leak)
level = math.max(0, level - (delta * leak_rate))

local allowed = 0
local remaining = capacity - level
local retry_after = 0

if level + increment <= capacity then
    level = level + increment
    allowed = 1
    remaining = capacity - level
else
    -- Calculate when there will be space
    retry_after = math.ceil((level + increment - capacity) / leak_rate)
end

redis.call('HMSET', key, 'level', level, 'last_leak', now)
redis.call('EXPIRE', key, math.ceil(capacity / leak_rate) + 10)

return {allowed, math.floor(remaining), retry_after}
"""
