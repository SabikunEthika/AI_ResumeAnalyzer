
import database
import pytest


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    test_database_path = tmp_path / "test_analyses.db"

    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        test_database_path,
    )

    database.init_db()
    return database


def test_save_and_get_analysis(test_db):
    test_db.save_analysis(
        "resume-1",
        "Sample resume text",
        ["Python", "Excel"],
    )

    result = test_db.get_analysis("resume-1")

    assert result is not None
    assert result["analysis_id"] == "resume-1"
    assert result["text"] == "Sample resume text"
    assert result["skills"] == ["Python", "Excel"]


def test_get_missing_analysis_returns_none(test_db):
    assert test_db.get_analysis("missing-id") is None


def test_save_and_get_match_result(test_db):
    test_db.save_analysis(
        "resume-2",
        "Resume text",
        ["Python"],
    )

    result = {
        "required_skills": ["Python"],
        "matched_skills": ["Python"],
        "missing_skills": [],
        "match_score": 100,
        "ai_analysis": {
            "overall_assessment": "Strong match",
            "strengths": ["Relevant experience"],
            "weaknesses": [],
            "suggestions": [],
            "requirement_assessments": [],
        },
    }

    test_db.save_match_result(
        "resume-2",
        "Python developer",
        result,
    )

    saved = test_db.get_match_result("resume-2")

    assert saved is not None
    assert saved["analysis_id"] == "resume-2"
    assert saved["job_description"] == "Python developer"
    assert saved["match_score"] == 100
    assert saved["ai_analysis"]["overall_assessment"] == "Strong match"
    assert "created_at" in saved


def test_saving_new_match_replaces_previous_match(test_db):
    test_db.save_analysis("resume-3", "Resume text", ["Python"])

    test_db.save_match_result(
        "resume-3",
        "First job",
        {"match_score": 50},
    )

    test_db.save_match_result(
        "resume-3",
        "Second job",
        {"match_score": 90},
    )

    saved = test_db.get_match_result("resume-3")

    assert saved["job_description"] == "Second job"
    assert saved["match_score"] == 90


def test_delete_analysis_also_deletes_match_result(test_db):
    test_db.save_analysis("resume-4", "Resume text", ["Python"])
    test_db.save_match_result(
        "resume-4",
        "Python developer",
        {"match_score": 80},
    )

    deleted = test_db.delete_analysis("resume-4")

    assert deleted is True
    assert test_db.get_analysis("resume-4") is None
    assert test_db.get_match_result("resume-4") is None


def test_delete_analysis_without_match_result(test_db):
    test_db.save_analysis("resume-5", "Resume text", ["Excel"])

    deleted = test_db.delete_analysis("resume-5")

    assert deleted is True
    assert test_db.get_analysis("resume-5") is None