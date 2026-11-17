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


class ProviderError(Exception):
    code = 503


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


def test_configured_cors_origin_normalizes_slashes_and_quotes(monkeypatch):
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        ' "https://frontend-delta-one-f7arl0zj17.vercel.app/", '
        "https://frontend-delta-one-f7arl0zj17.vercel.app",
    )

    assert gemini.get_allowed_origins() == [
        "https://frontend-delta-one-f7arl0zj17.vercel.app"
    ]


def test_gemini_client_retries_transient_provider_errors(monkeypatch):
    captured_options = {}

    class CapturingClient:
        def __init__(self, **kwargs):
            captured_options.update(kwargs)

    monkeypatch.setattr(
        gemini,
        "get_gemini_settings",
        lambda: gemini.GeminiSettings(
            "test-key", "test-model", None, None, 30_000
        ),
    )
    monkeypatch.setattr(gemini.genai, "Client", CapturingClient)
    gemini.get_gemini_client.cache_clear()

    gemini.get_gemini_client()

    retry_options = captured_options["http_options"].retry_options
    assert retry_options.attempts == 3
    assert retry_options.http_status_codes == [408, 429, 500, 502, 503, 504]
    gemini.get_gemini_client.cache_clear()


def test_uses_fallback_model_after_primary_503(monkeypatch):
    calls = []

    class FallbackModels:
        def generate_content(self, **kwargs):
            calls.append(kwargs["model"])
            if len(calls) == 1:
                raise ProviderError()
            return SimpleNamespace(
                text='{"is_resume": true, "reason": "Resume content found."}'
            )

    monkeypatch.setattr(
        gemini,
        "get_gemini_settings",
        lambda: gemini.GeminiSettings(
            "test-key", "primary-model", "fallback-model", None, 30_000
        ),
    )

    result = gemini.generate_structured_content(
        client=SimpleNamespace(models=FallbackModels()),
        prompt="Resume text",
        schema=resume_validator.ResumeValidation,
        operation="resume_validation",
    )

    assert result.is_resume is True
    assert calls == ["primary-model", "fallback-model"]


def test_uses_second_fallback_after_two_provider_503s(monkeypatch):
    calls = []

    class FallbackModels:
        def generate_content(self, **kwargs):
            calls.append(kwargs["model"])
            if len(calls) < 3:
                raise ProviderError()
            return SimpleNamespace(
                text='{"is_resume": true, "reason": "Resume content found."}'
            )

    monkeypatch.setattr(
        gemini,
        "get_gemini_settings",
        lambda: gemini.GeminiSettings(
            "test-key",
            "primary-model",
            "fallback-model",
            "second-fallback-model",
            30_000,
        ),
    )

    result = gemini.generate_structured_content(
        client=SimpleNamespace(models=FallbackModels()),
        prompt="Resume text",
        schema=resume_validator.ResumeValidation,
        operation="resume_validation",
    )

    assert result.is_resume is True
    assert calls == [
        "primary-model",
        "fallback-model",
        "second-fallback-model",
    ]
