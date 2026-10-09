
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == (
        "AI Resume Analyzer Backend is running!"
    )


def test_upload_rejects_unsupported_file_type():
    response = client.post(
        "/resume/upload",
        files={
            "file": (
                "notes.txt",
                b"This is a text file.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert "Only PDF and DOCX" in response.json()["detail"]


def test_get_analysis_returns_404_for_unknown_id(monkeypatch):
    monkeypatch.setattr(main, "get_analysis", lambda analysis_id: None)

    response = client.get("/analysis/unknown-id")

    assert response.status_code == 404
    assert response.json()["detail"] == "Analysis not found."


def test_delete_returns_404_for_unknown_id(monkeypatch):
    monkeypatch.setattr(main, "delete_analysis", lambda analysis_id: False)

    response = client.delete("/analysis/unknown-id")

    assert response.status_code == 404
    assert response.json()["detail"] == "Analysis not found."


def test_job_match_returns_404_for_unknown_id(monkeypatch):
    monkeypatch.setattr(main, "get_analysis", lambda analysis_id: None)

    response = client.post(
        "/job/match",
        json={
            "analysis_id": "unknown-id",
            "text": "We are looking for an office assistant.",
        },
    )

    assert response.status_code == 404
    assert "Invalid analysis ID" in response.json()["detail"]


def test_job_match_rejects_empty_description():
    response = client.post(
        "/job/match",
        json={
            "analysis_id": "test-id",
            "text": "   ",
        },
    )

    assert response.status_code == 422


def test_quality_analysis_returns_404_for_unknown_id(monkeypatch):
    monkeypatch.setattr(main, "get_analysis", lambda analysis_id: None)

    response = client.post(
        "/resume/quality",
        json={"analysis_id": "unknown-id"},
    )

    assert response.status_code == 404
    assert "Resume not found" in response.json()["detail"]


def test_job_match_returns_503_when_ai_fails(monkeypatch):
    monkeypatch.setattr(
        main,
        "get_analysis",
        lambda analysis_id: {
            "text": "Sample resume text",
            "skills": ["Python"],
        },
    )

    def fake_analyze(*args, **kwargs):
        raise RuntimeError("Simulated AI failure")

    monkeypatch.setattr(main, "analyze_job_match", fake_analyze)

    response = client.post(
        "/job/match",
        json={
            "analysis_id": "test-id",
            "text": "We are looking for a Python developer.",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "AI analysis failed. Please try again later."
    )


def test_quality_analysis_returns_503_when_ai_fails(monkeypatch):
    monkeypatch.setattr(
        main,
        "get_analysis",
        lambda analysis_id: {
            "text": "Sample resume text",
            "skills": ["Python"],
        },
    )

    def fake_analyze(*args, **kwargs):
        raise RuntimeError("Simulated AI failure")

    monkeypatch.setattr(
        main,
        "analyze_resume_quality",
        fake_analyze,
    )

    response = client.post(
        "/resume/quality",
        json={"analysis_id": "test-id"},
    )

    assert response.status_code == 503
    assert "Unable to analyze resume quality" in response.json()["detail"]