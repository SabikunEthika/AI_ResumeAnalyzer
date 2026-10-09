
from types import SimpleNamespace

from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


def test_resume_upload_saves_valid_resume(monkeypatch):
    saved = {}

    monkeypatch.setattr(
        main,
        "extract_resume_text",
        lambda filename, file_bytes: (
            "Alex Morgan\n"
            "Professional Summary\n"
            "Experienced finance assistant with reporting skills.\n"
            "Education: Bachelor of Business Administration.\n"
            "Experience: Finance Assistant, ABC Company, 2023-2025.\n"
            "Skills: Excel, financial reporting, communication."
        ),
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
        lambda text: ["Excel"],
    )
    monkeypatch.setattr(
        main,
        "save_analysis",
        lambda analysis_id, text, skills: saved.update(
            {
                "analysis_id": analysis_id,
                "text": text,
                "skills": skills,
            }
        ),
    )

    response = client.post(
        "/resume/upload",
        files={
            "file": (
                "resume.pdf",
                b"fake PDF bytes",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "resume.pdf"
    assert data["skills"] == ["Excel"]
    assert data["analysis_id"] == saved["analysis_id"]
    assert saved["skills"] == ["Excel"]


def test_job_match_saves_and_returns_result(monkeypatch):
    stored = {}
    ai_result = {
        "overall_assessment": "Good match for the position.",
        "strengths": ["Relevant Python experience"],
        "weaknesses": [],
        "suggestions": ["Add measurable achievements"],
        "requirement_assessments": [
            {
                "title": "Python",
                "importance": "required",
                "status": "supported",
                "evidence": "Python experience listed.",
                "explanation": "The resume supports this requirement.",
            }
        ],
    }

    match_result = {
        "required_skills": ["Python"],
        "matched_skills": ["Python"],
        "missing_skills": [],
        "match_score": 100,
        "ai_analysis": SimpleNamespace(
            model_dump=lambda: ai_result
        ),
    }

    monkeypatch.setattr(
        main,
        "get_analysis",
        lambda analysis_id: {
            "text": "Resume with Python experience.",
            "skills": ["Python"],
        },
    )
    monkeypatch.setattr(
        main,
        "analyze_job_match",
        lambda resume_text, skills, job_text: match_result,
    )

    def fake_save(analysis_id, job_description, result):
        stored.update(
            {
                "analysis_id": analysis_id,
                "job_description": job_description,
                **result,
            }
        )

    monkeypatch.setattr(main, "save_match_result", fake_save)
    monkeypatch.setattr(
        main,
        "get_match_result",
        lambda analysis_id: {
            **stored,
            "created_at": "2026-10-10T12:00:00",
        } if stored else None,
    )

    response = client.post(
        "/job/match",
        json={
            "analysis_id": "test-resume-id",
            "text": "We need a Python developer.",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["analysis_id"] == "test-resume-id"
    assert data["match_score"] == 100
    assert data["matched_skills"] == ["Python"]
    assert data["ai_analysis"]["requirement_assessments"][0]["status"] == "supported"
    assert stored["job_description"] == "We need a Python developer."

    saved_response = client.get(
        "/analysis/test-resume-id/match-result"
    )

    assert saved_response.status_code == 200
    saved_data = saved_response.json()
    assert saved_data["match_score"] == 100
    assert saved_data["job_description"] == "We need a Python developer."
    assert saved_data["created_at"] == "2026-10-10T12:00:00"


def test_quality_analysis_returns_expected_scores(monkeypatch):
    quality_result = {
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
        "get_analysis",
        lambda analysis_id: {
            "text": "Sample resume text.",
            "skills": ["Python"],
        },
    )
    monkeypatch.setattr(
        main,
        "analyze_resume_quality",
        lambda text: SimpleNamespace(
            model_dump=lambda: quality_result
        ),
    )

    response = client.post(
        "/resume/quality",
        json={"analysis_id": "test-resume-id"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["analysis_id"] == "test-resume-id"
    assert data["quality_analysis"]["overall_score"] == 82
    assert data["quality_analysis"]["ats_score"] == 76
    assert "strengths" in data["quality_analysis"]
    assert "ats_issues" in data["quality_analysis"]
    assert "section_reviews" in data["quality_analysis"]