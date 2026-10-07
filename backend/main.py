from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel, field_validator

from services.resume_parser import extract_resume_text
from services.skill_analyzer import extract_skills
from services.job_matcher import calculate_match
from services.ai_analyzer import analyze_resume


app = FastAPI()

class JobDescription(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, value):
        if not value.strip():
            raise ValueError("Job description cannot be empty.")

        return value

resume_data = {
    "text": "",
    "skills": []
}

@app.get("/")
def home():
    return {"message": "AI Resume Analyzer Backend is running!"}


@app.post("/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    file_bytes = await file.read()

    try:
        text = extract_resume_text(file.filename, file_bytes)
        skills = extract_skills(text)

        resume_data["text"] = text
        resume_data["skills"] = skills

        return {
            "filename": file.filename,
            "text": text,
            "skills": skills
        }

    except ValueError as error:
        return {
            "error": str(error)
        }
@app.post("/job/match")
async def match_job(job: JobDescription):
    if not resume_data["text"]:
        return {
            "error": "Please upload a resume before matching a job."
        }

    required_skills = extract_skills(job.text)

    result = calculate_match(
        resume_data["skills"],
        required_skills
    )

    try:
        ai_analysis = analyze_resume(
            resume_data["text"],
            job.text,
            result["matched_skills"],
            result["missing_skills"],
            result["match_score"]
        )

    except Exception:
        return {
            "error": "AI analysis failed. Please try again later."
        }

    return {
        "required_skills": required_skills,
        **result,
        "ai_analysis": ai_analysis
    }
  