import uuid

from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel, field_validator

from services.resume_parser import extract_resume_text
from services.skill_analyzer import extract_skills
from services.job_matcher import calculate_match
from services.ai_analyzer import analyze_resume


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


@app.post("/job/match", response_model=JobMatchResponse)
async def match_job(job: JobDescription):
    analysis = analyses.get(job.analysis_id)

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="Invalid analysis ID. Please upload a resume first."
        )

    required_skills = extract_skills(job.text)

    result = calculate_match(
        analysis["skills"],
        required_skills
    )

    try:
        ai_analysis = analyze_resume(
            analysis["text"],
            job.text,
            result["matched_skills"],
            result["missing_skills"],
            result["match_score"]
        )

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="AI analysis failed. Please try again later."
        )

    return {
        "analysis_id": job.analysis_id,
        "required_skills": required_skills,
        **result,
        "ai_analysis": ai_analysis
    }