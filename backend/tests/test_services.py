
import pytest

from services.skill_analyzer import extract_skills
from services.job_matcher import calculate_match
from services.job_description_validator import validate_job_description


def test_extract_skills():
    text = "I have experience with Python, React, Git, and MySQL."

    skills = extract_skills(text)

    assert "Python" in skills
    assert "React" in skills
    assert "Git" in skills
    assert "MySQL" in skills


def test_extract_skills_with_no_matching_skills():
    skills = extract_skills("I enjoy learning and solving problems.")

    assert skills == []


def test_calculate_match():
    resume_skills = ["Python", "React", "Git"]
    required_skills = ["Python", "React", "MySQL"]

    result = calculate_match(resume_skills, required_skills)

    assert result["matched_skills"] == ["Python", "React"]
    assert result["missing_skills"] == ["MySQL"]
    assert result["match_score"] == 67


def test_calculate_match_with_no_required_skills():
    result = calculate_match(["Python"], [])

    assert result["matched_skills"] == []
    assert result["missing_skills"] == []
    assert result["match_score"] == 0


def test_validate_valid_job_description():
    text = (
        "We are looking for an office assistant. "
        "The candidate will organize documents, "
        "communicate with the team, and support the manager."
    )

    assert validate_job_description(text) == text


def test_validate_short_job_description():
    with pytest.raises(ValueError):
        validate_job_description("hello")