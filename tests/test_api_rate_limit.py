from __future__ import annotations

import io

from fastapi.testclient import TestClient
from starlette.requests import Request

from api.main import create_app
from api.rate_limit import (
    RATE_LIMIT_DETAIL,
    InMemoryRateLimiter,
    RateLimitSettings,
    client_identifier,
    resolve_policy,
)
from models.parse_result import ParseResult
from parsers.credit_options import CreditOption
from parsers.gpa_weighting import FIELD_LOCAL_CREDIT


def _settings(**overrides) -> RateLimitSettings:
    values = dict(
        analyze_limit=2,
        calculation_limit=2,
        window_seconds=60,
        max_client_keys=32,
        trust_proxy=False,
    )
    values.update(overrides)
    return RateLimitSettings(**values)


def _client(settings: RateLimitSettings | None = None, **kwargs) -> TestClient:
    return TestClient(create_app(settings or _settings()), **kwargs)


def _pdf_files():
    return {
        "file": (
            "transcript.pdf",
            io.BytesIO(b"%PDF-1.4 rate-limit-fixture"),
            "application/pdf",
        )
    }


def _summary_payload() -> dict:
    return {
        "courses": [
            {
                "code": "A",
                "name": "Course",
                "gpa_credit": 4,
                "ects": 4,
                "local_credit": 3,
                "grade": "AA",
                "semester": "2024 Güz",
                "source_order": 1,
            }
        ]
    }


def _credit_selection_result() -> ParseResult:
    return ParseResult(
        courses=[],
        format_name="cankaya",
        confidence=1.0,
        requires_user_confirmation=False,
        requires_credit_selection=True,
        warnings=[],
        credit_options=[
            CreditOption(
                label="Kredi",
                field_key=FIELD_LOCAL_CREDIT,
                sample_values=[4.0],
                score=1.0,
            )
        ],
    )


def _http_request(*, host: str, xff: str | None = None) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if xff is not None:
        headers.append((b"x-forwarded-for", xff.encode("latin-1")))
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/academic/summary",
        "raw_path": b"/api/academic/summary",
        "query_string": b"",
        "headers": headers,
        "client": (host, 12345),
        "server": ("testserver", 80),
    }
    return Request(scope)


def test_resolve_policy_classifies_expensive_and_calculation_routes():
    settings = _settings()
    analyze = resolve_policy("POST", "/api/transcripts/analyze", settings)
    summary = resolve_policy("POST", "/api/academic/summary", settings)
    health = resolve_policy("GET", "/health", settings)
    options = resolve_policy("OPTIONS", "/api/academic/summary", settings)

    assert analyze is not None and analyze.bucket == "analyze"
    assert analyze.limit == 2
    assert summary is not None and summary.bucket == "calculation"
    assert health is None
    assert options is None


def test_client_identifier_ignores_forwarded_for_unless_proxy_trusted():
    request = _http_request(host="10.0.0.8", xff="1.1.1.1, 8.8.8.8")
    assert client_identifier(request, trust_proxy=False) == "10.0.0.8"
    assert client_identifier(request, trust_proxy=True) == "8.8.8.8"


def test_limiter_allows_under_limit_and_denies_over_limit():
    limiter = InMemoryRateLimiter(max_keys=8)
    first = limiter.hit("a:calc", limit=2, window_seconds=60)
    second = limiter.hit("a:calc", limit=2, window_seconds=60)
    third = limiter.hit("a:calc", limit=2, window_seconds=60)

    assert first.allowed and second.allowed
    assert not third.allowed
    assert third.retry_after_seconds == 60


def test_limiter_clients_are_independent():
    limiter = InMemoryRateLimiter(max_keys=8)
    assert limiter.hit("one:calc", limit=1, window_seconds=60).allowed
    assert limiter.hit("two:calc", limit=1, window_seconds=60).allowed
    assert not limiter.hit("one:calc", limit=1, window_seconds=60).allowed
    assert not limiter.hit("two:calc", limit=1, window_seconds=60).allowed


def test_limiter_expires_old_hits(monkeypatch):
    clock = {"now": 0.0}
    limiter = InMemoryRateLimiter(max_keys=8, clock=lambda: clock["now"])
    assert limiter.hit("a:calc", limit=1, window_seconds=10).allowed
    assert not limiter.hit("a:calc", limit=1, window_seconds=10).allowed

    clock["now"] = 11.0
    assert limiter.hit("a:calc", limit=1, window_seconds=10).allowed


def test_limiter_key_set_is_bounded():
    limiter = InMemoryRateLimiter(max_keys=2)
    assert limiter.hit("a:calc", limit=1, window_seconds=60).allowed
    assert limiter.hit("b:calc", limit=1, window_seconds=60).allowed
    assert limiter.key_count == 2
    assert limiter.hit("c:calc", limit=1, window_seconds=60).allowed
    assert limiter.key_count == 2
    # LRU key "a" was evicted; it gets a fresh window.
    assert limiter.hit("a:calc", limit=1, window_seconds=60).allowed


