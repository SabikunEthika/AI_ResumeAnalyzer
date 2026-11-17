
from types import SimpleNamespace

from services import resume_validator


class FakeModels:
    def __init__(self, result):
        self.result = result

    def generate_content(self, **kwargs):
        return SimpleNamespace(text=self.result)


class FakeClient:
    def __init__(self, result):
        self.models = FakeModels(result)


def test_short_document_is_rejected():
    result = resume_validator.validate_resume_document("Too short")

    assert result.is_resume is False
    assert "too little readable text" in result.reason.lower()


def test_valid_resume_classification(monkeypatch):
    monkeypatch.setattr(
        resume_validator,
        "client",
        FakeClient(
            '{"is_resume": true, "reason": "Contains career and education history."}'
        ),
    )

    text = """
    Alex Morgan
    Professional Summary
    Experienced finance assistant with experience in reporting.
    Education: Bachelor of Business Administration.
    Experience: Finance Assistant, ABC Company, 2023-2025.
    Skills: Excel, financial reporting, communication.
    """

    result = resume_validator.validate_resume_document(text)

    assert result.is_resume is True


def test_research_paper_classification(monkeypatch):
    monkeypatch.setattr(
        resume_validator,
        "client",
        FakeClient(
            '{"is_resume": false, "reason": "This is a research paper."}'
        ),
    )

    text = (
        "Abstract: This research paper proposes a new method for image "
        "classification. The introduction discusses prior work, the "
        "methodology explains the experiments, and the results compare "
        "the proposed model with several existing approaches. "
    ) * 3

    result = resume_validator.validate_resume_document(text)

    assert result.is_resume is False


def test_job_description_classification(monkeypatch):
    monkeypatch.setattr(
        resume_validator,
        "client",
        FakeClient(
            '{"is_resume": false, "reason": "This is a job description."}'
        ),
    )

    text = (
        "We are hiring a marketing assistant. Responsibilities include "
        "campaign planning, market research, preparing reports, and "
        "supporting the marketing team. Candidates should have strong "
        "communication skills and a relevant degree. "
    ) * 3

    result = resume_validator.validate_resume_document(text)

    assert result.is_resume is False