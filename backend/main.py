import uuid

from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel, field_validator
from fastapi.middleware.cors import CORSMiddleware
from typing import Literal

from services.resume_parser import extract_resume_text
from services.skill_analyzer import extract_skills
from services.analysis_service import analyze_job_match
from services.resume_validator import validate_resume_document
from services.resume_quality_analyzer import analyze_resume_quality
from database import (
    init_db,
    save_analysis,
    get_analysis,
    delete_analysis,
    save_match_result,
    get_match_result
)

app = FastAPI()
init_db()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobDescription(BaseModel):
    analysis_id: str
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, value):
        if not value.strip():
            raise ValueError("Job description cannot be empty.")

        return value

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

class ResumeUploadResponse(BaseModel):
    analysis_id: str
    filename: str
    skills: list[str]

class JobMatchResponse(BaseModel):
    analysis_id: str
    required_skills: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    match_score: int | None
    ai_analysis: AIAnalysisResponse
    
class ResumeQualityRequest(BaseModel):
    analysis_id: str


@app.get("/")
def home():
    return {
        "message": "AI Resume Analyzer Backend is running!"
    }


MAX_FILE_SIZE = 5 * 1024 * 1024


@app.post("/resume/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file was provided."
        )

    filename = file.filename.lower()

    if not filename.endswith((".pdf", ".docx")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported."
        )

    file_bytes = await file.read(MAX_FILE_SIZE + 1)

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File is too large. Maximum allowed size is 5 MB."
        )

    try:
        text = extract_resume_text(file.filename, file_bytes)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to read the file. Please upload a valid PDF or DOCX."
        )


    try:
        validation = validate_resume_document(text)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to verify this document right now. Please try again."
        )

    if not validation.is_resume:
        raise HTTPException(
            status_code=400,
            detail=(
                "This file does not appear to be a resume or CV. "
                + validation.reason
            )
        )

    skills = extract_skills(text)
    analysis_id = str(uuid.uuid4())

    save_analysis(analysis_id, text, skills)

    return {
        "analysis_id": analysis_id,
        "filename": file.filename,
        "skills": skills
    }

class AnalysisResponse(BaseModel):
    analysis_id: str
    skills: list[str]


@app.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
def get_analysis_endpoint(analysis_id: str):
    analysis = get_analysis(analysis_id)

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found."
        )

    return {
        "analysis_id": analysis_id,
        "skills": analysis["skills"]
    }


@app.delete("/analysis/{analysis_id}")
def delete_analysis_endpoint(analysis_id: str):
    deleted = delete_analysis(analysis_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found."
        )

    return {
        "message": "Analysis deleted successfully."
    }

@app.post("/job/match", response_model=JobMatchResponse)
async def match_job(job: JobDescription):
    analysis = get_analysis(job.analysis_id)

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="Invalid analysis ID. Please upload a resume first."
        )

    try:
        result = analyze_job_match(
            analysis["text"],
            analysis["skills"],
            job.text
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="AI analysis failed. Please try again later."
        )

    result["ai_analysis"] = result["ai_analysis"].model_dump()

    save_match_result(
        job.analysis_id,
        job.text,
        result
    )

    return {
        "analysis_id": job.analysis_id,
        **result
    }

class SavedMatchResponse(JobMatchResponse):
    job_description: str
    created_at: str

@app.get(
    "/analysis/{analysis_id}/match-result",
    response_model=SavedMatchResponse
)
def get_saved_match_result(analysis_id: str):
    analysis = get_analysis(analysis_id)

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found."
        )

    result = get_match_result(analysis_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="No saved job-match result found."
        )

    return result


@app.post("/resume/quality")
def resume_quality(request: ResumeQualityRequest):
    analysis = get_analysis(request.analysis_id)

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="Resume not found. Please upload your resume again.",
        )

    try:
        result = analyze_resume_quality(analysis["text"])
        return {
            "analysis_id": request.analysis_id,
            "quality_analysis": result.model_dump(),
        }
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to analyze resume quality right now. Please try again.",
        )