from __future__ import annotations

import os

DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)

CORS_ALLOW_METHODS = ("GET", "POST", "OPTIONS")
CORS_ALLOW_HEADERS = ("Accept", "Content-Type")
CORS_EXPOSE_HEADERS = ("Retry-After",)


def env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def parse_cors_origins(raw: str | None) -> list[str]:
    """Explicit origin list. Wildcard '*' is ignored (fail closed if nothing remains)."""
    if raw is None or not raw.strip():
        return list(DEFAULT_CORS_ORIGINS)

    origins: list[str] = []
    for part in raw.split(","):
        origin = part.strip()
        if not origin or origin == "*":
            continue
        origins.append(origin)
    return origins


def cors_origins_from_env() -> list[str]:
    return parse_cors_origins(os.getenv("GRADEPILOT_CORS_ORIGINS"))


def enable_api_docs_from_env() -> bool:
    # Default on for local development. Production should set 0.
    return env_bool("GRADEPILOT_ENABLE_API_DOCS", True)


def enable_hsts_from_env() -> bool:
    # Default off so localhost HTTP never receives HSTS.
    return env_bool("GRADEPILOT_ENABLE_HSTS", False)
