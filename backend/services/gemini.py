"""Central Gemini configuration and safe error handling."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import TypeVar
from urllib.parse import urlsplit, urlunsplit

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError


logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-3.5-flash-lite"
DEFAULT_FALLBACK_MODEL = "gemini-3.5-flash"
DEFAULT_SECOND_FALLBACK_MODEL = "gemini-3.8-flash"
DEFAULT_TIMEOUT_MS = 30_000
RETRYABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504]
ModelT = TypeVar("ModelT", bound=BaseModel)


class GeminiServiceError(RuntimeError):
    """A safe, classified Gemini failure suitable for API handling."""

    def __init__(
        self,
        operation: str,
        category: str,
        status_code: int | None = None,
    ) -> None:
        super().__init__(f"Gemini {operation} failed: {category}")
        self.operation = operation
        self.category = category
        self.status_code = status_code


@dataclass(frozen=True)
class GeminiSettings:
    api_key: str | None
    model: str
    fallback_model: str | None
    second_fallback_model: str | None
    timeout_ms: int


def get_allowed_origins() -> list[str]:
    """Read explicitly configured browser origins for CORS."""
    configured_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
    origins = []
    for configured_origin in configured_origins.split(","):
        origin = _normalize_origin(configured_origin)
        if origin and origin not in origins:
            origins.append(origin)

    if origins:
        return origins

    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


def _normalize_origin(value: str) -> str | None:
    """Normalize a configured origin without accepting paths or wildcards."""
    origin = value.strip().strip('"\'')
    if not origin:
        return None

    parsed = urlsplit(origin)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        return None

    return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))


def get_local_development_origin_regex() -> str | None:
    """Allow Vite's alternate local ports, but never in production."""
    environment = os.getenv("APP_ENV", "development").strip().lower()
    if environment == "production":
        return None
    return r"^https?://(localhost|127\.0\.0\.1)(?::\d+)?$"


@lru_cache(maxsize=1)
def get_gemini_settings() -> GeminiSettings:
    # This is intentionally the only place that loads environment variables.
    load_dotenv()
    timeout_value = os.getenv("GEMINI_TIMEOUT_MS", str(DEFAULT_TIMEOUT_MS))

    try:
        timeout_ms = int(timeout_value)
    except ValueError:
        timeout_ms = DEFAULT_TIMEOUT_MS

    return GeminiSettings(
        api_key=os.getenv("GEMINI_API_KEY") or None,
        model=os.getenv("GEMINI_MODEL", DEFAULT_MODEL),
        fallback_model=os.getenv("GEMINI_FALLBACK_MODEL", DEFAULT_FALLBACK_MODEL)
        or None,
        second_fallback_model=os.getenv(
            "GEMINI_SECOND_FALLBACK_MODEL", DEFAULT_SECOND_FALLBACK_MODEL
        )
        or None,
        timeout_ms=max(1_000, timeout_ms),
    )


def is_gemini_configured() -> bool:
    return bool(get_gemini_settings().api_key)


@lru_cache(maxsize=1)
def get_gemini_client() -> genai.Client:
    settings = get_gemini_settings()
    if not settings.api_key:
        raise GeminiServiceError("configuration", "not_configured")

    return genai.Client(
        api_key=settings.api_key,
        http_options=types.HttpOptions(
            timeout=settings.timeout_ms,
            # The SDK does not retry unless retry_options is explicitly set.
            # Keep this bounded for an interactive user request.
            retry_options=types.HttpRetryOptions(
                attempts=3,
                initial_delay=1.0,
                max_delay=4.0,
                http_status_codes=RETRYABLE_STATUS_CODES,
            ),
        ),
    )


def _classify_error(error: Exception) -> tuple[str, int | None]:
    status_code = getattr(error, "code", None)
    if isinstance(status_code, bool) or not isinstance(status_code, int):
        status_code = None

    if isinstance(error, (httpx.TimeoutException, TimeoutError)):
        return "timeout", status_code
    if status_code in {401, 403}:
        return "authentication", status_code
    if status_code == 429:
        return "rate_limited", status_code
    if status_code is not None and status_code >= 500:
        return "unavailable", status_code
    return "request_failed", status_code


def generate_structured_content(
    *,
    client: genai.Client,
    prompt: str,
    schema: type[ModelT],
    operation: str,
) -> ModelT:
    """Call Gemini without logging sensitive prompt or response content."""
    settings = get_gemini_settings()

    def request(model: str):
        return client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )

    models = tuple(
        dict.fromkeys(
            model
            for model in (
                settings.model,
                settings.fallback_model,
                settings.second_fallback_model,
            )
            if model
        )
    )

    for index, model in enumerate(models):
        try:
            response = request(model)
            break
        except Exception as error:
            category, status_code = _classify_error(error)
            has_next_model = index < len(models) - 1

            if category == "unavailable" and has_next_model:
                logger.warning(
                    "Gemini model unavailable operation=%s status_code=%s; trying next fallback",
                    operation,
                    status_code,
                )
                continue

            logger.warning(
                "Gemini request failed operation=%s category=%s status_code=%s exception=%s",
                operation,
                category,
                status_code,
                type(error).__name__,
            )
            raise GeminiServiceError(operation, category, status_code) from error
    else:  # pragma: no cover - defensive; settings always includes a primary model.
        raise GeminiServiceError(operation, "not_configured")

    if not response.text:
        logger.warning("Gemini returned an empty response operation=%s", operation)
        raise GeminiServiceError(operation, "empty_response")

    try:
        return schema.model_validate_json(response.text)
    except ValidationError as error:
        logger.warning(
            "Gemini returned an invalid structured response operation=%s exception=%s",
            operation,
            type(error).__name__,
        )
        raise GeminiServiceError(operation, "invalid_response") from error
