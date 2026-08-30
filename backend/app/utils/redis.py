import json
import redis.asyncio as redis
from typing import Optional, Union, Any
from app.core.config import settings

# Global Redis client instance
redis_client: Optional[redis.Redis] = None


async def init_redis():
    """Initialize Redis connection."""
    global redis_client
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30,
    )
    # Test connection
    try:
        await redis_client.ping()
    except redis.ConnectionError:
        raise ConnectionError("Failed to connect to Redis")


async def close_redis():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


def get_redis() -> redis.Redis:
    """Get Redis client instance."""
    if redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return redis_client


async def set_cache(key: str, value: Any, expire: int = None) -> bool:
    """
    Set a value in Redis cache.

    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        expire: Expiration time in seconds (optional)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        client = get_redis()
        serialized_value = json.dumps(value)
        if expire:
            return await client.setex(key, expire, serialized_value)
        else:
            return await client.set(key, serialized_value)
    except (json.JSONEncodeError, redis.RedisError):
        return False


async def get_cache(key: str) -> Optional[Any]:
    """
    Get a value from Redis cache.

    Args:
        key: Cache key

    Returns:
        Any: Cached value or None if not found/error
    """
    try:
        client = get_redis()
        value = await client.get(key)
        if value is None:
            return None
        return json.loads(value)
    except (json.JSONDecodeError, redis.RedisError):
        return None


async def delete_cache(key: str) -> bool:
    """
    Delete a value from Redis cache.

    Args:
        key: Cache key

    Returns:
        bool: True if key was deleted, False otherwise
    """
    try:
        client = get_redis()
        result = await client.delete(key)
        return result > 0
    except redis.RedisError:
        return False


async def exists_cache(key: str) -> bool:
    """
    Check if a key exists in Redis cache.

    Args:
        key: Cache key

    Returns:
        bool: True if key exists, False otherwise
    """
    try:
        client = get_redis()
        return await client.exists(key) > 0
    except redis.RedisError:
        return False


async def increment_cache(key: str, amount: int = 1) -> Optional[int]:
    """
    Increment a numeric value in Redis cache.

    Args:
        key: Cache key
        amount: Amount to increment by

    Returns:
        Optional[int]: New value after increment or None if error
    """
    try:
        client = get_redis()
        return await client.incrby(key, amount)
    except (redis.RedisError, ValueError):
        return None


async def set_hash(key: str, field: str, value: Any, expire: int = None) -> bool:
    """
    Set a field in a Redis hash.

    Args:
        key: Hash key
        field: Field name
        value: Value to store (will be JSON serialized)
        expire: Expiration time in seconds (optional)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        client = get_redis()
        serialized_value = json.dumps(value)
        await client.hset(key, field, serialized_value)
        if expire:
            await client.expire(key, expire)
        return True
    except (json.JSONEncodeError, redis.RedisError):
        return False


async def get_hash(key: str, field: str) -> Optional[Any]:
    """
    Get a field from a Redis hash.

    Args:
        key: Hash key
        field: Field name

    Returns:
        Any: Field value or None if not found/error
    """
    try:
        client = get_redis()
        value = await client.hget(key, field)
        if value is None:
            return None
        return json.loads(value)
    except (json.JSONDecodeError, redis.RedisError):
        return None