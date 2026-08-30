from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, Optional
from app.utils.redis import set_cache, get_cache, delete_cache

router = APIRouter()


@router.post("/set/{key}", status_code=status.HTTP_200_OK)
async def set_cache_endpoint(key: str, value: Any, expire: Optional[int] = None):
    """
    Set a value in the cache.
    """
    success = await set_cache(key, value, expire)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to set cache")
    return {"message": f"Cache set for key: {key}"}


@router.get("/get/{key}", response_model=Any)
async def get_cache_endpoint(key: str):
    """
    Get a value from the cache.
    """
    value = await get_cache(key)
    if value is None:
        raise HTTPException(status_code=404, detail="Cache key not found")
    return value


@router.delete("/delete/{key}", status_code=status.HTTP_200_OK)
async def delete_cache_endpoint(key: str):
    """
    Delete a value from the cache.
    """
    success = await delete_cache(key)
    if not success:
        raise HTTPException(status_code=404, detail="Cache key not found")
    return {"message": f"Cache deleted for key: {key}"}