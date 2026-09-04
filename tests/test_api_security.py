from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import GENERIC_SERVER_ERROR, create_app
from api.rate_limit import RateLimitSettings
from api.security_headers import BASE_SECURITY_HEADERS
from api.settings import (
    enable_api_docs_from_env,
    enable_hsts_from_env,
    parse_cors_origins,
)


def test_parse_cors_origins_defaults_and_rejects_wildcard():
    assert parse_cors_origins(None) == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    assert parse_cors_origins("  ") == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    assert parse_cors_origins("*") == []
    assert parse_cors_origins("*,https://app.example") == ["https://app.example"]
    assert parse_cors_origins(
        "http://localhost:3000, http://127.0.0.1:3000"
    ) == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def test_docs_and_hsts_env_defaults(monkeypatch):
    monkeypatch.delenv("GRADEPILOT_ENABLE_API_DOCS", raising=False)
    monkeypatch.delenv("GRADEPILOT_ENABLE_HSTS", raising=False)
    monkeypatch.delenv("GRADEPILOT_TRUST_PROXY", raising=False)
    assert enable_api_docs_from_env() is True
    assert enable_hsts_from_env() is False
    assert RateLimitSettings.from_env().trust_proxy is False

    monkeypatch.setenv("GRADEPILOT_ENABLE_API_DOCS", "0")
    monkeypatch.setenv("GRADEPILOT_ENABLE_HSTS", "1")
    monkeypatch.setenv("GRADEPILOT_TRUST_PROXY", "true")
    assert enable_api_docs_from_env() is False
    assert enable_hsts_from_env() is True
    assert RateLimitSettings.from_env().trust_proxy is True


def test_allowed_origin_receives_cors_header():
    app = create_app(cors_origins=["http://localhost:3000"])
    client = TestClient(app)
    response = client.post(
        "/api/academic/summary",
        json={"courses": []},
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 400
    assert (
        response.headers.get("access-control-allow-origin")
        == "http://localhost:3000"
    )


def test_disallowed_origin_is_not_reflected():
    app = create_app(cors_origins=["http://localhost:3000"])
    client = TestClient(app)
    response = client.post(
        "/api/academic/summary",
        json={"courses": []},
        headers={"Origin": "https://evil.example"},
    )
    assert response.headers.get("access-control-allow-origin") != "https://evil.example"
    assert "https://evil.example" not in (
        response.headers.get("access-control-allow-origin") or ""
    )


def test_cors_preflight_allows_json_content_type_only_for_listed_origin():
    app = create_app(cors_origins=["http://localhost:3000"])
    client = TestClient(app)
    allowed = client.options(
        "/api/academic/summary",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    denied = client.options(
        "/api/academic/summary",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert allowed.status_code == 200
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert denied.headers.get("access-control-allow-origin") != "https://evil.example"


def test_production_docs_can_be_disabled():
    app = create_app(enable_api_docs=False)
    client = TestClient(app)
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_docs_enabled_by_default():
    client = TestClient(create_app())
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 200


def test_security_headers_present_and_hsts_off_by_default():
    client = TestClient(create_app(enable_hsts=False))
    response = client.get("/health")
    for name, value in BASE_SECURITY_HEADERS.items():
        assert response.headers.get(name) == value
    assert "strict-transport-security" not in {
        key.lower() for key in response.headers
    }


def test_hsts_only_when_enabled():
    client = TestClient(create_app(enable_hsts=True))
    response = client.get("/health")
    assert response.headers.get("strict-transport-security") == (
        "max-age=31536000; includeSubDomains"
    )


def test_api_responses_remain_no_store():
    client = TestClient(create_app())
    response = client.post("/api/academic/summary", json={"courses": []})
    assert response.status_code == 400
    assert response.headers.get("cache-control") == "no-store"
    assert "application/json" in (response.headers.get("content-type") or "")


def test_unhandled_error_does_not_leak_internal_details():
    app = create_app()

    @app.get("/__test-boom")
    def boom() -> None:
        raise RuntimeError(r"secret C:\Users\internal\transcript.pdf GPA=3.14")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/__test-boom")
    assert response.status_code == 500
    body = response.json()
    assert body == {"detail": GENERIC_SERVER_ERROR}
    serialized = str(body).lower()
    assert "traceback" not in serialized
    assert "runtimeerror" not in serialized
    assert "transcript.pdf" not in serialized
    assert "3.14" not in serialized
    assert ":\\" not in str(body)
    assert response.headers.get("cache-control") == "no-store"


def test_existing_4xx_detail_is_unchanged():
    client = TestClient(create_app())
    response = client.post("/api/academic/summary", json={"courses": []})
    assert response.status_code == 400
    assert "No courses were provided" in response.json()["detail"]
    assert "traceback" not in str(response.json()).lower()
