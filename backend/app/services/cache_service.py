import asyncio
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable


_cache: dict[str, dict[str, Any]] = {}
_cache_lock = asyncio.Lock()
_inflight: dict[str, asyncio.Task] = {}
_metrics = Counter()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def set_cache(key: str, data: Any, source: str, ttl_seconds: int):
    if ttl_seconds <= 0:
        raise ValueError("Cache TTL must be greater than zero.")
    async with _cache_lock:
        _cache[key] = {
            "data": data,
            "source": source,
            "updated_at": utc_now_iso(),
            "ttl_seconds": ttl_seconds,
            "timestamp": datetime.now(timezone.utc).timestamp(),
        }
        _metrics["sets"] += 1


async def get_cache(key: str, allow_stale: bool = False):
    async with _cache_lock:
        entry = _cache.get(key)
        if not entry:
            _metrics["misses"] += 1
            return None
        age_seconds = datetime.now(timezone.utc).timestamp() - entry["timestamp"]
        expired = age_seconds > entry["ttl_seconds"]
        if expired and not allow_stale:
            _metrics["expired"] += 1
            _metrics["misses"] += 1
            return None
        _metrics["stale_hits" if expired else "hits"] += 1
        return {**entry, "age_seconds": round(age_seconds, 2), "expired": expired}


async def get_or_load(
    key: str,
    source: str,
    ttl_seconds: int,
    loader: Callable[[], Awaitable[Any]],
):
    """Return fresh cached data, coalescing concurrent loads for one key."""
    cached = await get_cache(key)
    if cached is not None:
        return cached
    async with _cache_lock:
        task = _inflight.get(key)
        if task is None:
            task = asyncio.create_task(loader())
            _inflight[key] = task
            _metrics["upstream_requests"] += 1
        else:
            _metrics["coalesced_requests"] += 1
    try:
        data = await task
        await set_cache(key, data, source, ttl_seconds)
        cached = await get_cache(key)
        if cached is None:
            raise RuntimeError("Cache entry was unavailable after loading.")
        return cached
    finally:
        if task.done():
            async with _cache_lock:
                if _inflight.get(key) is task:
                    _inflight.pop(key, None)


async def delete_cache(key: str):
    async with _cache_lock:
        _cache.pop(key, None)


async def get_all_cache_status():
    async with _cache_lock:
        now = datetime.now(timezone.utc).timestamp()
        return {
            key: {
                "source": entry["source"],
                "updated_at": entry["updated_at"],
                "age_seconds": round(now - entry["timestamp"], 2),
                "ttl_seconds": entry["ttl_seconds"],
                "expired": now - entry["timestamp"] > entry["ttl_seconds"],
            }
            for key, entry in _cache.items()
        }


async def get_cache_metrics():
    async with _cache_lock:
        hits = _metrics["hits"]
        misses = _metrics["misses"]
        total = hits + misses
        return {
            "entries": len(_cache),
            "inflight_requests": len(_inflight),
            "hits": hits,
            "misses": misses,
            "expired": _metrics["expired"],
            "stale_hits": _metrics["stale_hits"],
            "sets": _metrics["sets"],
            "upstream_requests": _metrics["upstream_requests"],
            "coalesced_requests": _metrics["coalesced_requests"],
            "hit_rate_percent": round((hits / total) * 100, 2) if total else 0.0,
        }


async def clear_cache():
    async with _cache_lock:
        _cache.clear()
        _metrics.clear()