def test_analyze_under_limit_succeeds(monkeypatch):
    client = _client(_settings(analyze_limit=2))
    monkeypatch.setattr(
        "api.transcripts.process_transcript",
        lambda path, **kwargs: _credit_selection_result(),
    )

    first = client.post("/api/transcripts/analyze", files=_pdf_files())
    second = client.post("/api/transcripts/analyze", files=_pdf_files())

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.headers.get("cache-control") == "no-store"


def test_analyze_over_limit_returns_429(monkeypatch):
    client = _client(_settings(analyze_limit=2, window_seconds=60))
    monkeypatch.setattr(
        "api.transcripts.process_transcript",
        lambda path, **kwargs: _credit_selection_result(),
    )

    client.post("/api/transcripts/analyze", files=_pdf_files())
    client.post("/api/transcripts/analyze", files=_pdf_files())
    blocked = client.post("/api/transcripts/analyze", files=_pdf_files())

    assert blocked.status_code == 429
    assert blocked.json() == {"detail": RATE_LIMIT_DETAIL}
    assert blocked.headers.get("retry-after") == "60"
    assert blocked.headers.get("cache-control") == "no-store"


def test_calculation_endpoint_is_rate_limited():
    client = _client(_settings(calculation_limit=2, window_seconds=45))
    payload = _summary_payload()

    assert client.post("/api/academic/summary", json=payload).status_code == 200
    assert client.post("/api/academic/summary", json=payload).status_code == 200
    blocked = client.post("/api/academic/summary", json=payload)

    assert blocked.status_code == 429
    assert blocked.json()["detail"] == RATE_LIMIT_DETAIL
    assert blocked.headers.get("retry-after") == "45"


def test_analyze_and_calculation_buckets_are_separate(monkeypatch):
    client = _client(_settings(analyze_limit=1, calculation_limit=1))
    monkeypatch.setattr(
        "api.transcripts.process_transcript",
        lambda path, **kwargs: _credit_selection_result(),
    )

    assert client.post("/api/transcripts/analyze", files=_pdf_files()).status_code == 200
    assert client.post("/api/academic/summary", json=_summary_payload()).status_code == 200
    assert client.post("/api/transcripts/analyze", files=_pdf_files()).status_code == 429
    assert client.post("/api/academic/summary", json=_summary_payload()).status_code == 429


def test_different_clients_do_not_share_limits():
    settings = _settings(calculation_limit=1)
    app = create_app(settings)
    one = TestClient(app, client=("10.0.0.1", 50000))
    two = TestClient(app, client=("10.0.0.2", 50000))
    payload = _summary_payload()

    assert one.post("/api/academic/summary", json=payload).status_code == 200
    assert two.post("/api/academic/summary", json=payload).status_code == 200
    assert one.post("/api/academic/summary", json=payload).status_code == 429
    assert two.post("/api/academic/summary", json=payload).status_code == 429


def test_spoofed_forwarded_for_does_not_bypass_limit_by_default():
    client = _client(_settings(calculation_limit=1, trust_proxy=False))
    payload = _summary_payload()

    first = client.post(
        "/api/academic/summary",
        json=payload,
        headers={"X-Forwarded-For": "203.0.113.10"},
    )
    second = client.post(
        "/api/academic/summary",
        json=payload,
        headers={"X-Forwarded-For": "203.0.113.11"},
    )

    assert first.status_code == 200
    assert second.status_code == 429


def test_trusted_proxy_uses_rightmost_forwarded_for():
    settings = _settings(calculation_limit=1, trust_proxy=True)
    client = _client(settings)
    payload = _summary_payload()

    first = client.post(
        "/api/academic/summary",
        json=payload,
        headers={"X-Forwarded-For": "203.0.113.10, 10.1.1.1"},
    )
    second = client.post(
        "/api/academic/summary",
        json=payload,
        headers={"X-Forwarded-For": "198.51.100.9, 10.1.1.1"},
    )
    other = client.post(
        "/api/academic/summary",
        json=payload,
        headers={"X-Forwarded-For": "198.51.100.9, 10.1.1.2"},
    )

    assert first.status_code == 200
    assert second.status_code == 429
    assert other.status_code == 200


def test_health_is_not_rate_limited():
    client = _client(_settings(calculation_limit=1, analyze_limit=1))
    for _ in range(8):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert response.headers.get("cache-control") != "no-store"


def test_academic_responses_are_not_storeable():
    client = _client()
    response = client.post("/api/academic/summary", json=_summary_payload())
    assert response.status_code == 200
    assert response.headers.get("cache-control") == "no-store"


def test_target_plan_uses_calculation_limit():
    client = _client(_settings(calculation_limit=1, window_seconds=30))
    payload = {
        "courses": [
            {
                "code": "CENG101",
                "name": "Programming",
                "gpa_credit": 4,
                "grade": "DD",
                "semester": "2024-2025 Güz",
            }
        ],
        "target_gpa": 2.0,
        "max_grade": "BB",
        "strategy": "min_courses",
    }
    assert client.post("/api/academic/target-plan", json=payload).status_code == 200
    blocked = client.post("/api/academic/target-plan", json=payload)
    assert blocked.status_code == 429
    assert blocked.headers.get("retry-after") == "30"
