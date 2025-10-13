import json
import os
import hashlib
import redis
from typing import Any, Dict, Optional

r: Optional[redis.Redis] = None


def init_redis() -> None:  
    global r
    if r is not None:
        return 
    try:
        r = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"))
    except Exception as e:
        print(f"Redis initialization failed: {e}")
        print("Make sure Redis is running on localhost:6379")
        r = None


def make_cache_key(request_data: Dict[str, Any]) -> str:  
    encoded = json.dumps(request_data, sort_keys=True)
    return "hotel_search:" + hashlib.sha256(encoded.encode()).hexdigest()


def get_cached_result(request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    global r
    if r is None:
        init_redis()
        if r is None:
            return None

    key = make_cache_key(request_data)
    try:
        cached = r.get(key)
        if cached:
            print(f"Cache hit for key: {key}")
            return json.loads(cached)
        print(f"Cache miss for key: {key}")
    except Exception as e:
        print(f"Redis get error: {e}")
    return None


def set_cached_result(request_data: Dict[str, Any], result: Dict[str, Any], ttl_seconds: int = os.getenv("CACHE_TTL_SECONDS")) -> bool:    
    global r
    if r is None:
        init_redis()
        if r is None:
            return False

    key = make_cache_key(request_data)
    try:
        r.setex(key, ttl_seconds, json.dumps(result))
        print(f"Cached result for 1 day (key={key})")
        return True
    except Exception as e:
        print(f"Redis set error: {e}")
        return False
