from __future__ import annotations

import math
import os
import threading
import time
from collections import OrderedDict, deque
from dataclasses import dataclass
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

Clock = Callable[[], float]

RATE_LIMIT_DETAIL = (
    "Çok fazla istek gönderildi. Lütfen kısa bir süre sonra tekrar deneyin."
)

ANALYZE_LIMIT_DEFAULT = 5
CALCULATION_LIMIT_DEFAULT = 30
WINDOW_SECONDS_DEFAULT = 60
MAX_CLIENT_KEYS_DEFAULT = 4096


@dataclass(frozen=True)
class RateLimitSettings:
    analyze_limit: int = ANALYZE_LIMIT_DEFAULT
    calculation_limit: int = CALCULATION_LIMIT_DEFAULT
    window_seconds: int = WINDOW_SECONDS_DEFAULT
    max_client_keys: int = MAX_CLIENT_KEYS_DEFAULT
    trust_proxy: bool = False

    @classmethod
    def from_env(cls) -> RateLimitSettings:
        return cls(
            analyze_limit=_positive_int_env(
                "GRADEPILOT_RATE_LIMIT_ANALYZE",
                ANALYZE_LIMIT_DEFAULT,
            ),
            calculation_limit=_positive_int_env(
                "GRADEPILOT_RATE_LIMIT_CALCULATION",
                CALCULATION_LIMIT_DEFAULT,
            ),
            window_seconds=_positive_int_env(
                "GRADEPILOT_RATE_LIMIT_WINDOW_SECONDS",
                WINDOW_SECONDS_DEFAULT,
            ),
            max_client_keys=_positive_int_env(
                "GRADEPILOT_RATE_LIMIT_MAX_KEYS",
                MAX_CLIENT_KEYS_DEFAULT,
            ),
            trust_proxy=_bool_env("GRADEPILOT_TRUST_PROXY", False),
        )


@dataclass(frozen=True)
class RateLimitPolicy:
    bucket: str
    limit: int


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int


class InMemoryRateLimiter:
    """Process-local sliding-window limiter with a bounded key set."""

    def __init__(
        self,
        *,
        max_keys: int = MAX_CLIENT_KEYS_DEFAULT,
        clock: Clock | None = None,
    ) -> None:
        if max_keys < 1:
            raise ValueError("max_keys must be >= 1")
        self._max_keys = max_keys
        self._clock = clock or time.monotonic
        self._lock = threading.Lock()
        self._windows: OrderedDict[str, deque[float]] = OrderedDict()

    @property
    def key_count(self) -> int:
        with self._lock:
            return len(self._windows)

    def hit(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: float,
    ) -> RateLimitDecision:
        if limit < 1:
            raise ValueError("limit must be >= 1")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")

        now = self._clock()
        cutoff = now - window_seconds

        with self._lock:
            hits = self._windows.get(key)
            if hits is None:
                self._purge_expired(cutoff)
                self._evict_until_room()
                hits = deque()
                self._windows[key] = hits
            else:
                self._windows.move_to_end(key)
                _drop_expired(hits, cutoff)
                if not hits:
                    del self._windows[key]
                    self._evict_until_room()
                    hits = deque()
                    self._windows[key] = hits

            if len(hits) >= limit:
                remaining = window_seconds - (now - hits[0])
                retry_after = max(1, math.ceil(remaining))
                return RateLimitDecision(False, retry_after)

            hits.append(now)
            return RateLimitDecision(True, 0)

    def _purge_expired(self, cutoff: float) -> None:
        stale: list[str] = []
        for key, hits in self._windows.items():
            _drop_expired(hits, cutoff)
            if not hits:
                stale.append(key)
        for key in stale:
            del self._windows[key]

    def _evict_until_room(self) -> None:
        while len(self._windows) >= self._max_keys:
            self._windows.popitem(last=False)


def client_identifier(request: Request, *, trust_proxy: bool) -> str:
    """Identify a client without trusting spoofable forwarding headers by default.

    Direct deployment: use the TCP peer address (request.client.host).
    Behind one trusted reverse proxy that appends X-Forwarded-For, set
    GRADEPILOT_TRUST_PROXY=1 and the rightmost forwarded hop is used.
    """
    if trust_proxy:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            parts = [part.strip() for part in forwarded.split(",") if part.strip()]
            if parts:
                return parts[-1]
    if request.client is not None and request.client.host:
        return request.client.host
    return "unknown"


def resolve_policy(
    method: str,
    path: str,
    settings: RateLimitSettings,
) -> RateLimitPolicy | None:
    if method.upper() != "POST":
        return None

    normalized = path.rstrip("/") or "/"
    if normalized == "/api/transcripts/analyze":
        return RateLimitPolicy("analyze", settings.analyze_limit)
    if normalized.startswith("/api/academic"):
        return RateLimitPolicy("calculation", settings.calculation_limit)
    return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        *,
        limiter: InMemoryRateLimiter,
        settings: RateLimitSettings,
    ) -> None:
        super().__init__(app)
        self._limiter = limiter
        self._settings = settings

    async def dispatch(self, request: Request, call_next) -> Response:
        policy = resolve_policy(request.method, request.url.path, self._settings)
        if policy is None:
            return await call_next(request)

        client = client_identifier(
            request,
            trust_proxy=self._settings.trust_proxy,
        )
        decision = self._limiter.hit(
            f"{client}:{policy.bucket}",
            limit=policy.limit,
            window_seconds=self._settings.window_seconds,
        )
        if not decision.allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": RATE_LIMIT_DETAIL},
                headers={
                    "Retry-After": str(decision.retry_after_seconds),
                    "Cache-Control": "no-store",
                },
            )
        return await call_next(request)


def _drop_expired(hits: deque[float], cutoff: float) -> None:
    while hits and hits[0] <= cutoff:
        hits.popleft()


def _positive_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw.strip())
    except ValueError:
        return default
    return value if value >= 1 else default


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}
