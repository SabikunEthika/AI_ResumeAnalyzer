
from types import SimpleNamespace

from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


def setup_valid_resume(monkeypatch):
    resume_text = (
        "Alex Morgan\n"
        "Professional Summary\n"
        "Experienced professional with reporting skills.\n"
        "Education: Bachelor of Business Administration.\n"
        "Experience: Finance Assistant, ABC Company, 2023-2025.\n"
        "Skills: Excel, financial reporting, communication."
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
        lambda text: ["Excel", "Financial Reporting"],
    )

    return resume_text


def setup_job_match(monkeypatch):
    result = {
        "required_skills": ["Excel", "Financial Reporting"],
        "matched_skills": ["Excel"],
        "missing_skills": ["Financial Reporting"],
        "match_score": 75,
        "ai_analysis": {
            "overall_assessment": "A reasonable match for the position.",
            "strengths": ["Excel experience"],
            "weaknesses": ["Limited reporting evidence"],
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


def setup_quality_analysis(monkeypatch):
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
        lambda text: SimpleNamespace(
            model_dump=lambda: result
        ),
    )

    return result


def test_job_match_returns_result_without_persistence(monkeypatch):
    setup_valid_resume(monkeypatch)
    expected = setup_job_match(monkeypatch)

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
            "job_description": "We need an experienced Excel professional."
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "resume.pdf"
    assert data["skills"] == ["Excel", "Financial Reporting"]
    assert data["job_match"]["match_score"] == expected["match_score"]
    assert data["job_match"]["matched_skills"] == ["Excel"]
    assert data["job_match"]["ai_analysis"]["requirement_assessments"][0][
        "status"
    ] == "supported"
    assert data["quality_analysis"] is None
    assert "analysis_id" not in data


def test_quality_analysis_returns_scores_without_persistence(monkeypatch):
    setup_valid_resume(monkeypatch)
    expected = setup_quality_analysis(monkeypatch)

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
    assert data["quality_analysis"]["overall_score"] == expected["overall_score"]
    assert data["quality_analysis"]["ats_score"] == expected["ats_score"]
    assert data["quality_analysis"]["strengths"] == expected["strengths"]
    assert data["quality_analysis"]["section_reviews"][0]["section"] == "Experience"
    assert data["job_match"] is None
    assert "analysis_id" not in data


def test_combined_analysis_returns_both_results_without_persistence(
    monkeypatch,
):
    setup_valid_resume(monkeypatch)
    setup_job_match(monkeypatch)
    setup_quality_analysis(monkeypatch)

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
    assert data["job_match"]["match_score"] == 75
    assert data["quality_analysis"]["overall_score"] == 82
    assert "analysis_id" not in data


def test_old_database_dependent_endpoints_are_not_available():
    upload_response = client.post(
        "/resume/upload",
        files={
            "file": (
                "resume.pdf",
                b"Mock PDF content",
                "application/pdf",
            )
        },
    )

    match_response = client.post(
        "/job/match",
        json={
            "analysis_id": "test-resume-id",
            "text": "We need an Excel professional.",
        },
    )

    quality_response = client.post(
        "/resume/quality",
        json={"analysis_id": "test-resume-id"},
    )

    saved_result_response = client.get(
        "/analysis/test-resume-id/match-result"
    )

    assert upload_response.status_code == 404
    assert match_response.status_code == 404
    assert quality_response.status_code == 404
    assert saved_result_response.status_code == 404
