import uuid

from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel, field_validator

from services.resume_parser import extract_resume_text
from services.skill_analyzer import extract_skills
from services.analysis_service import analyze_job_match


app = FastAPI()


class JobDescription(BaseModel):
    analysis_id: str
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, value):
        if not value.strip():
            raise ValueError("Job description cannot be empty.")

        return value

class AIAnalysisResponse(BaseModel):
    overall_assessment: str
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]

class ResumeUploadResponse(BaseModel):
    analysis_id: str
    filename: str
    skills: list[str]

class JobMatchResponse(BaseModel):
    analysis_id: str
    required_skills: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    match_score: int
    ai_analysis: AIAnalysisResponse

analyses = {}


@app.get("/")
def home():
    return {
        "message": "AI Resume Analyzer Backend is running!"
    }


@app.post("/resume/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    file_bytes = await file.read()

    try:
        text = extract_resume_text(file.filename, file_bytes)
        skills = extract_skills(text)

        analysis_id = str(uuid.uuid4())

        analyses[analysis_id] = {
            "text": text,
            "skills": skills
        }

        return {
            "analysis_id": analysis_id,
            "filename": file.filename,
            "skills": skills
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

class AnalysisResponse(BaseModel):
    analysis_id: str
    skills: list[str]

@app.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(analysis_id: str):
    analysis = analyses.get(analysis_id)

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
def delete_analysis(analysis_id: str):
    if analysis_id not in analyses:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found."
        )

    del analyses[analysis_id]

    return {
        "message": "Analysis deleted successfully."
    }

@app.post("/job/match", response_model=JobMatchResponse)
async def match_job(job: JobDescription):
    analysis = analyses.get(job.analysis_id)

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

    return {
        "analysis_id": job.analysis_id,
        **result
    }