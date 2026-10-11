
from types import SimpleNamespace

from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


def mock_valid_resume_pipeline(monkeypatch):
    resume_text = (
        "Alex Morgan\n"
        "Professional Summary\n"
        "Experienced professional with reporting skills.\n"
        "Education: Bachelor degree.\n"
        "Experience: Assistant, ABC Company, 2023-2025.\n"
        "Skills: Excel, communication, reporting."
    )

    monkeypatch.setattr(
        main,
        "extract_resume_text",
        lambda filename, file_bytes: resume_text,
    )
    monkeypatch.setattr(
        main,
        "validate_resume_document",
        lambda text: SimpleNamespace(
            is_resume=True,
            reason="Contains resume information.",
        ),
    )
    monkeypatch.setattr(
        main,
        "extract_skills",
        lambda text: ["Excel", "Communication"],
    )

    return resume_text


def mock_job_match(monkeypatch):
    result = {
        "required_skills": ["Excel"],
        "matched_skills": ["Excel"],
        "missing_skills": [],
        "match_score": 100,
        "ai_analysis": {
            "overall_assessment": "Good match for the position.",
            "strengths": ["Relevant experience"],
            "weaknesses": [],
            "suggestions": ["Add measurable achievements"],
            "requirement_assessments": [
                {
                    "title": "Excel",
                    "importance": "required",
                    "status": "supported",
                    "evidence": "Excel is listed in the resume.",
                    "explanation": "The resume supports this requirement.",
                }
            ],
        },
    }

    monkeypatch.setattr(
        main,
        "analyze_job_match",
        lambda *args, **kwargs: result,
    )

    return result


def mock_quality_analysis(monkeypatch):
    result = {
        "overall_score": 82,
        "summary": "A clear resume with room for improvement.",
        "strengths": ["Relevant experience"],
        "improvements": ["Add measurable achievements"],
        "section_reviews": [
            {
                "section": "Experience",
                "status": "Present",
                "feedback": "Add measurable results.",
            }
        ],
        "missing_information": ["Contact details"],
        "achievement_feedback": ["Quantify your impact."],
        "ats_score": 76,
        "ats_summary": "Generally readable resume text.",
        "ats_strengths": ["Clear section headings"],
        "ats_issues": ["Some dates may need clarification"],
        "ats_improvements": ["Use consistent date formatting"],
    }

    monkeypatch.setattr(
        main,
        "analyze_resume_quality",
        lambda *args, **kwargs: SimpleNamespace(
            model_dump=lambda: result
        ),
    )

    return result


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert "message" in response.json()


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_rejects_unsupported_file_type():
    response = client.post(
        "/analyze",
        files={
            "file": (
                "notes.txt",
                b"This is a text file.",
                "text/plain",
            )
        },
        data={"include_quality": "true"},
    )

    assert response.status_code == 400
    assert "Only PDF and DOCX" in response.json()["detail"]


