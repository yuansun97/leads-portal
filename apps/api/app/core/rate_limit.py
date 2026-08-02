"""Simple in-process rate limiter for public lead creation.

Adequate for a single Railway replica at low QPS. Keys are IP and email so
rotating either alone is not enough to spam freely.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def hit(self, key: str, *, limit: int, window_seconds: float) -> None:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            bucket = self._events[key]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many lead submissions. Please try again later.",
                    headers={"Retry-After": str(int(window_seconds))},
                )
            bucket.append(now)


lead_create_limiter = SlidingWindowLimiter()


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or "unknown"
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def enforce_lead_create_rate_limits(
    request: Request,
    *,
    email: str,
    per_ip_per_minute: int,
    per_email_per_hour: int,
) -> None:
    ip = client_ip(request)
    lead_create_limiter.hit(f"ip:{ip}", limit=per_ip_per_minute, window_seconds=60)
    normalized = email.strip().lower()
    lead_create_limiter.hit(f"email:{normalized}", limit=per_email_per_hour, window_seconds=3600)
