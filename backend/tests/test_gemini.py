from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import main
from services.gemini import GeminiServiceError
from services import gemini, resume_validator


class FakeModels:
    def __init__(self, result):
        self.result = result

    def generate_content(self, **kwargs):
        return SimpleNamespace(text=self.result)


class FakeClient:
    def __init__(self, result):
        self.models = FakeModels(result)


client = TestClient(main.app)


def test_invalid_gemini_json_is_classified_without_exposing_content(monkeypatch):
    monkeypatch.setattr(resume_validator, "client", FakeClient("{}"))

    with pytest.raises(GeminiServiceError) as error:
        resume_validator.validate_resume_document("A" * 120)

    assert error.value.category == "invalid_response"


def test_rate_limited_validation_returns_safe_429(monkeypatch):
    monkeypatch.setattr(
        main,
        "extract_resume_text",
        lambda filename, file_bytes: "A" * 120,
    )

    def raise_rate_limit(text):
        raise GeminiServiceError("resume_validation", "rate_limited", 429)

    monkeypatch.setattr(main, "validate_resume_document", raise_rate_limit)

    response = client.post(
        "/analyze",
        files={"file": ("resume.pdf", b"PDF", "application/pdf")},
        data={"include_quality": "true"},
    )

    assert response.status_code == 429
    assert response.json()["detail"] == (
        "AI analysis is temporarily busy. Please try again shortly."
    )


def test_readiness_reports_missing_ai_configuration(monkeypatch):
    monkeypatch.setattr(main, "is_gemini_configured", lambda: False)

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == "AI analysis service is not configured."


def test_development_cors_allows_vites_alternate_local_port():
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:5174"},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5174"


def test_gemini_client_retries_transient_provider_errors(monkeypatch):
    captured_options = {}

    class CapturingClient:
        def __init__(self, **kwargs):
            captured_options.update(kwargs)

    monkeypatch.setattr(
        gemini,
        "get_gemini_settings",
        lambda: gemini.GeminiSettings("test-key", "test-model", 30_000),
    )
    monkeypatch.setattr(gemini.genai, "Client", CapturingClient)
    gemini.get_gemini_client.cache_clear()

    gemini.get_gemini_client()

    retry_options = captured_options["http_options"].retry_options
    assert retry_options.attempts == 3
    assert retry_options.http_status_codes == [408, 429, 500, 502, 503, 504]
    gemini.get_gemini_client.cache_clear()