def test_analyze_rejects_request_without_analysis_options():
    response = client.post(
        "/analyze",
        files={
            "file": (
                "resume.pdf",
                b"Fake PDF content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert "Select an analysis" in response.json()["detail"]


def test_analyze_rejects_empty_file(monkeypatch):
    def reject_empty_file(filename, file_bytes):
        raise ValueError("The uploaded file is empty.")

    monkeypatch.setattr(
        main,
        "extract_resume_text",
        reject_empty_file,
    )

    response = client.post(
        "/analyze",
        files={
            "file": (
                "resume.pdf",
                b"",
                "application/pdf",
            )
        },
        data={"include_quality": "true"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "The uploaded file is empty."


def test_analyze_rejects_file_over_5_mb():
    response = client.post(
        "/analyze",
        files={
            "file": (
                "resume.pdf",
                b"x" * (5 * 1024 * 1024 + 1),
                "application/pdf",
            )
        },
        data={"include_quality": "true"},
    )

    assert response.status_code == 413
    assert "Maximum allowed size is 5 MB" in response.json()["detail"]


def test_analyze_rejects_non_resume_document(monkeypatch):
    monkeypatch.setattr(
        main,
        "extract_resume_text",
        lambda filename, file_bytes: "A research paper about science.",
    )
    monkeypatch.setattr(
        main,
        "validate_resume_document",
        lambda text: SimpleNamespace(
            is_resume=False,
            reason="This appears to be a research paper.",
        ),
    )

    response = client.post(
        "/analyze",
        files={
            "file": (
                "paper.pdf",
                b"Fake PDF content",
                "application/pdf",
            )
        },
        data={"include_quality": "true"},
    )

    assert response.status_code == 400
    assert "does not appear to be a resume" in response.json()["detail"]


def test_quality_only_analysis(monkeypatch):
    mock_valid_resume_pipeline(monkeypatch)
    expected = mock_quality_analysis(monkeypatch)

    response = client.post(
        "/analyze",
        files={
            "file": (
                "resume.docx",
                b"Mock DOCX content",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        data={"include_quality": "true"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["filename"] == "resume.docx"
    assert data["skills"] == ["Excel", "Communication"]
    assert data["quality_analysis"]["overall_score"] == expected["overall_score"]
    assert data["quality_analysis"]["ats_score"] == expected["ats_score"]
    assert data["job_match"] is None
    assert "analysis_id" not in data


def test_job_match_only_analysis(monkeypatch):
    mock_valid_resume_pipeline(monkeypatch)
    expected = mock_job_match(monkeypatch)

    response = client.post(
        "/analyze",
        files={
            "file": (
                "resume.pdf",
                b"Mock PDF content",
                "application/pdf",
            )
        },
        data={
            "job_description": "We need an experienced Excel professional.",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["job_match"]["match_score"] == expected["match_score"]
    assert data["job_match"]["matched_skills"] == ["Excel"]
    assert data["quality_analysis"] is None
    assert "analysis_id" not in data


def test_combined_analysis(monkeypatch):
    mock_valid_resume_pipeline(monkeypatch)
    mock_job_match(monkeypatch)
    mock_quality_analysis(monkeypatch)

    response = client.post(
        "/analyze",
        files={
            "file": (
                "resume.pdf",
                b"Mock PDF content",
                "application/pdf",
            )
        },
        data={
            "include_quality": "true",
            "job_description": "We need an experienced Excel professional.",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["job_match"] is not None
    assert data["quality_analysis"] is not None
    assert "analysis_id" not in data


def test_job_match_returns_503_when_ai_fails(monkeypatch):
    mock_valid_resume_pipeline(monkeypatch)

    def fail_analysis(*args, **kwargs):
        raise RuntimeError("Simulated AI failure")

    monkeypatch.setattr(main, "analyze_job_match", fail_analysis)

    response = client.post(
        "/analyze",
        files={
            "file": (
                "resume.pdf",
                b"Mock PDF content",
                "application/pdf",
            )
        },
        data={
            "job_description": "We need an experienced Excel professional.",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Job matching failed. Please try again later."
    )


def test_quality_analysis_returns_503_when_ai_fails(monkeypatch):
    mock_valid_resume_pipeline(monkeypatch)

    def fail_analysis(*args, **kwargs):
        raise RuntimeError("Simulated AI failure")

    monkeypatch.setattr(
        main,
        "analyze_resume_quality",
        fail_analysis,
    )

    response = client.post(
        "/analyze",
        files={
            "file": (
                "resume.pdf",
                b"Mock PDF content",
                "application/pdf",
            )
        },
        data={"include_quality": "true"},
    )

    assert response.status_code == 503
    assert "Unable to analyze resume quality" in response.json()["detail"]


def test_resume_validation_failure_returns_503(monkeypatch):
    monkeypatch.setattr(
        main,
        "extract_resume_text",
        lambda filename, file_bytes: "Sample resume text.",
    )

    def fail_validation(text):
        raise RuntimeError("Simulated validation failure")

    monkeypatch.setattr(
        main,
        "validate_resume_document",
        fail_validation,
    )

    response = client.post(
        "/analyze",
        files={
            "file": (
                "resume.pdf",
                b"Mock PDF content",
                "application/pdf",
            )
        },
        data={"include_quality": "true"},
    )

    assert response.status_code == 503
    assert "Unable to verify this document" in response.json()["detail"]
