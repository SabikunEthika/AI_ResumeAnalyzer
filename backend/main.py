
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.resume_parser import extract_resume_text
from services.skill_analyzer import extract_skills
from services.analysis_service import analyze_job_match
from services.resume_validator import validate_resume_document
from services.resume_quality_analyzer import analyze_resume_quality
from services.gemini import (
    GeminiServiceError,
    get_allowed_origins,
    get_local_development_origin_regex,
    is_gemini_configured,
)


app = FastAPI(title="ResumeOrbit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_origin_regex=get_local_development_origin_regex(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

MAX_FILE_SIZE = 5 * 1024 * 1024


class RequirementAssessmentResponse(BaseModel):
    title: str
    importance: Literal["required", "preferred"]
    status: Literal["supported", "partial", "not_found"]
    evidence: str
    explanation: str


class AIAnalysisResponse(BaseModel):
    overall_assessment: str
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]
    requirement_assessments: list[RequirementAssessmentResponse]


class JobMatchResult(BaseModel):
    required_skills: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    match_score: int | None
    ai_analysis: AIAnalysisResponse


class ResumeSectionReview(BaseModel):
    section: str
    status: str
    feedback: str


class ResumeQualityResult(BaseModel):
    overall_score: int
    summary: str
    strengths: list[str]
    improvements: list[str]
    section_reviews: list[ResumeSectionReview]
    missing_information: list[str]
    achievement_feedback: list[str]
    ats_score: int
    ats_summary: str
    ats_strengths: list[str]
    ats_issues: list[str]
    ats_improvements: list[str]


class AnalyzeResponse(BaseModel):
    filename: str
    skills: list[str]
    job_match: JobMatchResult | None = None
    quality_analysis: ResumeQualityResult | None = None


@app.get("/")
def home():
    return {"message": "ResumeOrbit API is running."}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/ready")
def readiness():
    """Expose configuration readiness without initializing or exposing Gemini."""
    if not is_gemini_configured():
        raise HTTPException(
            status_code=503,
            detail="AI analysis service is not configured.",
        )
    return {"status": "ready"}


def gemini_error_response(error: GeminiServiceError) -> HTTPException:
    """Translate classified provider failures into safe API responses."""
    if error.category == "rate_limited":
        return HTTPException(
            status_code=429,
            detail="AI analysis is temporarily busy. Please try again shortly.",
        )
    if error.category == "timeout":
        return HTTPException(
            status_code=504,
            detail="AI analysis timed out. Please try again.",
        )
    if error.category == "invalid_response":
        return HTTPException(
            status_code=502,
            detail="AI analysis returned an invalid response. Please try again.",
        )
    return HTTPException(
        status_code=503,
        detail="AI analysis is temporarily unavailable. Please try again later.",
    )


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    file: UploadFile = File(...),
    include_quality: bool = Form(False),
    job_description: str | None = Form(None),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file was provided.",
        )

    filename = file.filename.lower()

    if not filename.endswith((".pdf", ".docx")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported.",
        )

    if not include_quality and not (job_description or "").strip():
        raise HTTPException(
            status_code=400,
            detail="Select an analysis or provide a job description.",
        )

    try:
        file_bytes = await file.read(MAX_FILE_SIZE + 1)

        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File is too large. Maximum allowed size is 5 MB.",
            )

        try:
            resume_text = extract_resume_text(
                file.filename,
                file_bytes,
            )
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail=str(error),
            ) from error
        except Exception:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Unable to read the file. Please upload "
                    "a valid PDF or DOCX."
                ),
            ) from None

        try:
            validation = validate_resume_document(resume_text)
        except GeminiServiceError as error:
            raise gemini_error_response(error) from error
        except Exception:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Unable to verify this document right now. "
                    "Please try again."
                ),
            ) from None

        if not validation.is_resume:
            raise HTTPException(
                status_code=400,
                detail=(
                    "This file does not appear to be a resume or CV. "
                    + validation.reason
                ),
            )

        skills = extract_skills(resume_text)

        job_match = None
        quality_analysis = None

        if (job_description or "").strip():
            try:
                match_result = analyze_job_match(
                    resume_text,
                    skills,
                    job_description,
                )

                ai_analysis = match_result["ai_analysis"]

                if hasattr(ai_analysis, "model_dump"):
                    match_result["ai_analysis"] = ai_analysis.model_dump()

                job_match = JobMatchResult.model_validate(match_result)

            except ValueError as error:
                raise HTTPException(
                    status_code=400,
                    detail=str(error),
                ) from error
            except GeminiServiceError as error:
                raise gemini_error_response(error) from error
            except Exception:
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "Job matching failed. Please try again later."
                    ),
                ) from None

        if include_quality:
            try:
                quality_result = analyze_resume_quality(resume_text)

                quality_data = (
                    quality_result.model_dump()
                    if hasattr(quality_result, "model_dump")
                    else quality_result
                )

                quality_analysis = ResumeQualityResult.model_validate(
                    quality_data
                )

            except GeminiServiceError as error:
                raise gemini_error_response(error) from error
            except Exception:
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "Unable to analyze resume quality right now. "
                        "Please try again."
                    ),
                ) from None

        return AnalyzeResponse(
            filename=file.filename,
            skills=skills,
            job_match=job_match,
            quality_analysis=quality_analysis,
        )

    finally:
        await file.close()
